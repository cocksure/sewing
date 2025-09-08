# sewing/views.py
# helpers (можешь вынести повыше в файл)
from base64 import b64encode

from django.contrib import messages
from django.db import transaction
from django.db.models import Case, When, IntegerField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View

from core.mixins import AjaxMessageMixin
from core.views import BaseModelListView
from info.models import UploadedImage
from sewing import models
from .forms import (
    SewingProductModelForm, ModelVariantForm,
    VariantSizeFormSet, VariantOperationFormSet, VariantAccessoryForm, VariantOperationForm, VariantSizeForm,
    FillFromVariantForm
)
from .forms import VariantMaterialForm
from .models import ModelVariant, VariantMaterial
from .models import SewingProductModel
from .utils import make_clone_name


def _msg_headers(resp, text: str, typ: str = "info"):
    """Укладываем текст в Base64 + тип в заголовки ответа."""
    resp["X-Message-B64"] = b64encode(text.encode("utf-8")).decode("ascii")
    resp["X-Message-Type"] = typ
    return resp


# Шаг 1: экран создания модели + первого варианта (без модалок)
class SewingProductModelCreateView(View):
    template_name = "sewing/model_create.html"

    def get(self, request):
        return render(request, self.template_name, {
            "form_spm": SewingProductModelForm(prefix="spm"),
            "form_var": ModelVariantForm(prefix="var"),
        })

    def post(self, request):
        form_spm = SewingProductModelForm(request.POST, request.FILES, prefix="spm")
        form_var = ModelVariantForm(request.POST, request.FILES, prefix="var")

        if not (form_spm.is_valid() and form_var.is_valid()):
            messages.error(request, "Проверьте поля формы.")
            return render(request, self.template_name, {
                "form_spm": form_spm,
                "form_var": form_var
            })

        with transaction.atomic():
            # 1) создаём/обновляем SPM, но сначала готовим FK на UploadedImage
            spm = form_spm.save(commit=False)

            img_file = form_spm.cleaned_data.get("image_file")
            if img_file:
                up = UploadedImage.objects.create(
                    image=img_file,
                    created_by=getattr(request, "user", None) or None
                )
                spm.image = up  # FK на загруженную картинку

            spm.save()

            # 2) создаём первый вариант
            variant = form_var.save(commit=False)
            variant.product_model = spm

            # Если у варианта есть поле kind и он SAMPLE — подставим имя
            if hasattr(variant, "kind"):
                # если у тебя Enum/Choices, сравнивай корректно:
                # например: if variant.kind == ModelVariant.VariantKind.SAMPLE:
                try:
                    if variant.kind == ModelVariant.VariantKind.SAMPLE and not variant.name:
                        variant.name = "Образец"
                except Exception:
                    # если у тебя Choices-строка ('sample'):
                    if str(getattr(variant, "kind", "")) == "sample" and not variant.name:
                        variant.name = "Образец"

            variant.save()
            form_var.save_m2m()

        messages.success(request, "Модель и первый вариант созданы.")
        return redirect(reverse("sewing:model-edit", args=[spm.pk]))


