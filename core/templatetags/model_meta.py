# core/templatetags/model_meta.py
from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


# ------- базовые фильтры (были у тебя) -------
@register.filter
def verbose_name_plural(model):
    return model._meta.verbose_name_plural.capitalize()


@register.filter
def verbose_name(model):
    return model._meta.verbose_name.capitalize()


@register.filter
def app_label(obj):
    try:
        return obj._meta.app_label
    except Exception:
        return ""


@register.filter
def model_name(obj):
    try:
        return obj._meta.model_name
    except Exception:
        return ""


# ------- Маппинг явных имён урлов -------
# Ключ: (app_label, model_name) в нижнем регистре
# Значение: словарь action -> route_name
# deystviyalardegi izmneit udlaitlarga
ROUTE_MAP = {
    ("sewing", "sewingproductmodel"): {
        # если view/delete нет — оставляй "#"
        "view": "#",
        "edit": "sewing:model-edit",  # ← твой реальный роут редактирования
        "delete": "#",
    },
    ("sewing", "sewingorder"): {
        # если view/delete нет — оставляй "#"
        "view": "#",
        "edit": "sewing:orders-edit",  # ← твой реальный роут редактирования
        "delete": "#",
    },
    # добавляй сюда другие модели по мере необходимости
    # ("info","material"): {"view":"info:material-detail","edit":"info:material-edit","delete":"info:material-delete"},
}


@register.simple_tag
def url_for(obj, action: str):
    """
    Возвращает URL для действия (view|edit|delete).
    1) Сначала смотрит в ROUTE_MAP.
    2) Потом пробует угадать: <app>:<model>-<action>, затем <model>-<action>.
    3) Если не найдено — '#'.
    """
    try:
        app = obj._meta.app_label.lower()
        model = obj._meta.model_name.lower()
    except Exception:
        return "#"

    # 1) явная настройка
    mapping = ROUTE_MAP.get((app, model), {})
    route_name = mapping.get(action)
    if route_name and route_name != "#":
        try:
            return reverse(route_name, kwargs={"pk": obj.pk})
        except NoReverseMatch:
            pass  # попробуем fallback

    # 2) угадать по шаблону
    candidates = [f"{app}:{model}-{action}", f"{model}-{action}"]
    for name in candidates:
        try:
            return reverse(name, kwargs={"pk": obj.pk})
        except NoReverseMatch:
            continue

    return "#"
