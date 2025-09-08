from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from . import models


@admin.register(models.Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)
    list_filter = ("created_at",)


@admin.register(models.Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "factory", "employee_count", "master", "approve_employee_works")
    search_fields = ("name", "factory__name")
    list_filter = ("factory", "approve_employee_works")
    autocomplete_fields = ("factory", "master")


@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "factory",
        "department",
        "position",
        "birth_date",
        "phone",
        "fired",
        "black_listed",
    )
    list_filter = (
        "factory",
        "department",
        "position",
        "fired",
        "black_listed",
        "gender",
    )
    search_fields = ("full_name", "report_card", "pinfl", "passport_id", "badge")
    ordering = ("-created_at",)

    # удобные автополя для ForeignKey
    autocomplete_fields = (
        "factory",
        "position",
        "department",
        "photo",
        "user",
        "sewing_line",
        "process",
    )

    # для M2M полей лучше filter_horizontal, чтобы не занимало кучу места
    filter_horizontal = (
        "additional_factories",
        "access_control_factories",
        "process_roles",
    )

    fieldsets = (
        (_("Основные данные"), {
            "fields": ("full_name", "factory", "department", "position", "position_last_updated"),
        }),
        (_("Контакты"), {
            "fields": ("phone", "phone_number", "email", "address"),
        }),
        (_("Документы"), {
            "fields": ("passport_id", "issued_by", "issued_date", "pinfl"),
        }),
        (_("Работа"), {
            "fields": (
            "report_card", "employment_date", "dismissal_date", "fired", "black_listed", "black_listed_reason"),
        }),
        (_("Технические"), {
            "fields": (
                "badge", "telegram_id", "ptr",
                "user", "photo", "sewing_line", "process",
                "additional_factories", "access_control_factories", "process_roles",
            ),
        }),
        (_("Служебные отметки"), {
            "fields": ("created_at", "updated_at"),
        }),
    )

    readonly_fields = ("created_at", "updated_at")
