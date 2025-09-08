# sewing/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet

from core.widgets import MaterialSelect2, ColorSelect2, OperationSelect2, SizeSelect2,  VariantSelect2
from info.models import Operation
from .models import (
    SewingProductModel, ModelVariant,
    VariantMaterial, VariantAccessory,
    VariantSize, VariantOperation
)


# ===== Общий миксин для компактных виджетов (без select2) =====
class SmallWidgetMixin:
    def _smallify(self):
        for f in self.fields.values():
            w = f.widget
            input_type = getattr(w, "input_type", None)
            clsname = w.__class__.__name__.lower()

            if input_type in {"text", "number", "search", "email", "file"}:
                w.attrs.setdefault("class", "form-control form-control-sm")
            elif clsname.endswith(("select", "selectmultiple")):
                w.attrs.setdefault("class", "form-select form-select-sm")
            elif clsname.endswith("checkboxinput"):
                w.attrs.setdefault("class", "form-check-input")


# ===== Форма модели (SPM) =====
class SewingProductModelForm(SmallWidgetMixin, forms.ModelForm):
    image_file = forms.ImageField(
        label="Изображение",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"})
    )

    class Meta:
        model = SewingProductModel
        fields = (
            "vendor_code", "name", "season", "image",
            "discount",
            "cutting_price", "transfer_price", "print_price", "embroidery_price",
            "sewing_loss_percent", "other_expenses_percent", "profitability", "commission",
            "category",
        )
        widgets = {
            "image": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._smallify()


class ModelVariantForm(SmallWidgetMixin, forms.ModelForm):
    class Meta:
        model = ModelVariant
        fields = (
            "kind",
            "name",
            "description",
            "work_type",
            "design_code",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._smallify()
        # для SAMPLE делаем name read-only (название подставится "Образец" в save())
        if self.instance and getattr(self.instance, "kind", None) == ModelVariant.VariantKind.SAMPLE:
            self.fields["name"].widget.attrs["readonly"] = True
            self.fields["name"].help_text = "Имя автоматически задано как «Образец»"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("kind") == ModelVariant.VariantKind.SAMPLE:
            cleaned["name"] = "Образец"
        return cleaned


# ===== Материалы варианта =====

class VariantMaterialForm(SmallWidgetMixin, forms.ModelForm):
    class Meta:
        model = VariantMaterial
        fields = (
            "material", "color", "count", "packing_type",
            "width", "height", "density", "loss",
            "price", "main", "notes", "used_parts"
        )
        widgets = {
            # AJAX select2 по группе «ОТП»
            "material": MaterialSelect2(
                group_name="ОТП",
                attrs={
                    "data-placeholder": "Начните вводить материал…",
                    "data-minimum-input-length": 1,
                    "data-dropdown-parent": "#materialFormModal",  # id модалки формы
                    "style": "width:100%",
                },
            ),
            "color": ColorSelect2(
                attrs={
                    "data-placeholder": "Начните вводить материал…",
                    "data-minimum-input-length": 1,
                    "data-dropdown-parent": "#materialFormModal",  # id модалки формы
                    "style": "width:100%",
                },
            ),
            # если хочешь — обычный select2 для M2M used_parts (не ajax)
            "used_parts": forms.SelectMultiple(attrs={
                "data-select2": "1",
                "data-placeholder": "Детали использования",
                "style": "width:100%",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._smallify()  # мелкие инпуты/селекты (select2 мы не трогаем)
        # color можно отсортировать/ограничить при желании
        # self.fields["color"].queryset = self.fields["color"].queryset.order_by("name")


class _BaseVMFS(BaseInlineFormSet):
    """Чтобы M2M used_parts был маленьким."""

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if "used_parts" in form.fields:
            form.fields["used_parts"].widget.attrs.setdefault("class", "form-select form-select-sm")


VariantMaterialFormSet = inlineformset_factory(
    ModelVariant, VariantMaterial,
    form=VariantMaterialForm, formset=_BaseVMFS,
    fields=VariantMaterialForm.Meta.fields,
    extra=1, can_delete=True
)


# ===== Аксессуары варианта =====
class VariantAccessoryForm(SmallWidgetMixin, forms.ModelForm):
    class Meta:
        model = VariantAccessory
        fields = ("accessory", "count", "price", "local_produce", "notes")

        widgets = {
            "accessory": MaterialSelect2(
                group_name="Аксессуары",
                attrs={"data-dropdown-parent": "#accessoryFormModal"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._smallify()


VariantAccessoryFormSet = inlineformset_factory(
    ModelVariant, VariantAccessory,
    form=VariantAccessoryForm,
    fields=VariantAccessoryForm.Meta.fields,
    extra=1, can_delete=True
)


# forms.py
class VariantSizeForm(SmallWidgetMixin, forms.ModelForm):
    class Meta:
        model = VariantSize
        fields = ("size", "notes")
        widgets = {
            "size": SizeSelect2(attrs={
                "data-dropdown-parent": "#sizeFormModal",  # важно для модалки
                "data-minimum-input-length": "1",  # можно вводить L, S и т.п.
                "data-placeholder": "Найдите размер…",
                "data-allow-clear": "true",
                "style": "width:100%",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._smallify()


VariantSizeFormSet = inlineformset_factory(
    ModelVariant, VariantSize,
    form=VariantSizeForm,
    fields=VariantSizeForm.Meta.fields,
    extra=1, can_delete=True
)


# ===== Операции варианта (без select2) =====
# sewing/forms.py

class VariantOperationForm(SmallWidgetMixin, forms.ModelForm):
    class Meta:
        model = VariantOperation
        fields = ("operation", "seconds")  # ← только эти два
        widgets = {
            "operation": OperationSelect2(attrs={
                "data-dropdown-parent": "#operationFormModal",  # id модалки с формой операций
                "data-placeholder": "Найдите операцию…",
            }),
            "seconds": forms.NumberInput(attrs={
                "class": "form-control form-control-sm",
                "min": 0,
                "step": 1,
                "placeholder": "Секунды",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._smallify()
        # показываем только активные операции (если есть флаг), иначе все
        try:
            qs = Operation.objects.filter(is_active=True)
        except Exception:
            qs = Operation.objects.all().order_by("name")
        self.fields["operation"].queryset = qs

        # опционально: подпись как "Название — N сек."
        self.fields["operation"].label_from_instance = (
            lambda
                obj: f"{getattr(obj, 'name', 'Без имени')} — {getattr(obj, 'seconds', getattr(obj, 'default_seconds', 0))} сек."
        )


VariantOperationFormSet = inlineformset_factory(
    ModelVariant, VariantOperation,
    form=VariantOperationForm,
    fields=VariantOperationForm.Meta.fields,
    extra=1, can_delete=True
)


class FillFromVariantForm(forms.Form):
    source_variant = forms.ModelChoiceField(
        label="Вариант-источник",
        queryset=ModelVariant.objects.select_related("product_model").all(),
        required=True,
        widget=VariantSelect2(attrs={
            "data-placeholder": "Найдите вариант…",
            "data-minimum-input-length": "0",
            "style": "width:100%",
        })
    )
    replace = forms.BooleanField(
        label="Очистить текущие записи перед копированием",
        required=False
    )
