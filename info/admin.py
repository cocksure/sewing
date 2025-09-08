from django.contrib import admin

from . import models


@admin.register(models.UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'created_at', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    search_fields = ("id",)


@admin.register(models.UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'file', 'created_at', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_master']
    list_filter = ['is_master']
    search_fields = ['name']


@admin.register(models.ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ("id", "name")


@admin.register(models.Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'name', 'type', 'status', 'created_at', 'created_by']
    search_fields = ['name', 'code']
    list_filter = ['type', 'status']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(models.ProcessRole)
class ProcessRoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'process', 'role', 'individual', 'salary_percent']
    list_filter = ['individual', 'work_in_machine']
    search_fields = ['process__name', 'role__name']


@admin.register(models.Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'year', 'name', 'firm', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(models.Factory)
class FactoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'official_name', 'company']
    list_filter = ['company']
    search_fields = ['name']


@admin.register(models.Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'order', 'is_parallel', 'barcode', 'created_at']
    search_fields = ['name', 'barcode']
    list_filter = ['is_parallel', 'is_record_keeped']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(models.WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'product_type']
    filter_horizontal = ['processes']
    search_fields = ['name']


@admin.register(models.MaterialGroup)
class MaterialGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'name']
    search_fields = ['name', 'code']


@admin.register(models.MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(models.PriceCategory)
class PriceCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'm_unit']
    list_filter = ['m_unit']


@admin.register(models.MaterialGroupCategory)
class MaterialGroupCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'material_group', 'category']


@admin.register(models.MaterialSpecialGroup)
class MaterialSpecialGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(models.ColorGroup)
class ColorGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'last_color_code']


@admin.register(models.RecipeType)
class RecipeTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code']


@admin.register(models.RecipeGroup)
class RecipeGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(models.TypeOrderColor)
class TypeOrderColorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code']


@admin.register(models.ColorGraphic)
class ColorGraphicAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'name']


@admin.register(models.Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'title', 'group', 'm_unit', 'planned_cost', 'created_at', 'created_by']
    list_filter = ['type', 'group', 'special_group']
    search_fields = ['code', 'title']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_editable = ['group', ]


@admin.register(models.SubMaterial)
class SubMaterialAdmin(admin.ModelAdmin):
    list_display = ['id', 'material', 'sub_material', 'percent']


@admin.register(models.Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'name', 'group', 'firm', 'color_tone', 'created_at']
    list_filter = ['group', 'firm', 'color_tone']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(models.RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'product_type']
    search_fields = ['name']


@admin.register(models.SewingMachineType)
class SewingMachineTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(models.Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ("machine_type","name",  "default_price", "default_duration", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active", "machine_type")
    autocomplete_fields = ("machine_type",)
    list_editable = ["name", ]


@admin.register(models.Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', "name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
    list_editable = ["name"]
