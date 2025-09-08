# core/tables.py
import django_tables2 as tables


def make_table_class(
        model,
        fields,
        *,
        order_by=("-id",),
        add_actions=True,
        template_name="django_tables2/bootstrap5.html",
        verbose_map=None,
        order_by_map=None,
        table_attrs=None,
        paginate=True,
):
    verbose_map = verbose_map or {}
    order_by_map = order_by_map or {}
    table_attrs = table_attrs or {"class": "table table-hover align-middle"}

    attrs = {}

    # Сформируем колонки
    for f in fields:
        col_kwargs = {}
        if f in verbose_map:
            col_kwargs["verbose_name"] = verbose_map[f]
        if f in order_by_map:
            col_kwargs["order_by"] = order_by_map[f]

        # Дата-время — своим классом
        if f.endswith("_at"):
            col = tables.DateTimeColumn(format="d.m.Y H:i", **col_kwargs)
        else:
            col = tables.Column(**col_kwargs)

        attrs[f] = col

    # Универсальная колонка действий (опционально)
    if add_actions:
        attrs["actions"] = tables.TemplateColumn(
            template_name="common/_row_actions.html",
            orderable=False,
            verbose_name="Действия",  # <-- заголовок
            attrs={"th": {"class": "text-end"}, "td": {"class": "text-end"}},  # выравнивание
        )

    # PyCharm-friendly Meta через type(...)
    meta_fields = tuple(fields) + (("actions",) if add_actions else ())

    meta_attrs = {
        "model": model,
        "template_name": template_name,
        "fields": meta_fields,
        "order_by": order_by,
        "attrs": table_attrs,
    }

    # Добавляем пагинацию в Meta
    if paginate:
        meta_attrs["per_page"] = 12  # или динамически из view

    Meta = type("Meta", (), meta_attrs)
    attrs["Meta"] = Meta

    # Сгенерируем класс таблицы
    cls_name = f"{model.__name__}AutoTable"
    return type(cls_name, (tables.Table,), attrs)

