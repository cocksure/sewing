# <app>/management/commands/seed_test_data.py
from __future__ import annotations

from datetime import date
from typing import List

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
# Вверху файла:
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.timezone import now
MIN_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc``\x00"
    b"\x00\x00\x02\x00\x01E\x9c\xbb\x7f\x00\x00\x00\x00IEND\xaeB`\x82"
)

today = now()
DIR_PREFIX = f"seed/{today.year}/{today.month:02d}"


class Command(BaseCommand):
    help = "Создаёт по 20 тестовых объектов для каждой модели приложения (идемпотентно)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            dest="app_label",
            default=None,
            help="App label, где находятся модели (например: info, sewing и т.п.). "
                 "Если не указать, будет попытка autodiscover по одной из моделей.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        app_label = options.get("app_label")

        # Если app не передали, попробуем угадать из наиболее характерной модели.
        if not app_label:
            candidates = [
                "info", "sewing", "core", "materials", "tmsmodels",
            ]
            for c in candidates:
                try:
                    apps.get_app_config(c)
                    app_label = c
                    break
                except LookupError:
                    continue
            if not app_label:
                raise CommandError(
                    "Нужно указать --app <app_label>, например: --app info"
                )

        # Быстрый резолвер моделей по имени
        def M(name: str):
            return apps.get_model(app_label, name)

        # ---- Получаем классы моделей (если каких-то нет в этом app — пропускаем) ----
        def maybe(name):
            try:
                return M(name)
            except LookupError:
                return None

        UploadedImage = maybe("UploadedImage")
        UploadedFile = maybe("UploadedFile")
        Role = maybe("Role")
        ProductType = maybe("ProductType")
        Firm = maybe("Firm")
        ProcessRole = maybe("ProcessRole")
        Specification = maybe("Specification")
        Factory = maybe("Factory")
        Process = maybe("Process")
        WorkType = maybe("WorkType")
        MaterialGroup = maybe("MaterialGroup")
        MeasurementUnit = maybe("MeasurementUnit")
        PriceCategory = maybe("PriceCategory")
        MaterialGroupCategory = maybe("MaterialGroupCategory")
        MaterialSpecialGroup = maybe("MaterialSpecialGroup")
        ColorGroup = maybe("ColorGroup")
        RecipeType = maybe("RecipeType")
        RecipeGroup = maybe("RecipeGroup")
        TypeOrderColor = maybe("TypeOrderColor")
        ColorGraphic = maybe("ColorGraphic")
        Material = maybe("Material")
        SubMaterial = maybe("SubMaterial")
        Color = maybe("Color")
        RawMaterial = maybe("RawMaterial")
        SewingMachineType = maybe("SewingMachineType")
        Operation = maybe("Operation")
        Size = maybe("Size")

        self.stdout.write(self.style.NOTICE(f"App: {app_label} — начинаем наполнение…"))

        # ------- Вспомогательный хелпер: создать недостающее до 20 -------
        def ensure_twenty(qs, make_one):
            """
            qs: QuerySet модели
            make_one: функция f(idx: int) -> obj, создаёт i-й объект (1..N)
            """
            cnt = qs.count()
            need = max(0, 20 - cnt)
            created = 0
            for i in range(cnt + 1, cnt + need + 1):
                make_one(i)
                created += 1
            return created

        created_total = 0

        # ====== 1) Примитивные/справочные ======
        if MeasurementUnit:
            created_total += ensure_twenty(
                MeasurementUnit.objects.all(),
                lambda i: MeasurementUnit.objects.get_or_create(name=f"MU-{i}"),
            )

        if ProductType:
            created_total += ensure_twenty(
                ProductType.objects.all(),
                lambda i: ProductType.objects.get_or_create(name=f"ProductType {i}"),
            )

        if Role:
            created_total += ensure_twenty(
                Role.objects.all(),
                lambda i: Role.objects.get_or_create(
                    name=f"Role {i}", defaults={"is_master": (i % 5 == 0)}
                ),
            )

        if MaterialGroup:
            created_total += ensure_twenty(
                MaterialGroup.objects.all(),
                lambda i: MaterialGroup.objects.get_or_create(
                    code=f"MG{i:03d}",
                    defaults={"name": f"Material Group {i}"},
                ),
            )

        if MaterialSpecialGroup:
            created_total += ensure_twenty(
                MaterialSpecialGroup.objects.all(),
                lambda i: MaterialSpecialGroup.objects.get_or_create(name=f"Special Group {i}"),
            )

        if ColorGroup:
            created_total += ensure_twenty(
                ColorGroup.objects.all(),
                lambda i: ColorGroup.objects.get_or_create(
                    code=f"CG{i:03d}",
                    defaults={"name": f"Color Group {i}", "last_color_code": f"L{i:03d}"},
                ),
            )

        if RecipeType:
            created_total += ensure_twenty(
                RecipeType.objects.all(),
                lambda i: RecipeType.objects.get_or_create(
                    name=f"Recipe Type {i}", defaults={"code": f"R{i:02d}"}
                ),
            )

        if RecipeGroup:
            created_total += ensure_twenty(
                RecipeGroup.objects.all(),
                lambda i: RecipeGroup.objects.get_or_create(name=f"Recipe Group {i}"),
            )

        if TypeOrderColor:
            created_total += ensure_twenty(
                TypeOrderColor.objects.all(),
                lambda i: TypeOrderColor.objects.get_or_create(
                    name=f"Order Type {i}", defaults={"code": f"T{i:02d}"}
                ),
            )

        if ColorGraphic:
            created_total += ensure_twenty(
                ColorGraphic.objects.all(),
                lambda i: ColorGraphic.objects.get_or_create(
                    code=f"GR{i:03d}", defaults={"name": f"Graphic {i}"}
                ),
            )

        if Factory:
            created_total += ensure_twenty(
                Factory.objects.all(),
                lambda i: Factory.objects.get_or_create(
                    name=f"Factory {i}", defaults={"official_name": f"Factory {i} LLC"}
                ),
            )

        # ====== 2) Файлы/картинки ======
        # ====== 2) Файлы/картинки ======
        if UploadedImage:
            # создаём РЕАЛЬНЫЕ файлы через storage; папки создадутся автоматически
            cnt = UploadedImage.objects.count()
            need = max(0, 20 - cnt)
            for i in range(cnt + 1, cnt + need + 1):
                fname = f"{DIR_PREFIX}/img_{i}.png"
                path = default_storage.save(fname, ContentFile(MIN_PNG))
                UploadedImage.objects.create(image=path)

        if UploadedFile:
            cnt = UploadedFile.objects.count()
            need = max(0, 20 - cnt)
            for i in range(cnt + 1, cnt + need + 1):
                fname = f"{DIR_PREFIX}/file_{i}.txt"
                path = default_storage.save(fname, ContentFile(b"seed test file"))
                UploadedFile.objects.create(file=path)
        # ====== 3) Цены и связанные ======
        if PriceCategory:
            created_total += ensure_twenty(
                PriceCategory.objects.all(),
                lambda i: PriceCategory.objects.get_or_create(
                    name=f"Price Cat {i}",
                    defaults={
                        "price": 1000 + i * 10,
                        "m_unit": MeasurementUnit.objects.order_by("id").first() if MeasurementUnit else None,
                    },
                ),
            )

        if MaterialGroupCategory and MaterialGroup and PriceCategory:
            # Свяжем первых 20 групп с первыми 20 категорий
            mgs: List = list(MaterialGroup.objects.order_by("id")[:20])
            pcs: List = list(PriceCategory.objects.order_by("id")[:20])
            for i in range(min(20, len(mgs), len(pcs))):
                mg = mgs[i]
                pc = pcs[i]
                MaterialGroupCategory.objects.get_or_create(
                    material_group=mg, defaults={"category": pc}
                )
            # Не учитываем в счётчик created_total, т.к. число зависит от наличия пар

        # ====== 4) Фирмы, спецификации ======
        if Firm:
            created_total += ensure_twenty(
                Firm.objects.all(),
                lambda i: Firm.objects.get_or_create(
                    code=f"FIRM{i:04d}",
                    defaults={"name": f"Firm {i}", "type": "customer", "status": 1},
                ),
            )

        if Specification:
            created_total += ensure_twenty(
                Specification.objects.all(),
                lambda i: Specification.objects.get_or_create(
                    name=f"Spec {i}",
                    defaults={"firm": Firm.objects.order_by("id").first() if Firm else None},
                ),
            )

        # ====== 5) Цвета ======
        if Color:
            cg = ColorGroup.objects.order_by("id") if ColorGroup else []
            fm = Firm.objects.order_by("id") if Firm else []
            rt = RecipeType.objects.order_by("id") if RecipeType else []
            rg = RecipeGroup.objects.order_by("id") if RecipeGroup else []
            toc = TypeOrderColor.objects.order_by("id") if TypeOrderColor else []
            gr = ColorGraphic.objects.order_by("id") if ColorGraphic else []

            def make_color(i):
                kwargs = {
                    "name": f"Color {i}",
                    "code": f"C{i:04d}",
                    "input_date": date.today(),
                }
                if cg: kwargs["group"] = cg[(i - 1) % len(cg)]
                if fm: kwargs["firm"] = fm[(i - 1) % len(fm)]
                if rt: kwargs["recipe_type"] = rt[(i - 1) % len(rt)]
                if rg: kwargs["recipe_group"] = rg[(i - 1) % len(rg)]
                if toc: kwargs["type_order"] = toc[(i - 1) % len(toc)]
                if gr: kwargs["graphic"] = gr[(i - 1) % len(gr)]
                Color.objects.get_or_create(code=kwargs["code"], defaults=kwargs)

            created_total += ensure_twenty(Color.objects.all(), make_color)

        # ====== 6) Материалы и субматериалы ======
        if Material:
            mus = list(MeasurementUnit.objects.order_by("id")[:20]) if MeasurementUnit else [None]
            mgs = list(MaterialGroup.objects.order_by("id")[:20]) if MaterialGroup else [None]

            def make_material(i):
                Material.objects.get_or_create(
                    code=f"MAT{i:04d}",
                    defaults={
                        "title": f"Material {i}",
                        "m_unit": mus[(i - 1) % len(mus)],
                        "group": mgs[(i - 1) % len(mgs)] if mgs[0] else None,
                        "planned_cost": float(100 + i),
                        "stock_dec_places": 2,
                        "gramaj": float(i),
                    },
                )

            created_total += ensure_twenty(Material.objects.all(), make_material)

        if SubMaterial and Material:
            mats = list(Material.objects.order_by("id")[:40])  # побольше для связок
            for i in range(min(20, max(0, len(mats) - 1))):
                m1 = mats[i]
                m2 = mats[(i + 1) % len(mats)]
                if m1.pk == m2.pk:
                    continue
                SubMaterial.objects.get_or_create(
                    material=m1, sub_material=m2, defaults={"percent": float(((i % 5) + 1) * 10)}
                )

        # ====== 7) Машины и операции ======
        if SewingMachineType:
            created_total += ensure_twenty(
                SewingMachineType.objects.all(),
                lambda i: SewingMachineType.objects.get_or_create(name=f"Machine Type {i}"),
            )

        if Operation:
            mts = list(SewingMachineType.objects.order_by("id")[:20]) if SewingMachineType else [None]

            def make_operation(i):
                Operation.objects.get_or_create(
                    name=f"Operation {i}",
                    defaults={
                        "default_price": 10 + i,
                        "default_duration": (i % 7) * 10,
                        "is_active": True,
                        "machine_type": mts[(i - 1) % len(mts)] if mts[0] else None,
                    },
                )

            created_total += ensure_twenty(Operation.objects.all(), make_operation)

        # ====== 8) Размеры ======
        if Size:
            created_total += ensure_twenty(
                Size.objects.all(),
                lambda i: Size.objects.get_or_create(name=f"Size {i}"),
            )

        # ====== 9) Сырьё ======
        if RawMaterial and ProductType:
            pts = list(ProductType.objects.order_by("id")[:20])

            def make_raw(i):
                RawMaterial.objects.get_or_create(
                    name=f"Raw {i}",
                    defaults={"price": float(50 + i), "product_type": pts[(i - 1) % len(pts)] if pts else None},
                )

            created_total += ensure_twenty(RawMaterial.objects.all(), make_raw)

        # ====== 10) Процессы / WorkType / ProcessRole ======
        if Process:
            pts = list(ProductType.objects.order_by("id")[:20]) if ProductType else [None]

            def make_process(i):
                Process.objects.get_or_create(
                    name=f"Process {i}",
                    defaults={
                        "order": i,
                        "is_parallel": (i % 3 == 0),
                        "product_type": pts[(i - 1) % len(pts)] if pts[0] else None,
                        "is_record_keeped": True,
                    },
                )

            created_total += ensure_twenty(Process.objects.all(), make_process)

        if WorkType:
            pts = list(ProductType.objects.order_by("id")[:20]) if ProductType else [None]
            created_total += ensure_twenty(
                WorkType.objects.all(),
                lambda i: WorkType.objects.get_or_create(
                    name=f"WorkType {i}",
                    defaults={"product_type": pts[(i - 1) % len(pts)] if pts[0] else None},
                ),
            )
            # Привяжем по 1–3 процесса к каждому WorkType
            procs = list(Process.objects.order_by("id")[:60]) if Process else []
            if procs:
                for idx, wt in enumerate(WorkType.objects.order_by("id")):
                    start = (idx * 3) % len(procs)
                    wt.processes.add(*procs[start:start + 3])

        if ProcessRole and Process and Role:
            procs = list(Process.objects.order_by("id")[:20])
            roles = list(Role.objects.order_by("id")[:20])
            for i in range(min(20, len(procs), len(roles))):
                ProcessRole.objects.get_or_create(
                    process=procs[i],
                    role=roles[i % len(roles)],
                    defaults={
                        "individual": (i % 4 == 0),
                        "salary_percent": float((i % 5) * 5),
                        "salary_group": (i % 3) + 1,
                        "work_in_machine": (i % 2 == 0),
                        "work_in_max_machine": 1 + (i % 3),
                    },
                )

        self.stdout.write(self.style.SUCCESS(f"Готово! Создано/дозаполнено ~{created_total} объектов."))