class SewingProductModelEditView(View):
    template_name = "sewing/model_edit.html"

    def _group_variants(self, spm):
        """Возвращает сгруппированные и отсортированные варианты."""
        variants_qs = (
            spm.variants.select_related("work_type")
            .prefetch_related("materials", "accessories")
            .order_by(
                Case(
                    When(kind=ModelVariant.VariantKind.MARKETING, then=0),
                    When(kind=ModelVariant.VariantKind.SAMPLE, then=1),
                    When(kind=ModelVariant.VariantKind.PLANNED, then=2),
                    default=3,
                    output_field=IntegerField(),
                ),
                "id",
            )
        )
        variants_by_kind = {
            ModelVariant.VariantKind.MARKETING: [],
            ModelVariant.VariantKind.SAMPLE: [],
            ModelVariant.VariantKind.PLANNED: [],
        }
        for v in variants_qs:
            variants_by_kind[v.kind].append(v)
        return variants_by_kind

    def _build_context(self, spm, form_spm, form_var):
        """Готовит контекст для шаблона с группировками и счетчиками."""
        variants_by_kind = self._group_variants(spm)

        marketing_variants = variants_by_kind.get(ModelVariant.VariantKind.MARKETING, [])
        sample_variants = variants_by_kind.get(ModelVariant.VariantKind.SAMPLE, [])
        planned_variants = variants_by_kind.get(ModelVariant.VariantKind.PLANNED, [])

        return {
            "spm": spm,
            "form_spm": form_spm,
            "form_var": form_var,
            "variants_by_kind": variants_by_kind,
            # отдельные списки для удобного рендера
            "marketing_variants": marketing_variants,
            "sample_variants": sample_variants,
            "planned_variants": planned_variants,
            # счётчики для заголовков
            "marketing_count": len(marketing_variants),
            "sample_count": len(sample_variants),
            "planned_count": len(planned_variants),
        }

    def get(self, request, pk):
        spm = get_object_or_404(SewingProductModel.objects.select_related("category"), pk=pk)
        form_spm = SewingProductModelForm(instance=spm, prefix="spm")
        form_var = ModelVariantForm(prefix="var")
        context = self._build_context(spm, form_spm, form_var)
        return render(request, self.template_name, context)

    def post(self, request, pk):
        spm = get_object_or_404(SewingProductModel, pk=pk)

        # --- Сохранение модели ---
        if request.POST.get("action") == "save_spm":
            form_spm = SewingProductModelForm(request.POST, request.FILES, instance=spm, prefix="spm")
            form_var = ModelVariantForm(prefix="var")  # пустая для рендера страницы
            if form_spm.is_valid():
                obj = form_spm.save(commit=False)

                uploaded = form_spm.cleaned_data.get("image_file")
                if uploaded:
                    ui = UploadedImage.objects.create(image=uploaded)
                    obj.image = ui

                obj.save()
                form_spm.save_m2m()
                messages.success(request, "Модель обновлена.")
                return redirect(request.path)

            # невалидно: вернуть страницу с тем же контекстом
            context = self._build_context(spm, form_spm, form_var)
            return render(request, self.template_name, context)

        # --- Добавление варианта ---
        if request.POST.get("action") == "add_variant":
            form_var = ModelVariantForm(request.POST, request.FILES, prefix="var")
            form_spm = SewingProductModelForm(instance=spm, prefix="spm")
            if form_var.is_valid():
                mv = form_var.save(commit=False)
                mv.product_model = spm
                mv.save()
                form_var.save_m2m()
                messages.success(request, "Вариант добавлен.")
                return redirect(request.path)

            # невалидно: вернуть страницу с тем же контекстом
            context = self._build_context(spm, form_spm, form_var)
            return render(request, self.template_name, context)

        # fallback
        return redirect(request.path)


class VariantEditView(View):
    def get(self, request, pk):
        v = get_object_or_404(ModelVariant, pk=pk)
        form = ModelVariantForm(instance=v)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return render(request, "sewing/_modal_variant_edit.html", {
                "title": f"Редактировать вариант — {v.name}",
                "form": form,
                "action_url": reverse("sewing:variant-edit", args=[v.pk]),
            })
        return redirect(reverse("sewing:model-edit", args=[v.product_model_id]) + f"#v{v.pk}")

    def post(self, request, pk):
        v = get_object_or_404(ModelVariant, pk=pk)
        form = ModelVariantForm(request.POST, instance=v)
        if form.is_valid():
            form.save()
            return redirect(reverse("sewing:model-edit", args=[v.product_model_id]) + f"#v{v.pk}")
        # вернуть модалку с ошибками
        return render(request, "sewing/_modal_variant_edit.html", {
            "title": f"Редактировать вариант — {v.name}",
            "form": form,
            "action_url": reverse("sewing:variant-edit", args=[v.pk]),
        })


class VariantSizesEditView(View):
    template_name = "sewing/_modal_variant_sizes.html"

    def get(self, request, pk):
        v = get_object_or_404(ModelVariant, pk=pk)
        fs = VariantSizeFormSet(instance=v, prefix="sizes")

        # Проверяем какие размеры доступны

        return render(request, self.template_name, {"variant": v, "fs": fs})

    def post(self, request, pk):
        v = get_object_or_404(ModelVariant, pk=pk)
        fs = VariantSizeFormSet(request.POST, instance=v, prefix="sizes")
        if fs.is_valid():
            fs.save();
            messages.success(request, "Размеры сохранены.")
            return redirect(reverse("sewing:model-edit", args=[v.product_model_id]) + "#v" + str(v.pk))
        return render(request, self.template_name, {"variant": v, "fs": fs})


