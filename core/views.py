# core/views_list.py
from django.contrib import messages
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .filters import make_filterset_class
from .tables import make_table_class


def settings(request):
    return render(request, "profile/settings.html")


class BaseModelListView(SingleTableMixin, FilterView):
    """
    Универсальный список:
    """
    model = None
    template_name = "common/base_list.html"

    # --- пагинация ---
    PAGE_SIZE_CHOICES = (12, 20, 50, 100)  # варианты для селекта
    default_per_page = 12  # дефолт
    table_pagination = {"per_page": default_per_page}  # будет перебиваться get_table_pagination()

    # --- конфиг остального ---
    list_fields = ()
    search_fields = ()
    fk_filters = ()
    extra_filters = None
    order_by = ("-id",)
    order_by_map = None
    verbose_map = None
    add_actions = True
    create_url_name = None

    # ---- helpers: per_page из GET ----
    def get_per_page(self) -> int:
        try:
            n = int(self.request.GET.get("per_page", "") or 0)
        except ValueError:
            n = 0
        return n if n in self.PAGE_SIZE_CHOICES else self.default_per_page

    # Если где-то используешь обычную пагинацию ListView:
    def get_paginate_by(self, queryset):
        return self.get_per_page()

    # Для django-tables2 (SingleTableMixin):
    def get_table_pagination(self, table):
        return {"per_page": self.get_per_page()}

    # ---- остальное как у тебя ----
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404 as e:
            msg = str(e)
            if "Invalid page" in msg or "Неправильная страница" in msg:
                q = request.GET.copy()
                q["page"] = 1
                return redirect(f"{request.path}?{q.urlencode()}")
            raise

    def get_table_class(self):
        return make_table_class(
            self.model,
            self.list_fields,
            order_by=self.order_by,
            add_actions=self.add_actions,
            verbose_map=self.get_verbose_map(),
            order_by_map=(self.order_by_map or {}),
        )

    def get_verbose_map(self):
        if self.verbose_map is not None:
            return self.verbose_map
        mapping = {}
        for f in getattr(self, "list_fields", []):
            try:
                field = self.model._meta.get_field(f)
                mapping[f] = field.verbose_name.capitalize()
            except Exception:
                mapping[f] = f.capitalize()
        return mapping

    def get_filterset_class(self):
        return make_filterset_class(
            self.model,
            search_fields=self.search_fields,
            fk_filters=self.fk_filters,
            extra_filters=(self.extra_filters or {}),
        )

    @property
    def table_class(self):
        return self.get_table_class()

    @property
    def filterset_class(self):
        return self.get_filterset_class()

    def get_queryset(self):
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.create_url_name:
            ctx["create_url"] = reverse(self.create_url_name)
            ctx["create_label"] = "Добавить"
        if self.model:
            ctx["verbose_name_plural"] = str(self.model._meta.verbose_name_plural).capitalize()

        # передаём в шаблон варианты и текущий выбор
        ctx["page_sizes"] = self.PAGE_SIZE_CHOICES
        ctx["per_page"] = self.get_per_page()
        return ctx


class BaseListCreateView(FormMixin, BaseModelListView):
    """
    На базе твоего BaseModelListView добавляем Create через модальное окно.
    """
    form_class = None
    create_fields = None
    success_message = "Объект создан."

    def get_form_class(self):
        if self.form_class:
            return self.form_class
        exclude = {"id", "created_at", "updated_at", "created_by", "updated_by"}
        fields = self.create_fields
        if not fields:
            fields = [
                f.name for f in self.model._meta.get_fields()
                if getattr(f, "editable", False) and f.concrete and f.name not in exclude
            ]
        return modelform_factory(self.model, fields=fields)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Накатываем Bootstrap-классы
        for name, field in form.fields.items():
            w = field.widget
            w_name = w.__class__.__name__.lower()
            input_type = getattr(w, "input_type", None)

            # Текстовые инпуты: text, email, number, url, tel, password, search
            if input_type in {"text", "email", "number", "url", "tel", "password", "search"}:
                w.attrs.setdefault("class", "form-control form-control-sm")
                w.attrs.setdefault("placeholder", field.label or name.capitalize())

            # Textarea
            elif "textarea" in w_name:
                w.attrs.setdefault("class", "form-control form-control-sm")
                w.attrs.setdefault("rows", 3)
                w.attrs.setdefault("placeholder", field.label or name.capitalize())

            # Select / ModelChoice / ModelMultipleChoice
            elif "select" in w_name:
                # и обычный Select, и SelectMultiple
                base = w.attrs.get("class", "")
                w.attrs["class"] = (base + " form-select form-select-sm").strip()

            # Checkbox
            elif "checkboxinput" in w_name:
                w.attrs.setdefault("class", "form-check-input")

            # Date / DateTime
            elif input_type in {"date", "datetime", "datetime-local", "time"}:
                w.attrs.setdefault("class", "form-control form-control-sm")

            else:
                # на всякий случай — дефолт
                base = w.attrs.get("class", "")
                w.attrs["class"] = (base + " form-control form-control-sm").strip()

        return form

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        obj = form.save(commit=False)
        user = getattr(self.request, "user", None)
        if user and hasattr(obj, "created_by") and getattr(obj, "created_by_id", None) is None:
            obj.created_by = user
        if user and hasattr(obj, "updated_by"):
            obj.updated_by = user
        obj.save()
        form.save_m2m()

        if self.success_message:
            messages.success(self.request, self.success_message)

        params = self.request.GET.copy()
        params.pop("page", None)
        qs = f"?{urlencode(params, doseq=True)}" if params else ""
        return redirect(f"{self.request.path}{qs}")

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context["open_create_modal"] = True
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("form", self.get_form())
        if not getattr(self, "create_url_name", None):
            ctx["open_modal_inplace"] = True
        return ctx
