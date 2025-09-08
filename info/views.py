# materials/views.py

import django_filters as df

from core.views import BaseListCreateView, BaseModelListView
from info import forms
from info import models
from info.models import Material


class ColorListCreateView(BaseListCreateView):
    model = models.Color
    template_name = "common/base_list_create.html"
    paginate_by = 12

    list_fields = ("code", "name", "group", "color_tone",)
    search_fields = ("code", "name",)
    fk_filters = ("group", "color_tone",)
    order_by = ("-id",)

    create_fields = ("code", "name", "group", "color_tone",)

    def get_queryset(self):
        return super().get_queryset()


class OperationListCreateView(BaseListCreateView):
    model = models.Operation
    template_name = "common/base_list_create.html"
    paginate_by = 12

    list_fields = ("name", "default_price", "default_duration", "is_active",)
    search_fields = ("name",)
    fk_filters = ("is_active", )
    order_by = ("-id",)

    create_fields = ("name", "default_price", "default_duration", "is_active", "notes")

    def get_queryset(self):
        return super().get_queryset()


class SizeListCreateView(BaseListCreateView):
    model = models.Size
    template_name = "common/base_list_create.html"
    paginate_by = 12

    list_fields = ("name", "is_active", "notes", )
    search_fields = ("name",)
    fk_filters = ( "is_active",)
    order_by = ("-id",)

    create_fields = ("name", "is_active", "notes", )

    def get_queryset(self):
        return super().get_queryset()


class MaterialListView(BaseModelListView):
    model = models.Material
    template_name = "common/base_list.html"
    paginate_by = 12

    list_fields = ("code", "title", "group", "special_group", "m_unit", "color",)
    search_fields = ("code", "title", "barcode", "accounting_code")
    fk_filters = ("group", "special_group")
    order_by = ("-id",)
    order_by_map = {"group": ("group__name",), "m_unit": ("m_unit__name",)}

    create_url_name = "info:material-create"

    def get_queryset(self):
        return (super().get_queryset()
                .select_related("group", "m_unit", "special_group"))


class MaterialGroupListCreateView(BaseListCreateView):
    model = models.MaterialGroup
    template_name = "common/base_list_create.html"
    paginate_by = 12

    list_fields = ("id", "name", "code", "created_at")
    search_fields = ("name", "code")
    fk_filters = ()
    order_by = ("-id",)

    create_fields = ("name", "code")

    def get_queryset(self):
        return super().get_queryset()


class SpecificationListCreateView(BaseListCreateView):
    model = models.Specification
    template_name = "common/base_list_create.html"
    paginate_by = 12

    list_fields = ("id", "year", "name", "firm", "created_at")
    search_fields = ("year", "name")
    fk_filters = ("firm",)
    order_by = ("-id",)
    order_by_map = {"firm": ("firm__name",)}

    create_fields = ("year", "name", "firm")

    def get_queryset(self):
        return super().get_queryset().select_related("firm")


class ProcessesListCreateView(BaseListCreateView):
    model = models.Process
    template_name = "common/base_list_create.html"
    paginate_by = 12

    list_fields = ("name", "order", "product_type", "required_process",)
    search_fields = ("name",)
    fk_filters = ("product_type",)
    order_by = ("-id",)
    order_by_map = {}

    create_fields = (
        "name", "order", "is_parallel", "product_type", "is_record_keeped", "replaceable_processes", "required_process")

    def get_queryset(self):
        return super().get_queryset().select_related("product_type")


class WorkTypeListCreateView(BaseListCreateView):
    model = models.WorkType
    template_name = "common/base_list_create.html"
    paginate_by = 12

    list_fields = ("name", "product_type",)
    search_fields = ("name",)
    fk_filters = ("product_type",)
    order_by = ("-id",)
    order_by_map = {}

    create_fields = ("name", "processes", "product_type")

    def get_queryset(self):
        return (super()
                .get_queryset()
                .select_related("product_type")
                .prefetch_related("processes"))


class FirmListCreateView(BaseListCreateView):
    model = models.Firm
    template_name = "common/base_list_create.html"
    paginate_by = 12

    list_fields = ("id", "code", "name", "type", "status", "phone", "email", "created_at")
    search_fields = ("code", "name", "phone", "email")
    fk_filters = ()
    order_by = ("-id",)
    verbose_map = {
        "code": "Код",
        "name": "Наименование",
        "type": "Тип",
        "status": "Статус",
        "phone": "Телефон",
        "email": "Email",
        "created_at": "Создан",
    }

    create_fields = ("code", "name", "type", "legal_address", "phone", "email",)

    # 👇 так добавляем фильтр по type
    extra_filters = {
        "type": df.ChoiceFilter(
            field_name="type",
            label="Тип",
            choices=models.Firm.TYPE_CHOICES,
        ),
    }

    def get_queryset(self):
        return super().get_queryset().select_related("logo")


class MaterialListCreateView(BaseListCreateView):
    model = Material
    form_class = forms.MaterialForm
    template_name = "info/material_list_create.html"

    paginate_by = 12
    search_fields = ("title", "code", "type", "accounting_code", "barcode")
    ordering_fields = ("id", "created_at", "updated_at", "title", "code", "planned_cost")
    default_ordering = ("-created_at",)

    def get_base_queryset(self):
        return (self.model.objects
                .select_related("group", "m_unit", "color")
                .all())
