from __future__ import annotations

from decimal import Decimal

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

DEC2 = Decimal("0.01")


def gm(app_label: str, model: str):
    try:
        return apps.get_model(app_label, model)
    except LookupError:
        return None


class Command(BaseCommand):
    help = "Создаёт по 20 тестовых объектов для моделей sewing (+минимальные зависимости из info/hr). Идемпотентно."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # sewing models
        SewingFabricType = gm("sewing", "SewingFabricType")
        SewingFabric = gm("sewing", "SewingFabric")
        TransferPrintPrice = gm("sewing", "TransferPrintPrice")
        SewingPackingPrice = gm("sewing", "SewingPackingPrice")
        SewingPart = gm("sewing", "SewingPart")
        SewingLine = gm("sewing", "SewingLine")
        CategoryModel = gm("sewing", "CategoryModel")
        SewingProductModel = gm("sewing", "SewingProductModel")
        ModelVariant = gm("sewing", "ModelVariant")
        VariantMaterial = gm("sewing", "VariantMaterial")
        VariantAccessory = gm("sewing", "VariantAccessory")
        VariantSize = gm("sewing", "VariantSize")
        VariantOperation = gm("sewing", "VariantOperation")

        # info models (внешние)
        Factory = gm("info", "Factory")
        UploadedImage = gm("info", "UploadedImage")
        WorkType = gm("info", "WorkType")
        Material = gm("info", "Material")
        MeasurementUnit = gm("info", "MeasurementUnit")
        Size = gm("info", "Size")
        Operation = gm("info", "Operation")

        # hr models (внешние)
        Department = gm("hr", "Department")
        Employee = gm("hr", "Employee")

        self.stdout.write(self.style.NOTICE("→ Подготовка минимальных зависимостей из info/hr…"))

        # === ensure helper ===
        def ensure_twenty(qs, make_one):
            count = qs.count()
            need = max(0, 20 - count)
            made = 0
            for i in range(count + 1, count + need + 1):
                make_one(i)
                made += 1
            return made

        created_total = 0

        # === Минимальные зависимости в info ===
        if MeasurementUnit and MeasurementUnit.objects.count() == 0:
            for i in range(1, 6 + 1):
                MeasurementUnit.objects.get_or_create(name=f"MU-{i}")

        if Material and Material.objects.count() == 0:
            mu = MeasurementUnit.objects.first()
            if not mu:
                mu = MeasurementUnit.objects.create(name="PCS")
            # создадим 20 универсальных материалов (для аксессуаров тоже)
            for i in range(1, 21):
                Material.objects.get_or_create(
                    code=f"MAT{i:04d}",
                    defaults=dict(
                        title=f"Material {i}",
                        m_unit=mu,
                        planned_cost=Decimal(100 + i),
                        stock_dec_places=2,
                        gramaj=i,
                    ),
                )

        if Size and Size.objects.count() == 0:
            for i in range(1, 21):
                Size.objects.get_or_create(name=f"Size {i}")

        if Operation and Operation.objects.count() == 0:
            # machine_type у вас nullable — создадим простые операции
            for i in range(1, 21):
                Operation.objects.get_or_create(
                    name=f"Operation {i}",
                    defaults=dict(default_price=10 + i, default_duration=(i % 7) * 10, is_active=True),
                )

        if WorkType and WorkType.objects.count() == 0:
            for i in range(1, 21):
                WorkType.objects.get_or_create(name=f"WorkType {i}")

        # === sewing: справочники ===
        if SewingFabricType:
            created_total += ensure_twenty(
                SewingFabricType.objects.all(),
                lambda i: SewingFabricType.objects.get_or_create(name=f"Тип полотна {i}"),
            )

        if SewingFabric:
            # нужно наличие типа
            ftypes = list(SewingFabricType.objects.all()[:20]) if SewingFabricType else []

            def make_fabric(i):
                kwargs = dict(name=f"Полотно {i}")
                if ftypes:
                    kwargs["fabric_type"] = ftypes[(i - 1) % len(ftypes)]
                SewingFabric.objects.get_or_create(name=kwargs["name"], defaults=kwargs)

            created_total += ensure_twenty(SewingFabric.objects.all(), make_fabric)

        if TransferPrintPrice:
            created_total += ensure_twenty(
                TransferPrintPrice.objects.all(),
                lambda i: TransferPrintPrice.objects.get_or_create(name=f"TTP-{i}", defaults={"price": 1000 + i * 5}),
            )

        if SewingPackingPrice:
            created_total += ensure_twenty(
                SewingPackingPrice.objects.all(),
                lambda i: SewingPackingPrice.objects.get_or_create(name=f"SPP-{i}", defaults={"price": 500 + i * 3}),
            )

        if SewingPart:
            created_total += ensure_twenty(
                SewingPart.objects.all(),
                lambda i: SewingPart.objects.get_or_create(name=f"Часть {i}"),
            )

        if CategoryModel:
            created_total += ensure_twenty(
                CategoryModel.objects.all(),
                lambda i: CategoryModel.objects.get_or_create(code=f"CAT{i:03d}",
                                                              defaults={"name": f"Категория {i}", "price": 100 + i}),
            )

        # === sewing: продуктовые сущности ===
        if SewingProductModel:
            imgs = list(UploadedImage.objects.all()[:20]) if UploadedImage else []
            cats = list(CategoryModel.objects.all()[:20]) if CategoryModel else []

            def make_spm(i):
                defaults = dict(
                    name=f"Модель {i}",
                    season="SS",
                    discount=Decimal("0.00"),
                    cutting_price=Decimal(10 + i),
                    transfer_price=Decimal(5 + i),
                    print_price=Decimal(2 + i),
                    embroidery_price=Decimal(1 + i),
                    sewing_loss_percent=Decimal("2.50"),
                    other_expenses_percent=Decimal("1.50"),
                    profitability=Decimal("10.00"),
                    commission=Decimal("3.00"),
                )
                if imgs: defaults["image"] = imgs[(i - 1) % len(imgs)]
                if cats: defaults["category"] = cats[(i - 1) % len(cats)]
                SewingProductModel.objects.get_or_create(vendor_code=f"ART{i:04d}", defaults=defaults)

            created_total += ensure_twenty(SewingProductModel.objects.all(), make_spm)

        if ModelVariant:
            spms = list(SewingProductModel.objects.all()[:40])
            wts = list(WorkType.objects.all()[:20]) if WorkType else []
            kinds = [ModelVariant.VariantKind.MARKETING, ModelVariant.VariantKind.SAMPLE,
                     ModelVariant.VariantKind.PLANNED]

            def make_variant(i):
                if not spms:
                    return
                defaults = dict(
                    kind=kinds[(i - 1) % len(kinds)],
                    loss=Decimal("0.00"),
                    design_code=f"D{i:04d}",
                    cloned=(i % 7 == 0),
                    description=f"Описание варианта {i}",
                    work_type=(wts[(i - 1) % len(wts)] if wts else None),
                )
                ModelVariant.objects.get_or_create(
                    product_model=spms[(i - 1) % len(spms)],
                    name=f"Вариант {i}",
                    defaults=defaults,
                )

            created_total += ensure_twenty(ModelVariant.objects.all(), make_variant)

        # === sewing: Variant* (20 штук в каждой таблице) ===
        variants = list(ModelVariant.objects.all()[:40]) if ModelVariant else []
        materials = list(Material.objects.all()[:40]) if Material else []
        sizes = list(Size.objects.all()[:40]) if Size else []
        operations = list(Operation.objects.all()[:40]) if Operation else []
        parts = list(SewingPart.objects.all()[:20]) if SewingPart else []

        if VariantMaterial and variants and materials:
            def make_vm(i):
                var = variants[(i - 1) % len(variants)]
                mat = materials[(i - 1) % len(materials)]
                obj, _ = VariantMaterial.objects.get_or_create(
                    variant=var, material=mat,
                    defaults=dict(
                        count=Decimal("0.250"),
                        price=Decimal(5 + i),
                        loss=Decimal("1.50"),
                        width=Decimal("1.00"),
                        height=Decimal("1.00"),
                        density=Decimal("0.00"),
                        main=(i % 5 == 0),
                        notes=f"Материал {i}",
                    ),
                )
                # M2M used_parts (1–3 части если есть)
                if parts:
                    idx = (i - 1) % len(parts)
                    chunk = parts[idx: idx + min(3, len(parts))]
                    obj.used_parts.add(*chunk)

            created_total += ensure_twenty(VariantMaterial.objects.all(), make_vm)

        if VariantAccessory and variants and materials:
            def make_va(i):
                var = variants[(i - 1) % len(variants)]
                acc = materials[(i * 3 - 1) % len(materials)]
                VariantAccessory.objects.get_or_create(
                    variant=var, accessory=acc,
                    defaults=dict(
                        count=Decimal("1.000"),
                        price=Decimal(1 + i),
                        local_produce=(i % 2 == 0),
                        notes=f"Аксессуар {i}",
                    ),
                )

            created_total += ensure_twenty(VariantAccessory.objects.all(), make_va)

        if VariantSize and variants and sizes:
            # Уникальность (variant, size) соблюдаем, распределяя разные размеры
            def make_vs(i):
                var = variants[(i - 1) % len(variants)]
                sz = sizes[(i - 1) % len(sizes)]
                VariantSize.objects.get_or_create(variant=var, size=sz, defaults={"notes": f"Размер {i}"})

            created_total += ensure_twenty(VariantSize.objects.all(), make_vs)

        if VariantOperation and variants and operations:
            def make_vo(i):
                var = variants[(i - 1) % len(variants)]
                op = operations[(i - 1) % len(operations)]
                VariantOperation.objects.get_or_create(
                    variant=var, operation=op,
                    defaults=dict(seconds=(i % 7) * 10, price=Decimal(0 + i), notes=f"Операция {i}"),
                )

            created_total += ensure_twenty(VariantOperation.objects.all(), make_vo)

        # === sewing: SewingLine (если есть Factory и Department) ===
        if SewingLine:
            if not Factory or Factory.objects.count() == 0 or not Department or Department.objects.count() == 0:
                self.stdout.write(self.style.WARNING(
                    "⚠ Пропускаю SewingLine: нет Factory или Department (info/hr)."
                ))
            else:
                factories = list(Factory.objects.all()[:20])
                deps = list(Department.objects.all()[:20])
                masters = list(Employee.objects.all()[:20]) if Employee else []

                def make_line(i):
                    SewingLine.objects.get_or_create(
                        name=f"Линия {i}",
                        factory=factories[(i - 1) % len(factories)],
                        department=deps[(i - 1) % len(deps)],
                        defaults=dict(
                            master=(masters[(i - 1) % len(masters)] if masters else None),
                            worker_count=25 + (i % 6),
                            ordering=i,
                            status=True,
                        ),
                    )

                created_total += ensure_twenty(SewingLine.objects.all(), make_line)

        # === Пересчитать unit_price у вариантов после добавления материалов/аксессуаров ===
        if ModelVariant:
            for v in ModelVariant.objects.all():
                v.unit_price = v.recalc_price()
                v.save(update_fields=["unit_price"])

        self.stdout.write(self.style.SUCCESS(f"Готово! Создано/дозаполнено ~{created_total} объектов."))
