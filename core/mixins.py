from base64 import b64encode

from django.db import models
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django.http import HttpResponse

from .middlewares import get_current_user


class AuditUserSaveMixin(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk and hasattr(self, "created_by") and self.created_by_id is None:
                self.created_by = user
            if hasattr(self, "updated_by"):
                self.updated_by = user
        return super().save(*args, **kwargs)


IGNORED_PARAMS = {"page", "page_size", "o", "ordering", "search", "csrfmiddlewaretoken", "format"}


class QueryParamsFilterMixin:
    """
    Точные фильтры из query params:
    ?status=1&name__icontains=abc&created_at__date=2025-08-31
    """

    def apply_param_filters(self, qs):
        params = self.request.GET
        filters = {}
        for key, val in params.items():
            if key in IGNORED_PARAMS or val == "":
                continue
            # Разрешаем и "field" и "field__lookup"
            if LOOKUP_SEP in key or hasattr(qs.model, key):
                filters[key] = val
        return qs.filter(**filters) if filters else qs


class SearchOrderingMixin:
    """
    Поиск (?search=) по search_fields и сортировка (?o=field|-field) по ordering_fields.
    """
    search_fields = ()  # напр.: ("title", "code", "name")
    ordering_fields = ()  # напр.: ("id", "created_at", "title")
    default_ordering = None  # напр.: ("-created_at",) или "title"

    def apply_search(self, qs):
        term = self.request.GET.get("search")
        if term and self.search_fields:
            q = Q()
            for field in self.search_fields:
                q |= Q(**{f"{field}__icontains": term})
            qs = qs.filter(q)
        return qs

    def apply_ordering(self, qs):
        param = self.request.GET.get("o") or self.request.GET.get("ordering")
        fields = set(self.ordering_fields or [])
        if param:
            # Поддержка нескольких полей: ?o=field1,-field2
            requested = [p.strip() for p in param.split(",") if p.strip()]
            valid = []
            for f in requested:
                raw = f[1:] if f.startswith("-") else f
                if not fields or raw in fields:
                    valid.append(f)
            if valid:
                return qs.order_by(*valid)
        # если параметр не задан — применим дефолт
        if self.default_ordering:
            if isinstance(self.default_ordering, (list, tuple)):
                return qs.order_by(*self.default_ordering)
            return qs.order_by(self.default_ordering)
        return qs


class PageSizeMixin:
    """
    Позволяет управлять размером страницы: ?page_size=50
    """
    paginate_by = 25
    max_page_size = 1000
    page_size_param = "page_size"

    def get_paginate_by(self, queryset):
        try:
            size = int(self.request.GET.get(self.page_size_param) or self.paginate_by or 25)
        except (TypeError, ValueError):
            size = self.paginate_by or 25
        size = max(1, min(size, self.max_page_size))
        return size


def _msg_headers(resp: HttpResponse, text: str, typ: str = "info"):
    resp["X-Message-B64"] = b64encode(text.encode("utf-8")).decode("ascii")
    resp["X-Message-Type"] = typ
    return resp


class AjaxMessageMixin:
    """Возвращает 204 + X-Message(X-Message-B64) для AJAX, иначе — django messages + redirect."""

    def ajax_or_redirect(self, request, *, text: str, typ: str = "success", redirect_to: str = None):
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if is_ajax:
            resp = HttpResponse(status=204)
            return _msg_headers(resp, text, typ)
        # non-AJAX -> через django messages + redirect
        from django.contrib import messages
        messages.add_message(request, getattr(messages, typ.upper(), messages.INFO), text)
        return redirect_to
