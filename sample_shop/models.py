# coding=utf-8
import uuid
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import safe
from orderable.models import Orderable
from shop.models import Product as ShopProduct
from shop.models_bases import BaseProduct
#from site_extras.libraries.utils import FilenameChanger


class Profile(models.Model):
    GENDER_CHOICES = [
        (True, '남'),
        (False, '여'),
    ]
    user = models.OneToOneField(User, related_name="profile")
    gender = models.BooleanField(choices=GENDER_CHOICES, default=True, verbose_name=u"성별")
    contact = models.CharField(u"연락처", max_length=100, blank=True)
    birthday = models.DateField(verbose_name=u"생년월일")
    favorite_products = models.ManyToManyField("Product", blank=True, verbose_name=u"관심제품들")

    class Meta:
        verbose_name = u"프로필"
        verbose_name_plural = u"프로필"

    def __unicode__(self):
        return u"%s의 프로필" % self.user.username

    def get_budget_status(self, date):
        result = {
            'minimum_amount': 0,
            'maximum_amount': 0,
        }
        return result

    def reports(self):
        dates = self.user.recommendations.distinct('date').values_list('date', flat=True)
        return self.user.recommendations.filter(date__in=dates).order_by('category')


class UserProductUsage(models.Model):
    user = models.ForeignKey(User, related_name="usages", verbose_name=u"사용자")
    category = models.ForeignKey("ProductCategory", verbose_name=u"제품카테고리")
    daily_amount_used = models.PositiveIntegerField(u"하루 권장 사용량")
    unit = models.CharField(u"단위", max_length=20, blank=True)

    class Meta:
        verbose_name = u"사용량 정보"
        verbose_name_plural = u"사용량 정보"
        unique_together = ['user', 'category']

    def __unicode__(self):
        return u"%s님의 %s 하루 사용량: %d %s" % (self.user.username, self.category.name, self.daily_amount_used, self.unit)


class Survey(Orderable):
    name = models.CharField(max_length=100, verbose_name=u"설문조사명")

    class Meta:
        verbose_name = u"설문지"
        verbose_name_plural = u"설문지"

    def __unicode__(self):
        return self.name


class SurveyQuestion(Orderable):
    TYPE_CHOICES = [
        (1, u"단일문항"),
        (2, u"다중문항"),
        (3, u"주관식"),
    ]
    survey = models.ForeignKey(Survey, blank=True, null=True, related_name="questions")
    content = models.TextField(verbose_name=u"내용")
    type = models.IntegerField(choices=TYPE_CHOICES, verbose_name=u"문항타입")
    # image = models.ImageField(upload_to=FilenameChanger("main/survey"), blank=True, verbose_name=u"이미지")

    class Meta:
        verbose_name = u"설문지 질문"
        verbose_name_plural = u"설문지 질문"
        ordering = ['sort_order']

    def __unicode__(self):
        return u"%d. %s" % (self.sort_order, self.content)


class SurveyQuestionItem(Orderable):
    question = models.ForeignKey(SurveyQuestion, related_name="items")
    content = models.TextField(verbose_name=u"내용")
    filter_tags = models.ManyToManyField("FilterTag", related_name="survey_question_items", verbose_name=u"필터태그들")

    class Meta:
        verbose_name = u"문항"
        verbose_name_plural = u"문항"

    def __unicode__(self):
        return u"%s" % self.content

    def clean(self):
        if self.question.type is 3:
            raise ValidationError(u"주관식 문제는 문항을 가질 수 없습니다.")


class SurveyResult(models.Model):
    user = models.ForeignKey(User, related_name="results")
    question = models.ForeignKey(SurveyQuestion, verbose_name=u"답변한 문제")
    chosen_answer = models.ForeignKey(SurveyQuestionItem, blank=True, verbose_name=u"객관식답안")
    writen_answer = models.TextField(blank=True, verbose_name=u"주관식답안")

    class Meta:
        verbose_name = u"설문 답안"
        verbose_name_plural = u"설문 답안"

    def clean(self):
        if self.chosen_answer not in self.question.items.all():
            raise ValidationError(u"선택한 답안이 선택지에 없습니다.")


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name=u"카테고리명")

    class Meta:
        verbose_name = u"제품 카테고리"
        verbose_name_plural = u"제품 카테고리"

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains",)

    def __unicode__(self):
        return u"%s" % self.name


