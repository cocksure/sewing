from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.db.models import Sum, F
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from hr.models import Employee, Department
from info.models import UploadedImage, WorkType, Material

DESIGN_GROUPS = (
    (1, _('Натуральный')),
    (2, _('Геометрический')),
    (3, _('Маленькие цвета'))
)

PRINT_TYPES = (
    (1, _('Пигмент')),
    (2, _('Реактив')),
    (3, _('Вытравка')),
    (4, _('Матвайс')),
    (5, _('Рельефный')),
    (6, _('Выжигание')),
    (7, _('Глиттер')),
)

DRAW_TYPES = (
    (1, _('Ручное')),
    (2, _('Авто'))
)

PRINT_RATIOS = (
    (1, _('0-30%')),
    (2, _('31-60%')),
    (3, _('61-80%')),
    (4, _('81-100%'))
)


class OrderStatus(models.IntegerChoices):
    NEW = 1, _("Новый")
    IN_PROGRESS = 3, _("В работе")
    DONE = 4, _("Готов")
    CANCELED = 5, _("Отменён")
    IN_DEVELOPMENT = 6, _("В разработке")
    IN_AGGREEMENT = 7, _("На согласовании")
    CONFIRMED = 8, _("Подтверждён")
    ABORTED = 9, _("Прерван")
    ACCEPTED = 10, _("Принят")


class SewingFabricType(models.Model):
    name = models.CharField(_('Тип полотна'), max_length=128)

    class Meta:
        managed = True
        db_table = 'sewing_fabric_type'
        verbose_name = _('Тип полотна')
        verbose_name_plural = _('Типы полотна')

    def __str__(self):
        return self.name


class SewingFabric(models.Model):
    name = models.CharField(_('Полотно'), max_length=128)
    fabric_type = models.ForeignKey(SewingFabricType, verbose_name=_('Тип полотна'), on_delete=models.PROTECT)

    class Meta:
        managed = True
        db_table = 'sewing_fabric'
        verbose_name = _('Полотно')
        verbose_name_plural = _('Полотна')

    def __str__(self):
        return '{0} - {1}'.format(self.fabric_type.name, self.name)


class TransferPrintPrice(models.Model):
    class Meta:
        verbose_name = _('Цена трансферной печати')
        verbose_name_plural = _('Цены трансферной печати')

    name = models.CharField(_('Наименования'), max_length=32)
    price = models.PositiveIntegerField(_('Цена'))

    def __str__(self) -> str:
        return str(self.name)


class SewingPackingPrice(models.Model):
    class Meta:
        verbose_name = _('Цена упаковка одежда')
        verbose_name_plural = _('Цены упаковка одежди')

    name = models.CharField(_('Наименования'), max_length=32)
    price = models.PositiveIntegerField(_('Цена'))

    def __str__(self) -> str:
        return str(self.name)


class SewingPart(models.Model):
    name = models.CharField(_('Названия части'), max_length=128)

    class Meta:
        managed = True
        db_table = 'sewing_parts'
        verbose_name = _('Часть одежды')
        verbose_name_plural = _('Части одежды')

    def __str__(self):
        return self.name


class SewingLine(models.Model):
    name = models.CharField(_('Линия'), max_length=128)
    factory = models.ForeignKey('info.Factory', on_delete=models.PROTECT, verbose_name=_('Фабрика'),
                                related_name='sewing_lines')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name=_('Отдел'),
                                   related_name='sewing_lines')
    master = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name=_('Мастер'), null=True, blank=True)
    worker_count = models.IntegerField(_('Вмесимость работников'), default=25)
    ordering = models.IntegerField(_('По очереди'), default=0)
    status = models.BooleanField(_('Статус'), default=True)

    @property
    def fact_worker_count(self):
        return self.employees.all().count()

    class Meta:
        db_table = 'sewing_lines'
        verbose_name = _('Линия швейки')
        verbose_name_plural = _('Линии швейки')

    def __str__(self):
        return '{0}-{1}'.format(self.factory.name, self.name)


