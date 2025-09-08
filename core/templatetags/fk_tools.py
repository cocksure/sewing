# core/templatetags/fk_tools.py
from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

# Явные маршруты списков для моделей (app_label, model_name) -> route_name
FK_LIST_ROUTES = {
    ("info", "material"): "materials-list",
    ("info", "materialgroup"): "material-groups",
    ("info", "color"): "color-list",            # подставь свой name
    ("sewing", "operation"): "operation-list",  # подставь свой name
    ("info", "size"): "size-list",              # подставь свой name
    # добавляй по мере необходимости
}

@register.simple_tag
def fk_list_url(bound_field):
    """
    Возвращает URL списка справочника для FK-поля формы.
    Если явного маппинга нет — пробует угадать по шаблонам имен.
    Если ничего не получилось — вернёт "#".
    """
    # Достаём модель из queryset поля формы
    field = getattr(bound_field, "field", None)
    qs = getattr(field, "queryset", None)
    model = getattr(qs, "model", None)
    if not model:
        return "#"

    app = model._meta.app_label.lower()
    name = model._meta.model_name.lower()

    # 1) Явная карта
    route = FK_LIST_ROUTES.get((app, name))
    if route:
        try:
            return reverse(route)
        except NoReverseMatch:
            pass

    # 2) Эвристика по распространённым паттернам
    candidates = [
        f"{app}:{name}-list",
        f"{name}-list",
        f"{app}:{name}s",        # иногда делают во мн. числе
        f"{app}:{name}list",     # запасной вариант
    ]
    for r in candidates:
        try:
            return reverse(r)
        except NoReverseMatch:
            continue

    return "#"