class VariantOperationsEditView(View):
    template_name = "sewing/_modal_variant_operations.html"

    def get(self, request, pk):
        v = get_object_or_404(ModelVariant, pk=pk)
        fs = VariantOperationFormSet(instance=v, prefix="ops")
        return render(request, self.template_name, {"variant": v, "fs": fs})

    def post(self, request, pk):
        v = get_object_or_404(ModelVariant, pk=pk)
        fs = VariantOperationFormSet(request.POST, instance=v, prefix="ops")
        if fs.is_valid():
            fs.save();
            messages.success(request, "Операции сохранены.")
            return redirect(reverse("sewing:model-edit", args=[v.product_model_id]) + "#v" + str(v.pk))
        return render(request, self.template_name, {"variant": v, "fs": fs})


class VariantCloneView(View):
    def post(self, request, pk):
        variant = (ModelVariant.objects
                   .select_related("product_model", "work_type")
                   .prefetch_related("materials", "accessories", "sizes", "operations__operation")
                   .get(pk=pk))

        with transaction.atomic():
            # имя: для SAMPLE оставляем "Образец", иначе — умный нейминг
            if variant.kind == ModelVariant.VariantKind.SAMPLE:
                new_name = "Образец"
            else:
                new_name = make_clone_name(variant.product_model_id, variant.name)

            new_variant = ModelVariant.objects.create(
                product_model=variant.product_model,
                kind=variant.kind,
                name=new_name,
                description=variant.description,
                work_type=variant.work_type,
                loss=variant.loss,
                design_code=variant.design_code,
                cloned=True,
            )

            # --- материалы ---
            mats_to_create = [
                models.VariantMaterial(
                    variant=new_variant,
                    material=vm.material,
                    count=vm.count,
                    color=vm.color,
                    packing_type=vm.packing_type,
                    width=vm.width,
                    height=vm.height,
                    density=vm.density,
                    loss=vm.loss,
                    notes=vm.notes,
                    price=vm.price,
                    main=vm.main,
                )
                for vm in variant.materials.all()
            ]
            models.VariantMaterial.objects.bulk_create(mats_to_create)

            # --- аксессуары ---
            accs_to_create = [
                models.VariantAccessory(
                    variant=new_variant,
                    accessory=va.accessory,
                    count=va.count,
                    notes=va.notes,
                    price=va.price,
                    local_produce=va.local_produce,
                )
                for va in variant.accessories.all()
            ]
            models.VariantAccessory.objects.bulk_create(accs_to_create)

            # --- размеры ---
            sizes_to_create = [
                models.VariantSize(
                    variant=new_variant,
                    size=s.size,  # важно: копируем FK на Size
                    notes=s.notes,
                )
                for s in variant.sizes.select_related("size").all()
            ]
            models.VariantSize.objects.bulk_create(sizes_to_create)

            # --- операции ---
            ops_to_create = [
                models.VariantOperation(
                    variant=new_variant,
                    operation=o.operation,  # FK на Operation
                    seconds=getattr(o, "seconds", None)  # текущее поле времени
                            or getattr(o, "duration", None)  # на случай старых данных
                            or (o.operation.default_duration if o.operation_id else 0),
                    notes=getattr(o, "notes", None),
                )
                for o in variant.operations.select_related("operation").all()
            ]
            models.VariantOperation.objects.bulk_create(ops_to_create)

        messages.success(request, f"Вариант «{variant.name}» клонирован как «{new_name}».")
        return redirect(
            reverse("sewing:model-edit", args=[new_variant.product_model_id]) + f"#v{new_variant.id}"
        )


class ModelsListView(BaseModelListView):
    model = models.SewingProductModel
    template_name = "common/base_list.html"
    paginate_by = 12

    list_fields = (
        "vendor_code", "name", "season", "cutting_price", "transfer_price", "print_price", "embroidery_price",
        "profitability", "category",)
    search_fields = ("vendor_code", "name",)
    fk_filters = ("")
    order_by = ("-id",)
    order_by_map = {}

    create_url_name = "sewing:model-create"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("category", "image")
        )


