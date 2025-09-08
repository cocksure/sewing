# core/filters.py
import django_filters as df
from django.db.models import Q, ForeignKey, OneToOneField


def make_filterset_class(
        model,
        *,
        search_fields=(),  # ("code","title","barcode")
        fk_filters=(),  # ("group","special_group")
        extra_filters=None,  # {"producible": df.BooleanFilter()}
):
    extra_filters = extra_filters or {}

    class AutoFilter(df.FilterSet):
        search = df.CharFilter(method="filter_search", label="Поиск", required=False)

        # core/filters.py  (фрагмент __init__ в AutoFilter)
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for name, field in self.form.fields.items():
                w = field.widget
                # текстовые поля (search и пр.)
                if getattr(w, "input_type", None) in {"text", "search", "number"}:
                    w.attrs.setdefault("class", "form-control form-control-sm")
                    w.attrs.setdefault("placeholder", field.label or name.capitalize())
                    w.attrs.setdefault("style", "min-width: 220px;")
                # селекты
                elif w.__class__.__name__.lower().endswith("select"):
                    w.attrs.setdefault("class", "form-select form-select-sm")
                    w.attrs.setdefault("style", "min-width: 220px;")
                # чекбоксы
                elif w.__class__.__name__.lower().endswith("checkboxinput"):
                    w.attrs.setdefault("class", "form-check-input")

        def filter_search(self, qs, name, value):
            if not value:
                return qs
            q = Q()
            for f in search_fields:
                q |= Q(**{f"{f}__icontains": value})
            return qs.filter(q)

    # PyCharm-friendly Meta
    AutoFilter.Meta = type("Meta", (), {"model": model, "fields": []})

    # FK-фильтры добавляем динамически
    for fname in fk_filters:
        field = model._meta.get_field(fname)
        if isinstance(field, (ForeignKey, OneToOneField)):
            qs = field.remote_field.model.objects.all()
            # ВАЖНО: указать field_name=fname (иначе будет ошибка "Cannot resolve keyword 'None'")
            AutoFilter.base_filters[fname] = df.ModelChoiceFilter(
                field_name=fname,
                queryset=qs,
                label=getattr(field, "verbose_name", None) or fname.capitalize(),
                required=False,
            )

    # Доп. фильтры (булевые и пр.)
    for name, flt in (extra_filters or {}).items():
        AutoFilter.base_filters[name] = flt

    return AutoFilter
