import json
from json import JSONDecodeError

import requests
from django.db import IntegrityError
from django.http import JsonResponse

from . import settings
from .models import Product, Category, Tag, Additive


class SuccessResponse(JsonResponse):
    def __init__(self, response=None, *args, **kwargs):
        if response is None:
            super().__init__({
                "success": True,
            }, *args, **kwargs)
        else:
            super().__init__({
                "success": True,
                "response": response
            }, *args, **kwargs)


class AbstractFailureResponse(JsonResponse):
    reason = None

    def __init__(self, *args, **kwargs):
        super().__init__({
            "success": False,
            "reason": self.reason
        }, *args, **kwargs)


class IncorrectAccessMethod(AbstractFailureResponse):
    reason = "incorrect_access_method"


class ProductNotFound(AbstractFailureResponse):
    reason = "product_not_found"


class DuplicateProduct(AbstractFailureResponse):
    reason = "duplicate_product"


class MalformedJson(AbstractFailureResponse):
    reason = "malformed_json"


class IncorrectCredentials(AbstractFailureResponse):
    reason = "incorrect_credentials"


class VerificationServiceUnavailable(AbstractFailureResponse):
    reason = "verification_service_unavailable"


class LocationsServiceUnavailable(AbstractFailureResponse):
    reason = "locations_service_unavailable"


def find_products(request) -> JsonResponse:
    """Find products via GET."""

    if request.method != "GET":
        return IncorrectAccessMethod()

    products = Product.objects.all()

    location_id = request.GET.get("location_id")
    if location_id:
        products = products.filter(location_id__exact=location_id)

    name = request.GET.get("name")
    if name:
        products = products.filter(name__icontains=name)

    category = request.GET.get("category")
    if category:
        try:
            category = Category.objects.get(name__iexact=category)
        except Category.DoesNotExist:
            pass
        else:
            products = products.intersection(category.product_set.all())

    tag = request.GET.get("tag")
    if tag:
        try:
            tag = Tag.objects.get(name__iexact=tag)
        except Tag.DoesNotExist:
            pass
        else:
            products = products.intersection(tag.product_set.all())

    additive = request.GET.get("additive")
    if additive:
        try:
            additive = Additive.objects.get(name__iexact=additive)
        except Additive.DoesNotExist:
            pass
        else:
            products = products.intersection(additive.product_set.all())

    products = products[:settings.MAX_RESULTS]

    return SuccessResponse(
        [
            {
                "product": product.dict_representation
            }
            for product in products
        ],
        safe=False
    )


def get_product(request, product_id) -> JsonResponse:
    """Get a product by its id via GET."""

    if request.method != "GET":
        return IncorrectAccessMethod()

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return ProductNotFound()

    return SuccessResponse(product.dict_representation)


def verify_user(data: dict) -> tuple:
    """Verify the user with the verification service."""
    session_key = data.get("session_key")
    if not session_key:
        raise ValueError()
    user_id = data.get("user_id")
    if not user_id:
        raise ValueError()

    # send a post request to the verification service endpoint
    response = requests.post(
        "{}/verification/verify/".format(settings.VERIFICATION_SERVICE_URL),
        data=json.dumps({"session_key": session_key, "user_id": user_id})
    )
    verification_data = response.json()
    if verification_data.get("success") is not True:
        raise ValueError()

    return user_id, session_key


def verify_location_owner(user_id, location_id):
    """Verify, that the user is the location owner."""

    # send a post request to the locations service endpoint
    response = requests.get("{}/locations/get/{}/".format(
        settings.LOCATIONS_SERVICE_URL, location_id
    ))
    location_data = response.json()
    if location_data.get("success") is not True:
        raise ValueError()

    # unwrap the user_id from the location data
    location_object = location_data.get("response")
    if not location_object:
        raise ValueError()
    location_user_id = location_object.get("user_id")
    if not location_user_id:
        raise ValueError()

    if user_id != location_user_id:
        raise ValueError()


def make_product(product_data: dict) -> JsonResponse:
    """Translate the given product data to a product model."""

    # infer all kwargs from the passed product data,
    # but exclude the many to many fields,
    # since they must be handled separately
    product = Product(**{
        x: product_data[x] for x in product_data
        if x not in ["tags", "categories", "additives"]
    })
    try:
        # do not use objects.create to allow id based product editing
        product.save()
    except IntegrityError:
        # if the passed product data violates any
        # uniqueness constraints, this fallback is called
        return DuplicateProduct()

    tags = product_data.get("tags")
    if tags:
        # infer all kwargs from the passed product data
        product.tags.set(Tag.objects.get_or_create(**t)[0] for t in tags)

    categories = product_data.get("categories")
    if categories:
        # infer all kwargs from the passed product data
        product.categories.set(Category.objects.get_or_create(**c)[0] for c in categories)

    additives = product_data.get("additives")
    if additives:
        # infer all kwargs from the passed product data
        product.additives.set(Additive.objects.get_or_create(**a)[0] for a in additives)

    return SuccessResponse()


def create_product(request) -> JsonResponse:
    """Create a product via POST."""
    if request.method != "POST":
        return IncorrectAccessMethod()

    try:
        data = json.loads(request.body)
    except JSONDecodeError:
        return MalformedJson()

    try:
        user_id, _ = verify_user(data)
    except ValueError:
        return IncorrectCredentials()
    except requests.ConnectionError:
        return VerificationServiceUnavailable()

    product_data = data.get("product")
    if not product_data:
        return MalformedJson()

    # this is necessary, because the user
    # should not create products for a
    # location which he doesn't have access to
    location_id = product_data.get("location_id")
    if not location_id:
        return MalformedJson()
    try:
        verify_location_owner(user_id, location_id)
    except ValueError:
        return IncorrectCredentials()
    except requests.ConnectionError:
        return LocationsServiceUnavailable()

    # the key "id" is disallowed, because django
    # would interpret the id key as the primary key
    # of the product object and therefore change
    # the properties of a potentially existing product
    if "id" in product_data:
        return MalformedJson()

    return make_product(product_data)


def edit_product(request, product_id) -> JsonResponse:
    """Edit the given product via POST."""

    if request.method != "POST":
        return IncorrectAccessMethod()

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return ProductNotFound()

    try:
        data = json.loads(request.body)
    except JSONDecodeError:
        return MalformedJson()

    try:
        user_id, session_key = verify_user(data)
    except ValueError:
        return IncorrectCredentials()
    except requests.ConnectionError:
        return VerificationServiceUnavailable()

    try:
        verify_location_owner(user_id, product.location_id)
    except ValueError:
        return IncorrectCredentials()
    except requests.ConnectionError:
        return LocationsServiceUnavailable()

    product_data = data.get("product")
    if not product_data:
        return MalformedJson()

    # disallow the key "id" to avoid overriding of
    # the wrong product, because the id of the product is
    # already inferred by the url
    if "id" in product_data:
        return MalformedJson()

    # if the products location id has changed, then the user
    # has to have access to the new location as well
    data_location_id = product_data.get("location_id")
    if data_location_id != product.location_id:
        try:
            verify_location_owner(user_id, data_location_id)
        except ValueError:
            return MalformedJson()
        except requests.ConnectionError:
            return LocationServiceUnavailable()

    # set the id attribute as inferred by the url
    # to make it possible for django to edit
    # the correct object
    product_data["id"] = product.id

    return make_product(product_data)