# ------------------ Variant Materials ----------------- #

class VariantMaterialsListView(View):
    def get(self, request, pk):
        variant = get_object_or_404(ModelVariant, pk=pk)
        materials = variant.materials.select_related("material", "color")
        return render(request, "sewing/_modal_variant_materials_list.html", {
            "variant": variant,
            "materials": materials,
        })


class VariantMaterialCreateView(AjaxMessageMixin, View):
    def get(self, request, pk):
        get_object_or_404(ModelVariant, pk=pk)
        form = VariantMaterialForm()
        return render(request, "sewing/_modal_variant_material_form.html", {"form": form})

    def post(self, request, pk):  # pk = variant.pk
        variant = get_object_or_404(ModelVariant, pk=pk)
        form = VariantMaterialForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.variant = variant
            obj.save()
            form.save_m2m()
            return self.ajax_or_redirect(
                request,
                text="Материал добавлен.",
                typ="success",
                redirect_to=redirect(reverse("sewing:variant-materials", args=[variant.pk]))
            )

        # Если форма невалидна:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            # При ajax возвращаем html фрагмент с ошибками
            return render(request, "sewing/_modal_variant_material_form.html", {"form": form})
        else:
            # При обычной отправке показываем сообщение и редиректим
            messages.error(request, "Ошибка в форме материала.")
            return redirect(reverse("sewing:variant-materials", args=[variant.pk]))


class VariantMaterialUpdateView(AjaxMessageMixin, View):
    def get(self, request, pk):  # pk = material.pk
        obj = get_object_or_404(VariantMaterial, pk=pk)
        form = VariantMaterialForm(instance=obj)
        return render(request, "sewing/_modal_variant_material_form.html", {"form": form})

    def post(self, request, pk):  # pk = material.pk
        obj = get_object_or_404(VariantMaterial, pk=pk)
        form = VariantMaterialForm(request.POST, instance=obj)

        if form.is_valid():
            form.save()
            # AJAX -> 204 + X-Message; не-AJAX -> messages + redirect
            return self.ajax_or_redirect(
                request,
                text="Материал обновлён.",
                typ="success",
                redirect_to=redirect(reverse("sewing:variant-materials", args=[obj.variant_id]))
            )

        # невалидно: вернуть форму с ошибками в модалку (AJAX) либо показать сообщение и редирект
        is_ajax = (request.headers.get("x-requested-with") == "XMLHttpRequest"
                   or request.headers.get("X-Requested-With") == "XMLHttpRequest")
        if is_ajax:
            return render(request, "sewing/_modal_variant_material_form.html", {"form": form})

        messages.error(request, "Исправьте ошибки в форме материала.")
        return redirect(reverse("sewing:variant-materials", args=[obj.variant_id]))


class VariantMaterialDeleteView(AjaxMessageMixin, View):
    def post(self, request, pk):  # pk = material.pk
        vm = get_object_or_404(VariantMaterial, pk=pk)
        variant_id = vm.variant_id
        vm.delete()

        # универсально: AJAX -> 204 + X-Message, не-AJAX -> messages + redirect
        return self.ajax_or_redirect(
            request,
            text="Материал удалён.",
            typ="success",
            redirect_to=redirect(reverse("sewing:variant-materials", args=[variant_id]))
        )


# ----------------- Variant Accessory ----------------- #

class VariantAccessoriesListView(View):
    def get(self, request, pk):
        variant = get_object_or_404(ModelVariant, pk=pk)
        accessories = variant.accessories.select_related("accessory").all()
        return render(request, "sewing/_modal_variant_accessories_list.html", {
            "variant": variant,
            "accessories": accessories,
        })


