# core/templatetags/form_extras.py
from django import template

register = template.Library()


@register.filter
def choice_label(bf, raw_value):
    """Возвращает красивый label для Choice/ModelChoice по value."""
    if not bf:
        return raw_value
    value = "" if raw_value is None else str(raw_value)
    # ModelChoice: берём queryset и ищем по pk
    qs = getattr(getattr(bf.field, "queryset", None), "all", None)
    if callable(qs):
        try:
            obj = bf.field.queryset.get(pk=value)
            return str(obj)
        except Exception:
            pass
    # Обычные choices
    for v, label in getattr(bf.field, "choices", []):
        if str(v) == value:
            return label
    return raw_value
