# core/widgets.py
from django_select2.forms import ModelSelect2Widget

from info.models import Material, Operation, Size, MaterialGroup, Color
from sewing.models import ModelVariant


class BaseAjaxSelect2(ModelSelect2Widget):
    search_fields = ()
    attrs = {
        "data-minimum-input-length": 1,
        "data-placeholder": "Начните вводить...",
        "style": "width: 100%;",

    }
    page_size = 20


class MaterialSelect2(BaseAjaxSelect2):
    model = Material
    search_fields = ("title__icontains", "code__icontains")

    def __init__(self, *args, group_name=None, **kwargs):
        self.group_name = group_name
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = Material.objects.select_related("group").all()
        if self.group_name:
            qs = qs.filter(group__name__iexact=self.group_name)
        return qs


class OperationSelect2(BaseAjaxSelect2):
    model = Operation
    search_fields = ("name__icontains",)

    def get_queryset(self):
        return Size.objects.filter(is_active=True)


class SizeSelect2(BaseAjaxSelect2):
    model = Size
    search_fields = ("name__icontains",)

    def get_queryset(self):
        return Size.objects.all()


class MaterialGroupSelect2(BaseAjaxSelect2):
    search_fields = ("name__icontains", "code__icontains")

    def get_queryset(self):
        return MaterialGroup.objects.all()


class ColorSelect2(BaseAjaxSelect2):
    model = Color
    search_fields = ("name__icontains", "code__icontains")


class VariantSelect2(ModelSelect2Widget):
    model = ModelVariant
    search_fields = (
        "name__icontains",
        "description__icontains",
        "product_model__vendor_code__icontains",
        "product_model__name__icontains",
    )

    def get_queryset(self):
        return ModelVariant.objects.select_related("product_model")
