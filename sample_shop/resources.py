# coding: utf-8
__author__ = 'woongkaa'

from import_export import resources
from models import Product


class ProductResource(resources.ModelResource):

    class Meta:
        model = Product
        # 아래처럼 관계형 필드로부터 __name으로 호출하지 않으면, id로 불러오기 때문에 export시 category id가 출력된다.
        fields = ('category__name', 'name',)
        # exclude = ('field name',)