class Product(ShopProduct):
    category = models.ForeignKey("ProductCategory", related_name="products", verbose_name=u"카테고리")
    description = models.TextField(u"제품설명", blank=True)
    # image = models.ImageField(u"메인 이미지", upload_to=FilenameChanger("main/product"), blank=True)
    capacity = models.PositiveIntegerField(u"용량", blank=True, null=True)
    capacity_unit = models.CharField(u"용량단위", default='ml', max_length=20, blank=True)
    days_to_consume = models.PositiveIntegerField(u"기본사용일", blank=True, null=True)
    review_counts = models.PositiveIntegerField(u"리뷰수", default=0)
    keywords = models.ManyToManyField("Keyword", through="ProductKeyword", related_name="products", verbose_name=u"키워드들")
    brand = models.ForeignKey("FilterTag", limit_choices_to={"type": u"브랜드"}, blank=True, null=True, verbose_name=u"브랜드")
    is_sold_out = models.BooleanField(u"품절", default=False)

    class Meta:
        verbose_name = u"제품"
        verbose_name_plural = u"제품"
        ordering = ['pk']

    def __unicode__(self):
        return u"%s: %s" % (self.category, self.name)

    def save(self, *args, **kwargs):
        self.slug = uuid.uuid4()
        super(Product, self).save(*args, **kwargs)

    def get_capacity_display(self):
        return u"%d %s" % (self.capacity, self.capacity_unit)

    def get_price_per_unit(self):
        return u"%d 원/%s" % (self.unit_price/self.capacity, self.capacity_unit)

    def is_reviewed(self):
        # TODO 리뷰여부
        return True


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product)
    name = models.CharField(max_length=100, verbose_name=u"이름")
    description = models.TextField(verbose_name=u"내용")
    sort_order = models.PositiveIntegerField(default=0, verbose_name=u"정렬순서")

    class Meta:
        verbose_name = u"제품사양"
        verbose_name_plural = u"제품사양"
        ordering = ["sort_order"]

    def __unicode__(self):
        return u"%s: %s" % (self.product.name, self.name)


class FilterTag(models.Model):
    TYPE_CHOICES = [
        (u"피부타입", u"피부타입"),
        (u"피부고민", u"피부고민"),
        (u"취향", u"취향"),
        (u"기능성", u"기능성"),
        (u"브랜드", u"브랜드"),
    ]
    name = models.CharField(max_length=200, unique=True, verbose_name=u"이름")
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, verbose_name=u"종류")

    class Meta:
        verbose_name = u"필터태그"
        verbose_name_plural = u"필터태그"

    def __unicode__(self):
        return u"%s: %s" % (self.type, self.name)


class Keyword(models.Model):
    TYPE_CHOICES = (
        (u"느낌", "느낌"),
        (u"특징", "특징"),
        (u"효과", "효과"),
        (u"피부타입", "피부타입")
    )

    name = models.CharField(max_length=100, unique=True, verbose_name=u"키워드명")
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, verbose_name=u"키워드 타입")
    filter_tags = models.ManyToManyField(FilterTag, related_name="keywords", blank=True, verbose_name=u"필터태그들")

    class Meta:
        verbose_name = u"키워드"
        verbose_name_plural = u"키워드"

    def __unicode__(self):
        return u"%s: %s" % (self.type, self.name)

    def get_filter_tags(self):
        # 웅 : 필터태그는 ManyToMany field 이므로 다른 모델의 admin에서 출력을 위해 합쳐진 문장으로 전달해야 list_display가 가능하다.
        return "\n".join(["#"+f.name for f in self.filter_tags.all()])


class ProductKeyword(models.Model):
    product = models.ForeignKey(Product, verbose_name=u"제품")
    keyword = models.ForeignKey(Keyword, verbose_name=u"키워드")
    count = models.IntegerField(default=0, verbose_name=u"키워드 수")

    class Meta:
        verbose_name = u"제품 키워드"
        verbose_name_plural = u"제품 키워드"
        unique_together = ['product', 'keyword']


class Recommendation(models.Model):
    user = models.ForeignKey(User, related_name="recommendations", verbose_name=u"사용자")
    category = models.ForeignKey(ProductCategory, default=1, verbose_name=u"제품카테고리")
    date = models.DateField(blank=True, null=True, verbose_name=u"추천일자")
    comment = models.TextField(u"추천내용", blank=True)
    products = models.ManyToManyField(Product, blank=True, verbose_name=u"추천제품")
    is_alerted = models.BooleanField(default=False, verbose_name=u"알림여부")
    is_recommended = models.BooleanField(default=False, verbose_name=u"추천여부")

    class Meta:
        verbose_name = u"추천"
        verbose_name_plural = u"추천"
        unique_together = ['user', 'date']

    def __unicode__(self):
        return u"%s %s 추천 %s" % (self.user, self.category.name, u"(추천완료 "+str(self.date)+")" if self.date else u"(추천대기)")

    def get_products_display(self):
        result = u""
        for product in self.products.all():
            result += u"%s <br>" % product.name

        return safe(result)

    def get_alert_date_display(self):
        return u"-"

    def get_remaining_days_display(self):
        return u"-"

    def get_purchase_date(self):
        return u"-"

    def get_days_to_use(self):
        return 0

    def get_days_remaining(self):
        return 0

    def get_date_to_alert(self):
        return 0

    def get_remaining_days_to_alert(self):
        return 0
