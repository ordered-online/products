
from django.db import models
from django.forms import model_to_dict


class Category(models.Model):
    name = models.TextField(max_length=100, primary_key=True)


class Tag(models.Model):
    name = models.TextField(max_length=100, primary_key=True)


class Additive(models.Model):
    name = models.TextField(max_length=100, primary_key=True)


class Product(models.Model):
    # mandatory fields
    location_id = models.IntegerField()
    name = models.TextField()
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # many to many fields
    tags = models.ManyToManyField(Tag)
    categories = models.ManyToManyField(Category)
    additives = models.ManyToManyField(Additive)

    class Meta:
        unique_together = ["location_id", "name"]
        indexes = [
            models.Index(fields=["location_id"]),
        ]

    @property
    def dict_representation(self):
        product_dict = model_to_dict(self)

        # Serialize many to many fields manually
        for field in ["categories", "tags", "additives"]:
            field_values = product_dict.get(field)
            if field_values:
                product_dict[field] = [model_to_dict(f) for f in field_values]

        return product_dict
