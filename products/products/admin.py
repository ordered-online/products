from django.contrib import admin
from .models import Category, Tag, Additive, Product


for model in [Category, Tag, Additive, Product]:
    admin.site.register(model)
