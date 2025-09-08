# sewing/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from . import models


# ---------- Простые справочники ----------

@admin.register(models.SewingFabricType)
class SewingFabricTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(models.SewingFabric)
class SewingFabricAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "fabric_type")
    list_filter = ("fabric_type",)
    search_fields = ("name", "fabric_type__name")
    ordering = ("fabric_type__name", "name")
    autocomplete_fields = ("fabric_type",)


@admin.register(models.TransferPrintPrice)
class TransferPrintPriceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(models.SewingPackingPrice)
class SewingPackingPriceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(models.SewingPart)
class SewingPartAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(models.CategoryModel)
class CategoryModelAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "price")
    search_fields = ("code", "name")
    ordering = ("code",)


# ---------- Линии ----------

@admin.register(models.SewingLine)
class SewingLineAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "factory", "department", "master", "worker_count", "status")
    list_filter = ("factory", "department", "status")
    search_fields = ("name", "factory__name", "department__name", "master__full_name")
    ordering = ("factory__name", "name")
    autocomplete_fields = ("factory", "department", "master")
    list_select_related = ("factory", "department", "master")

    readonly_fields = ()
    fieldsets = (
        (_("Основное"), {
            "fields": ("name", "factory", "department", "master", "status")
        }),
        (_("Параметры"), {
            "fields": ("worker_count", "ordering"),
        }),
    )


# ---------- Инлайны для Модели/Варианта ----------

class VariantSizeInline(admin.TabularInline):
    model = models.VariantSize
    extra = 0
    autocomplete_fields = ("size",)


class VariantOperationInline(admin.TabularInline):
    model = models.VariantOperation
    extra = 0
    autocomplete_fields = ("operation",)


class VariantMaterialInline(admin.TabularInline):
    model = models.VariantMaterial
    extra = 0
    autocomplete_fields = ("material", "color")
    fields = (
        # В инлайнах поле внешнего ключа (variant) обычно не показываем — админ сам его проставляет
        "material", "count", "color", "packing_type",
        "width", "height", "density", "loss", "price", "main", "notes", "used_parts",
    )
    filter_horizontal = ("used_parts",)
    verbose_name_plural = _("Материалы варианта")


class VariantAccessoryInline(admin.TabularInline):
    model = models.VariantAccessory
    extra = 0
    autocomplete_fields = ("accessory",)
    fields = ("accessory", "count", "price", "local_produce", "notes")
    verbose_name_plural = _("Аксессуары варианта")


# ---------- Модель одежды ----------

@admin.register(models.SewingProductModel)
class SewingProductModelAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor_code", "name", "category", "weight_display", "discount_display")
    # ВАЖНО: кортеж из одного элемента пишем с запятой
    list_filter = ("category",)
    search_fields = ("vendor_code", "name",)
    ordering = ("-created_at",)

    # В autocomplete только FK/M2M
    autocomplete_fields = ("category",)

    readonly_fields = ("created_at", "updated_at",)
    fieldsets = (
        (_("Основное"), {
            "fields": ("vendor_code", "name", "season", "image", "category",)
        }),
        (_("Технико-экономика"), {
            "fields": (
                "weight", "discount",
                "cutting_price", "transfer_price", "print_price", "embroidery_price",
                "sewing_loss_percent", "other_expenses_percent", "profitability", "commission",
            )
        }),
        (_("Служебные отметки"), {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # безопасный вывод, даже если этих полей нет в модели
    @admin.display(description=_("Вес"))
    def weight_display(self, obj):
        return getattr(obj, "weight", "—")

    @admin.display(description=_("Скидка"))
    def discount_display(self, obj):
        return getattr(obj, "discount", "—")


# ---------- Варианты модели ----------

@admin.register(models.ModelVariant)
class ModelVariantAdmin(admin.ModelAdmin):
    list_display = (
        "id", "product_model", "name", "description", "work_type", "cloned",
    )
    list_filter = ("work_type", "cloned")
    search_fields = (
        "name", "description",
        "product_model__name", "product_model__vendor_code",
    )
    ordering = ("-created_at",)
    list_select_related = ("product_model", "work_type")

    # Убираем несуществующие/неподходящие для автокомплита поля
    autocomplete_fields = ("product_model", "work_type")

    inlines = (VariantMaterialInline, VariantAccessoryInline, VariantSizeInline, VariantOperationInline)

    readonly_fields = ("created_at", "updated_at")

    # Поля для "Основное" есть почти всегда
    base_fieldsets = (
        (_("Основное"), {
            "fields": ("product_model", "kind", "name", "description",)
        }),
        (_("Производство"), {
            "fields": ("work_type", "loss", "design_code", "cloned")
        }),
        (_("Служебные отметки"), {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """
        Добавляем секцию 'Цены по умолчанию' только если эти поля существуют в модели.
        Это защищает от ошибок admin.E0xx при несовпадении схемы.
        """
        fieldsets = list(self.base_fieldsets)
        model = self.model
        has_transfer = hasattr(model, "_meta") and any(
            f.name == "transfer_price" for f in model._meta.get_fields()
        )
        has_packing = hasattr(model, "_meta") and any(
            f.name == "packing_price" for f in model._meta.get_fields()
        )
        if has_transfer or has_packing:
            price_fields = tuple(
                name for name, present in (
                    ("transfer_price", has_transfer),
                    ("packing_price", has_packing),
                ) if present
            )
            if price_fields:
                fieldsets.insert(2, (_("Цены по умолчанию"), {"fields": price_fields}))
        return fieldsets


# ---------- Отдельные регистраторы (если нужно работать поодиночке) ----------

@admin.register(models.VariantMaterial)
class VariantMaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "variant", "material", "count", "color", "main", "price")
    list_filter = ("main", "packing_type", "color")
    search_fields = (
        "variant__name",
        "variant__product_model__vendor_code",
        "material__title", "material__code",
    )
    autocomplete_fields = ("variant", "material", "color", "used_parts")
    filter_horizontal = ("used_parts",)
    ordering = ("-id",)
    list_select_related = ("variant",)


@admin.register(models.VariantAccessory)
class VariantAccessoryAdmin(admin.ModelAdmin):
    list_display = ("id", "variant", "accessory", "count", "price", "local_produce")
    list_filter = ("local_produce",)
    search_fields = (
        "variant__name",
        "variant__product_model__vendor_code",
        "accessory__title", "accessory__code",
    )
    autocomplete_fields = ("variant", "accessory")
    ordering = ("-id",)
    list_select_related = ("variant",)


@admin.register(models.VariantSize)
class VariantSizesAdmin(admin.ModelAdmin):
    list_display = ("variant", "size", "notes",)
    search_fields = (
        "variant__name",
        "variant__product_model__vendor_code",
    )
    list_editable = ["size", ]


@admin.register(models.VariantOperation)
class VariantOperationAdmin(admin.ModelAdmin):
    list_display = ("variant", "operation", "seconds", 'price')
    search_fields = (
        "variant__name",
        "variant__product_model__vendor_code",
    )
    list_editable = ["operation", ]