class VariantAccessoryCreateView(AjaxMessageMixin, View):
    def get(self, request, variant_id):
        # просто убедимся, что вариант существует (404 если нет)
        get_object_or_404(ModelVariant, pk=variant_id)
        form = VariantAccessoryForm()
        return render(request, "sewing/_modal_variant_accessory_form.html", {"form": form})

    def post(self, request, variant_id):
        variant = get_object_or_404(ModelVariant, pk=variant_id)
        form = VariantAccessoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.variant = variant
            obj.save()
            form.save_m2m()

            # AJAX -> 204 + X-Message; не-AJAX -> messages + redirect
            return self.ajax_or_redirect(
                request,
                text="Аксессуар добавлен.",
                typ="success",
                redirect_to=redirect(reverse("sewing:variant-accessories", args=[variant_id]))
            )

        # невалидно
        is_ajax = (request.headers.get("x-requested-with") == "XMLHttpRequest"
                   or request.headers.get("X-Requested-With") == "XMLHttpRequest")
        if is_ajax:
            return render(request, "sewing/_modal_variant_accessory_form.html", {"form": form})

        messages.error(request, "Проверьте поля формы аксессуара.")
        return redirect(reverse("sewing:variant-accessories", args=[variant_id]))


class VariantAccessoryUpdateView(AjaxMessageMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(models.VariantAccessory, pk=pk)
        form = VariantAccessoryForm(instance=obj)
        return render(request, "sewing/_modal_variant_accessory_form.html", {"form": form})

    def post(self, request, pk):
        obj = get_object_or_404(models.VariantAccessory, pk=pk)
        form = VariantAccessoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return self.ajax_or_redirect(
                request,
                text="Аксессуар обновлён.",
                typ="success",
                redirect_to=redirect(reverse("sewing:variant-accessories", args=[obj.variant_id]))
            )

        is_ajax = (request.headers.get("x-requested-with") == "XMLHttpRequest"
                   or request.headers.get("X-Requested-With") == "XMLHttpRequest")
        if is_ajax:
            return render(request, "sewing/_modal_variant_accessory_form.html", {"form": form})

        messages.error(request, "Исправьте ошибки в форме аксессуара.")
        return redirect(reverse("sewing:variant-accessories", args=[obj.variant_id]))


class VariantAccessoryDeleteView(AjaxMessageMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(models.VariantAccessory, pk=pk)
        variant_id = obj.variant_id
        obj.delete()

        return self.ajax_or_redirect(
            request,
            text="Аксессуар удалён.",
            typ="success",
            redirect_to=redirect(reverse("sewing:variant-accessories", args=[variant_id]))
        )


# ------------------ Variant Operation ----------------- #

class VariantOperationsListView(View):
    def get(self, request, pk):
        variant = get_object_or_404(ModelVariant, pk=pk)
        operations = (
            variant.operations
            .select_related("operation")  # справочник info.Operation
            .all()
        )
        return render(
            request,
            "sewing/_modal_variant_operations_list.html",
            {"variant": variant, "operations": operations},
        )


class VariantOperationCreateView(AjaxMessageMixin, View):
    def get(self, request, variant_id):
        # убеждаемся, что вариант существует
        get_object_or_404(ModelVariant, pk=variant_id)
        form = VariantOperationForm()
        return render(request, "sewing/_modal_variant_operation_form.html", {"form": form})

    def post(self, request, variant_id):
        variant = get_object_or_404(ModelVariant, pk=variant_id)
        form = VariantOperationForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.variant = variant
            obj.save()

            return self.ajax_or_redirect(
                request,
                text="Операция добавлена.",
                typ="success",
                redirect_to=redirect(reverse("sewing:variant-operations", args=[variant_id]))
            )

        # ошибки: для AJAX — вернуть html формы, для обычного — messages + redirect
        is_ajax = (request.headers.get("x-requested-with") == "XMLHttpRequest"
                   or request.headers.get("X-Requested-With") == "XMLHttpRequest")
        if is_ajax:
            return render(request, "sewing/_modal_variant_operation_form.html", {"form": form})

        messages.error(request, "Проверьте поля формы операции.")
        return redirect(reverse("sewing:variant-operations", args=[variant_id]))


class VariantOperationUpdateView(AjaxMessageMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(models.VariantOperation, pk=pk)
        form = VariantOperationForm(instance=obj)
        return render(request, "sewing/_modal_variant_operation_form.html", {"form": form})

    def post(self, request, pk):
        obj = get_object_or_404(models.VariantOperation, pk=pk)
        form = VariantOperationForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return self.ajax_or_redirect(
                request,
                text="Операция обновлена.",
                typ="success",
                redirect_to=redirect(reverse("sewing:variant-operations", args=[obj.variant_id]))
            )

        is_ajax = (request.headers.get("x-requested-with") == "XMLHttpRequest"
                   or request.headers.get("X-Requested-With") == "XMLHttpRequest")
        if is_ajax:
            return render(request, "sewing/_modal_variant_operation_form.html", {"form": form})

        messages.error(request, "Исправьте ошибки в форме операции.")
        return redirect(reverse("sewing:variant-operations", args=[obj.variant_id]))


class VariantOperationDeleteView(AjaxMessageMixin, View):
    def post(self, request, pk):
        op = get_object_or_404(models.VariantOperation, pk=pk)
        variant_id = op.variant_id
        op.delete()

        return self.ajax_or_redirect(
            request,
            text="Операция удалена.",
            typ="success",
            redirect_to=redirect(reverse("sewing:variant-operations", args=[variant_id]))
        )


# ------------------ Variant Sizes ----------------- #

class VariantSizesListView(View):
    """Список размеров (для первой модалки)"""

    def get(self, request, pk):
        variant = get_object_or_404(ModelVariant, pk=pk)
        sizes = variant.sizes.select_related("size").all()
        return render(request, "sewing/_modal_variant_sizes_list.html", {
            "variant": variant,
            "sizes": sizes,
        })


class VariantSizeCreateView(AjaxMessageMixin, View):
    """Форма создания (вторая модалка)"""

    def get(self, request, variant_id):
        # 404, если варианта нет
        get_object_or_404(ModelVariant, pk=variant_id)
        form = VariantSizeForm()
        return render(request, "sewing/_modal_variant_size_form.html", {"form": form})

    def post(self, request, variant_id):
        variant = get_object_or_404(ModelVariant, pk=variant_id)
        form = VariantSizeForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.variant = variant
            obj.save()
            form.save_m2m()

            # AJAX → 204 + X-Message; не-AJAX → messages + redirect
            return self.ajax_or_redirect(
                request,
                text="Размер добавлен.",
                typ="success",
                redirect_to=redirect(reverse("sewing:variant-sizes", args=[variant_id]))
            )

        # Ошибки: вернуть HTML формы для AJAX, messages+redirect для обычного запроса
        is_ajax = (request.headers.get("x-requested-with") == "XMLHttpRequest"
                   or request.headers.get("X-Requested-With") == "XMLHttpRequest")
        if is_ajax:
            return render(request, "sewing/_modal_variant_size_form.html", {"form": form})

        messages.error(request, "Проверьте поля размера.")
        return redirect(reverse("sewing:variant-sizes", args=[variant_id]))


class VariantSizeUpdateView(AjaxMessageMixin, View):
    """Форма редактирования (вторая модалка)"""

    def get(self, request, pk):
        obj = get_object_or_404(models.VariantSize, pk=pk)
        form = VariantSizeForm(instance=obj)
        return render(request, "sewing/_modal_variant_size_form.html", {"form": form})

    def post(self, request, pk):
        obj = get_object_or_404(models.VariantSize, pk=pk)
        form = VariantSizeForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return self.ajax_or_redirect(
                request,
                text="Размер обновлён.",
                typ="success",
                redirect_to=redirect(reverse("sewing:variant-sizes", args=[obj.variant_id]))
            )

        is_ajax = (request.headers.get("x-requested-with") == "XMLHttpRequest"
                   or request.headers.get("X-Requested-With") == "XMLHttpRequest")
        if is_ajax:
            return render(request, "sewing/_modal_variant_size_form.html", {"form": form})

        messages.error(request, "Исправьте ошибки в форме размера.")
        return redirect(reverse("sewing:variant-sizes", args=[obj.variant_id]))


class VariantSizeDeleteView(AjaxMessageMixin, View):
    """Удаление из списка (первая модалка, через AJAX)"""

    def post(self, request, pk):
        vs = get_object_or_404(models.VariantSize, pk=pk)
        variant_id = vs.variant_id
        vs.delete()

        return self.ajax_or_redirect(
            request,
            text="Размер удалён.",
            typ="success",
            redirect_to=redirect(reverse("sewing:variant-sizes", args=[variant_id]))
        )


class VariantFillFromView(View):
    """Одна вьюха для accessories/operations (kind='accessories' | 'operations')."""
    kind = None  # заполняется при as_view(..., kind="accessories"|"operations")

    def get(self, request, pk):
        variant = get_object_or_404(ModelVariant, pk=pk)
        form = FillFromVariantForm()
        return render(request, "sewing/_modal_fill_from_variant.html", {
            "form": form,
            "kind": self.kind,
            "variant": variant,
        })

    def post(self, request, pk):
        target = get_object_or_404(ModelVariant, pk=pk)
        form = FillFromVariantForm(request.POST)
        if not form.is_valid():
            return render(request, "sewing/_modal_fill_from_variant.html", {
                "form": form,
                "kind": self.kind,
                "variant": target,
            })

        src = form.cleaned_data["source_variant"]
        replace = form.cleaned_data["replace"]

        # ---- ACCESSORIES ----
        if self.kind == "accessories":
            if replace:
                models.VariantAccessory.objects.filter(variant=target).delete()
                objs = [
                    models.VariantAccessory(
                        variant=target,
                        accessory=a.accessory,
                        count=a.count,
                        price=a.price,
                        notes=a.notes,
                        local_produce=a.local_produce,
                    )
                    for a in src.accessories.all()
                ]
                created = models.VariantAccessory.objects.bulk_create(objs)
                resp = HttpResponse(status=204)
                return _msg_headers(resp, f"Скопировано аксессуаров: {len(created)}.", "success")

            # без replace — пропускаем дубликаты вручную
            existing_ids = set(
                models.VariantAccessory.objects
                .filter(variant=target)
                .values_list("accessory_id", flat=True)
            )
            to_create, skipped = [], 0
            for a in src.accessories.all():
                if a.accessory_id in existing_ids:
                    skipped += 1
                    continue
                to_create.append(models.VariantAccessory(
                    variant=target,
                    accessory=a.accessory,
                    count=a.count,
                    price=a.price,
                    notes=a.notes,
                    local_produce=a.local_produce,
                ))
            created = models.VariantAccessory.objects.bulk_create(to_create)
            created_n = len(created)

            if created_n == 0 and skipped > 0:
                # всё оказалось дубликатами
                resp = HttpResponse(status=409)
                return _msg_headers(resp, "Все выбранные аксессуары уже есть у варианта.", "danger")
            elif created_n > 0 and skipped > 0:
                resp = HttpResponse(status=204)
                return _msg_headers(resp, f"Добавлено: {created_n}. Пропущено как дубликаты: {skipped}.", "warning")
            else:
                resp = HttpResponse(status=204)
                return _msg_headers(resp, f"Скопировано аксессуаров: {created_n}.", "success")

        # ---- OPERATIONS ----
        elif self.kind == "operations":
            if replace:
                models.VariantOperation.objects.filter(variant=target).delete()
                objs = [
                    models.VariantOperation(
                        variant=target,
                        operation=o.operation,
                        price=o.price,
                        seconds=o.seconds,
                        notes=o.notes,
                    )
                    for o in src.operations.select_related("operation").all()
                ]
                created = models.VariantOperation.objects.bulk_create(objs)
                resp = HttpResponse(status=204)
                return _msg_headers(resp, f"Скопировано операций: {len(created)}.", "success")

            # без replace — пропускаем дубликаты вручную
            existing_ids = set(
                models.VariantOperation.objects
                .filter(variant=target)
                .values_list("operation_id", flat=True)
            )
            to_create, skipped = [], 0
            for o in src.operations.select_related("operation").all():
                if o.operation_id in existing_ids:
                    skipped += 1
                    continue
                to_create.append(models.VariantOperation(
                    variant=target,
                    operation=o.operation,
                    price=o.price,
                    seconds=o.seconds,
                    notes=o.notes,
                ))
            created = models.VariantOperation.objects.bulk_create(to_create)
            created_n = len(created)

            if created_n == 0 and skipped > 0:
                resp = HttpResponse(status=409)
                return _msg_headers(resp, "Все выбранные операции уже есть у варианта.", "danger")
            elif created_n > 0 and skipped > 0:
                resp = HttpResponse(status=204)
                return _msg_headers(resp, f"Добавлено: {created_n}. Пропущено как дубликаты: {skipped}.", "warning")
            else:
                resp = HttpResponse(status=204)
                return _msg_headers(resp, f"Скопировано операций: {created_n}.", "success")

        # ---- неизвестный kind ----
        return HttpResponse(status=400)
