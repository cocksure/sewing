# materials/forms.py
from django import forms
from django.forms import ModelForm
from django_select2.forms import Select2Widget

from core.widgets import MaterialGroupSelect2, ColorSelect2
from info.models import Material


class MaterialForm(ModelForm):
    class Meta:
        model = Material
        fields = [
            "code", "title", "type", "group", "special_group", "m_unit", "color",
            "barcode", "accounting_code", "producible", "planned_cost"
        ]
        labels = {
            "code": "Код", "title": "Название", "type": "Тип", "group": "Группа",
            "special_group": "Спец. группа", "m_unit": "Ед. изм.", "color": "Цвет",
            "barcode": "Штрих-код", "accounting_code": "Бухгалтерский код",
            "producible": "Производимый", "planned_cost": "Плановая цена",
        }
        widgets = {
            "code": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "off", "placeholder": "Напр. MAT001"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Наименование материала"}),
            "type": forms.TextInput(attrs={"class": "form-control", "placeholder": "Тип/категория"}),
            "barcode": forms.TextInput(attrs={"class": "form-control", "placeholder": "EAN/QR при наличии"}),
            "accounting_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Бух. код"}),
            "planned_cost": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "inputmode": "decimal", "placeholder": "0.00"}),
            "special_group": forms.Select(attrs={"class": "form-select"}),
            "m_unit": forms.Select(attrs={"class": "form-select"}),

            "group": Select2Widget(attrs={
                "data-placeholder": "Выберите группу",
                "data-allow-clear": "true",
                "style": "width:100%",
            }),
            "color": Select2Widget(attrs={
                "data-placeholder": "Цвет",
                "data-allow-clear": "true",
                "style": "width:100%",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # чекбоксу свой класс
        self.fields["producible"].widget.attrs.update({"class": "form-check-input"})
        for name in ("group", "color"):
            if name in self.fields and hasattr(self.fields[name].queryset, "order_by"):
                self.fields[name].queryset = self.fields[name].queryset.order_by("name")

    # дружелюбный ввод цены: "12,34" -> 12.34
    def clean_planned_cost(self):
        val = self.cleaned_data.get("planned_cost")
        raw = self.data.get("planned_cost", "")
        if isinstance(raw, str) and "," in raw and (val is None or str(val).find(",") != -1):
            try:
                return float(raw.replace(" ", "").replace(",", "."))
            except ValueError:
                pass  # упадёт стандартной ошибкой ниже
        return val