class CategoryModel(models.Model):
    code = models.CharField(_('Код'), max_length=32)
    name = models.CharField(_('Наименование'), max_length=32)
    price = models.FloatField(_('Цена'), default=0, null=True)

    class Meta:
        db_table = 'category_model'
        verbose_name = _('Категория модель')
        verbose_name_plural = _('Категории моделы')

    def __str__(self):
        return self.name


# --------------------------------------------- SewingModels Start ----------------------------------------------------

DEC2 = Decimal("0.01")


def D(x) -> Decimal:
    if x is None:
        return Decimal("0")
    return x if isinstance(x, Decimal) else Decimal(str(x))


class SewingProductModel(BaseModel):
    name = models.CharField(_("Наименование модели"), max_length=128)
    vendor_code = models.CharField(_("Артикул"), max_length=128)
    season = models.CharField(_("Сезон"), max_length=32, default="", blank=True)
    # firm = models.ForeignKey('info.Firm', on_delete=models.PROTECT, verbose_name=_('Заказчик'),
    #                          default=None, null=True, blank=True)

    # Цены/проценты → DecimalField
    discount = models.DecimalField(_("Скидка, %"), max_digits=5, decimal_places=2, default=0)
    cutting_price = models.DecimalField(_("Крой"), max_digits=12, decimal_places=2, default=0)
    transfer_price = models.DecimalField(_("Трансфер"), max_digits=12, decimal_places=2, default=0)
    print_price = models.DecimalField(_("Печать"), max_digits=12, decimal_places=2, default=0)
    embroidery_price = models.DecimalField(_("Вышивка"), max_digits=12, decimal_places=2, default=0)
    sewing_loss_percent = models.DecimalField(_("Потеря швейки, %"), max_digits=5, decimal_places=2, default=0)
    other_expenses_percent = models.DecimalField(_("Прочие расходы, %"), max_digits=5, decimal_places=2, default=0)
    profitability = models.DecimalField(_("Рентабельность, %"), max_digits=5, decimal_places=2, default=0)
    commission = models.DecimalField(_("Комиссия, %"), max_digits=5, decimal_places=2, default=0)

    category = models.ForeignKey(CategoryModel, on_delete=models.PROTECT, verbose_name=_("Категория"),
                                 null=True, blank=True, related_name="product_model")
    image = models.ForeignKey(UploadedImage, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = "sewing_product_model"
        verbose_name = _("Модель одежды")
        verbose_name_plural = _("Модели одежды")

    def __str__(self):
        return self.vendor_code


class ModelVariant(BaseModel):
    class VariantKind(models.TextChoices):
        MARKETING = "marketing", _("Маркетинг")
        SAMPLE = "sample", _("Образец")
        PLANNED = "planned", _("Плановый")

    kind = models.CharField(_("Тип варианта"), max_length=16, choices=VariantKind.choices,
                            default=VariantKind.MARKETING, db_index=True)
    name = models.CharField(_("Названия"), max_length=128)
    product_model = models.ForeignKey(SewingProductModel, on_delete=models.CASCADE, related_name="variants")
    loss = models.DecimalField(_("Угар, %"), max_digits=5, decimal_places=2, default=0)
    work_type = models.ForeignKey(WorkType, verbose_name=_("Вид работы"),
                                  on_delete=models.PROTECT, null=True, blank=True, related_name="model_variants")
    design_code = models.CharField(_("Код дизайна"), max_length=128, blank=True, null=True)
    cloned = models.BooleanField(_("Клон"), default=False)
    description = models.CharField(_("Подробно"), max_length=256, blank=True, null=True)

    unit_price = models.DecimalField(_("Цена за изделие"), max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "variants"
        verbose_name = _("Вариант модели")
        verbose_name_plural = _("Варианты модели")

    def __str__(self):
        return f"{self.product_model.vendor_code} : {self.name} - {self.description}"

    @property
    def has_sizes_and_ops(self):
        return self.kind in {self.VariantKind.SAMPLE, self.VariantKind.PLANNED}

        # --- новые маленькие хелперы ---

    def _materials_cost(self) -> Decimal:
        """
        Сумма по материалам:
          total += (цена_за_единицу * количество_на_изделие * (1 + потеря%))
        """
        if not self.pk:
            return D("0")

        total = D("0")
        for m in self.materials.all():
            price_per_unit = D(m.price or 0)  # цена за 1 ед. (у тебя сейчас "за 1 кг")
            qty_per_item = D(m.count or 0)  # количество на изделие (в тех же единицах)
            loss_frac = D(m.loss or 0) / D("100")
            total += price_per_unit * qty_per_item * (D("1") + loss_frac)
        return total

    def _accessories_cost(self) -> Decimal:
        """
        Сумма по аксессуарам:
          total += (цена_за_единицу * количество_на_изделие)
        """
        if not self.pk:
            return D("0")

        total = D("0")
        for a in self.accessories.all():
            price_per_item = D(a.price or 0)
            qty_per_item = D(a.count or 0)
            total += price_per_item * qty_per_item
        return total

    def recalc_price(self) -> Decimal:
        spm = self.product_model
        # 1) Считаем реальную «себестоимость» варианта
        base = D("0")
        base += self._materials_cost()
        base += self._accessories_cost()

        # 2) Базовые составляющие из модели
        base += D(spm.cutting_price or 0)
        base += D(spm.transfer_price or 0)
        base += D(spm.print_price or 0)
        base += D(spm.embroidery_price or 0)

        # 3) Накрутки и скидка
        def pct(p):
            return base * (D(p or 0) / D("100"))

        total = base
        total += pct(spm.sewing_loss_percent)  # потери пошива
        total += pct(spm.other_expenses_percent)  # прочие расходы
        total += pct(spm.profitability)  # рентабельность
        total += pct(spm.commission)  # комиссия

        # скидка в %
        total -= total * (D(spm.discount or 0) / D("100"))

        return total.quantize(DEC2, rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        # автоподстановка имени для образца при создании
        is_create = self.pk is None
        if is_create and self.kind == self.VariantKind.SAMPLE and not (self.name or "").strip():
            self.name = "Образец"

        # если сохраняют только unit_price — не пересчитываем
        update_fields = kwargs.get("update_fields")
        if update_fields and set(update_fields) <= {"unit_price"}:
            return super().save(*args, **kwargs)

        # обычный путь: сохраняем, потом пересчитываем и обновляем единичным UPDATE
        super().save(*args, **kwargs)
        new_price = self.recalc_price()
        if new_price != self.unit_price:
            type(self).objects.filter(pk=self.pk).update(unit_price=new_price)
            self.unit_price = new_price


class VariantMaterial(BaseModel):
    variant = models.ForeignKey(ModelVariant, on_delete=models.CASCADE, related_name="materials",
                                verbose_name=_("Вариант"))
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name=_("Материал"),
                                 related_name="sewing_variants")
    count = models.DecimalField(_("Количество"), max_digits=12, decimal_places=3)  # вес/кол-во на изделие
    color = models.ForeignKey("info.Color", verbose_name=_("Цвет"), on_delete=models.PROTECT, null=True, blank=True)
    packing_type = models.PositiveSmallIntegerField(_("Вид упаковки"),
                                                    choices=((1, "Рулон"), (2, "Пачка"), (3, "Раскрытий")),
                                                    blank=True, null=True)
    width = models.DecimalField(_("Ширина"), max_digits=8, decimal_places=2, default=0)
    height = models.DecimalField(_("Высота"), max_digits=8, decimal_places=2, default=0)
    density = models.DecimalField(_("Плотность"), max_digits=8, decimal_places=2, default=0)
    loss = models.DecimalField(_("Потеря Материала, %"), max_digits=5, decimal_places=2, default=0)
    used_parts = models.ManyToManyField("sewing.SewingPart", verbose_name=_("Использованные части"), blank=True)
    price = models.DecimalField(_("Цена (за 1 кг)"), max_digits=12, decimal_places=2, default=0)
    main = models.BooleanField(_("Основной"), default=False)
    notes = models.CharField(_("Примечание"), max_length=512, blank=True, null=True, default="")

    class Meta:
        db_table = "sewing_variant_materials"
        verbose_name = _("Материал варианта")
        verbose_name_plural = _("Материалы варианта")

    def __str__(self):
        return f"{self.variant.product_model.vendor_code} - {self.variant.name} - {self.material.title}"


class VariantAccessory(BaseModel):
    variant = models.ForeignKey(ModelVariant, on_delete=models.CASCADE, related_name="accessories",
                                verbose_name=_("Вариант"))
    accessory = models.ForeignKey("info.Material", on_delete=models.CASCADE, verbose_name=_("Аксессуар"),
                                  related_name="variant_accessories")
    count = models.DecimalField(_("Количество"), max_digits=12, decimal_places=3)
    price = models.DecimalField(_("Цена (за изделие)"), max_digits=12, decimal_places=2, default=0)
    local_produce = models.BooleanField(_("Производство"), default=False)
    notes = models.CharField(_("Примечание"), max_length=512, blank=True, default="")

    class Meta:
        db_table = "sewing_variant_accessories"
        verbose_name = _("Аксессуар варианта")
        verbose_name_plural = _("Аксессуары варианта")

    def __str__(self):
        return f"{self.accessory.title} — {self.count}"


class VariantSize(BaseModel):
    variant = models.ForeignKey('ModelVariant', on_delete=models.CASCADE,
                                related_name="sizes", verbose_name=_("Вариант"))
    size = models.ForeignKey('info.Size', on_delete=models.PROTECT, verbose_name=_("Размер"))

    notes = models.CharField(_("Примечание"), max_length=255, blank=True, null=True)

    class Meta:
        db_table = "sewing_variant_sizes"
        verbose_name = _("Размер варианта")
        verbose_name_plural = _("Размеры варианта")
        constraints = [
            UniqueConstraint(fields=["variant", "size"], name="uniq_size_per_variant")
        ]

    def __str__(self):
        return f"{self.variant} — {self.size}"


class VariantOperation(BaseModel):
    variant = models.ForeignKey('ModelVariant', on_delete=models.CASCADE,
                                related_name='operations', verbose_name=_('Вариант'))
    operation = models.ForeignKey('info.Operation', on_delete=models.PROTECT, verbose_name=_('Операция'))
    seconds = models.PositiveIntegerField(_('Расход времени'), default=0)
    price = models.DecimalField(_("Цена за операцию"), max_digits=10, decimal_places=2, default=0, blank=True)
    notes = models.CharField(_("Примечание"), max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'sewing_variant_operation'
        verbose_name = _('Операция варианта')
        verbose_name_plural = _('Операции варианта')
        constraints = [
            UniqueConstraint(fields=["variant", "operation"], name="uniq_operation_per_variant")
        ]

    def __str__(self):
        return f"{self.variant} — {self.operation}"


# --------------------------------------------- SewingOrders Start ----------------------------------------------------


class SewingOrder(BaseModel):
    class OrderType(models.TextChoices):
        SAMPLE = "sample", _("Образец")
        PRODUCTION = "production", _("Производство")
        MARKETING = "marketing", _("Маркетинг")
        OTHER = "other", _("Другое")

    # номер можно будет добавить позже, если нужен
    customer = models.ForeignKey(
        'info.Firm', verbose_name=_("Заказчик"),
        on_delete=models.PROTECT, related_name="sewing_orders_customer",
    )
    buyer = models.ForeignKey(
        'info.Firm', verbose_name=_("Покупатель"),
        on_delete=models.PROTECT, related_name="sewing_orders_buyer",
        null=True, blank=True,
    )
    shipment_date = models.DateField(_("Дата отгрузки"), null=True, blank=True)
    order_type = models.CharField(
        _("Тип заказа"), max_length=20, choices=OrderType.choices, default=OrderType.PRODUCTION
    )
    specification = models.ForeignKey(
        'info.Specification', verbose_name=_("Спецификация"),
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sewing_orders",
    )

    status = models.IntegerField(
        _("Статус"),
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
        db_index=True,
    )

    total_qty = models.PositiveIntegerField(_("Итого кол-во"), default=0)
    total_amount = models.DecimalField(
        _("Итого сумма"), max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        verbose_name = _("Швейный заказ")
        verbose_name_plural = _("Швейные заказы")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status",)),
            models.Index(fields=("shipment_date",)),
            models.Index(fields=("order_type",)),
            models.Index(fields=("customer",)),
            models.Index(fields=("created_at",)),
        ]

    @property
    def order_date(self):
        # дата создания как дата заказа
        return getattr(self, "created_at", None).date() if getattr(self, "created_at", None) else None

    @property
    def manager(self):
        # кто создал заказ
        return getattr(self, "created_by", None)

    def __str__(self):
        return f"Заказ #{self.pk or '—'} от {self.customer}"

    # пересчёт итогов из позиций
    def recompute_totals(self, save=True):
        agg = self.items.aggregate(
            qty=Sum("quantity"),
            amt=Sum(F("quantity") * F("unit_price")),
        )
        self.total_qty = agg.get("qty") or 0
        self.total_amount = agg.get("amt") or Decimal("0.00")
        if save:
            super().save(update_fields=("total_qty", "total_amount", "updated_at"))

    # легкий guard: не даём пересохранять заказ с отрицательными итогами
    def clean(self):
        super().clean()
        if self.total_qty < 0 or self.total_amount < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("Итоги заказа не могут быть отрицательными."))


class SewingOrderItem(models.Model):
    order = models.ForeignKey(SewingOrder, verbose_name=_("Заказ"),
                              on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ModelVariant, verbose_name=_("Вариант модели"),
                                on_delete=models.PROTECT, related_name="order_items")

    quantity = models.PositiveIntegerField(_("Кол-во"), default=1)
    unit_price = models.DecimalField(_("Цена за единицу"),
                                     max_digits=12, decimal_places=2, default=Decimal("0.00"))

    # статус позиции (часто удобно иметь свой, но можно наследовать от заказа)
    status = models.IntegerField(
        _("Статус позиции"),
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
        db_index=True,
    )

    notes = models.CharField(_("Примечание"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Позиция заказа")
        verbose_name_plural = _("Позиции заказа")
        ordering = ("pk",)
        indexes = [
            models.Index(fields=("order",)),
            models.Index(fields=("variant",)),
            models.Index(fields=("status",)),
        ]
        constraints = [
            # на одном заказе можно позволить дубли с разными ценами, но чаще — хотим уникальность варианта
            # если нужно запретить дубли — раскомментируй UniqueConstraint:
            # models.UniqueConstraint(fields=("order", "variant"), name="uq_order_variant"),
        ]

    def __str__(self):
        return f"{self.variant} × {self.quantity}"

    @property
    def amount(self) -> Decimal:
        return (self.unit_price or Decimal("0.00")) * self.quantity

    def clean(self):
        super().clean()
        if not self.variant_id:
            from django.core.exceptions import ValidationError
            raise ValidationError({"variant": _("Укажите вариант модели.")})

    def save(self, *args, **kwargs):
        # если цена не задана — берём текущую цену варианта (если есть)
        if (self.unit_price is None or self.unit_price == 0) and getattr(self, "variant", None):
            # у тебя у варианта есть поле unit_price (мы им пользовались в списках)
            price = getattr(self.variant, "unit_price", None)
            if price is not None:
                self.unit_price = price
        super().save(*args, **kwargs)
        # после сохранения позиции — пересчитаем итоги заказа
        self.order.recompute_totals(save=True)


class SewingOrderSizeCount(models.Model):
    """
    Количества по размерам для конкретной строки заказа (варианта).
    """
    item = models.ForeignKey(SewingOrderItem, related_name="size_counts", on_delete=models.CASCADE)
    size = models.ForeignKey('info.Size', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["item", "size"], name="uniq_item_size")
        ]