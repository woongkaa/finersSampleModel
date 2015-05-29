# coding: utf-8
from django.contrib import admin
from sample_shop.models import Product, ProductCategory, ProductSpecification, ProductKeyword, Keyword, FilterTag
from import_export.admin import ImportExportMixin
from .resources import ProductResource
# Register your models here.


class ProductAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'description']
    list_editable = ['category', 'description']
    ordering = ['name']
    resource_class = ProductResource


class KeywordAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'type', 'get_filter_tags']
    list_editable = ['name']
    ordering = ['id']


class FilterTagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'type']
    list_editable = ['name', 'type']
    ordering = ['id']

admin.site.register(ProductCategory)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductKeyword)
admin.site.register(ProductSpecification)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(FilterTag, FilterTagAdmin)

