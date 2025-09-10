# core/templatetags/dict_tools.py
from django import template

register = template.Library()


# zakazdegi ordersizecount uchun ishlatilingan
@register.filter
def dict_get(d, key):
    try:
        return d.get(key)
    except Exception:
        return None
