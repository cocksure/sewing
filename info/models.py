import os
from io import BytesIO
from datetime import datetime

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile
from django.utils.text import slugify

from core.mixins import AuditUserSaveMixin
from core.models import BaseModel
from PIL import Image

PACKING_CHOICES = (
    (1, _('Рулон')),
    (2, _('Пачка')),
    (3, _('Раскрытий')),
)

COLOR_TONES = (
    (1, _('Светлый')),
    (2, _('Средний')),
    (3, _('Тёмный')),
    (4, _('Белый'))
)


class PRODUCT_TYPES:
    cloth = 4


class Measurements:
    # Shtuk
    PIECE = 1
    KG = 2
    METER = 3
    GRAMM = 7
    LITER = 11
    RULON = 16


class SaleTypes:
    local = 1
    export = 2


def process_image(image, upload_path="uploads/", max_size=(1920, 1080), quality=85):
    try:
        img = Image.open(image)

        # Проверка формата
        if img.format and img.format.lower() not in ['jpg', 'jpeg', 'png', 'webp']:
            raise ValueError(f"Неподдерживаемый формат: {img.format}")

        # Сжатие
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)

        # Сохраняем в webp
        output = BytesIO()
        img.save(output, format="WEBP", quality=quality, optimize=True)
        output.seek(0)

        # Имя файла
        filename_wo_ext = os.path.splitext(os.path.basename(image.name))[0]
        safe_name = slugify(filename_wo_ext) + ".webp"
        full_path = os.path.join(upload_path, safe_name)

        return full_path, ContentFile(output.read())

    except Exception as e:
        raise ValueError(f"Ошибка при обработке изображения: {e}")


class UploadedImage(AuditUserSaveMixin, BaseModel):
    image = models.ImageField(_("Фото"), upload_to="%Y/%m/%d")

    class Meta:
        managed = True
        db_table = "upload_images"
        verbose_name = _("Загруженная картинка")
        verbose_name_plural = _("Загруженные картинки")

    def __str__(self):
        return os.path.basename(self.image.name) if self.image else "—"

    def save(self, *args, **kwargs):
        if self.image:
            new_name, new_file = process_image(self.image, "uploads/")
            # Удаление старого файла (если обновляем картинку)
            if self.pk:
                try:
                    old = UploadedImage.objects.get(pk=self.pk)
                    if old.image and old.image != self.image:
                        old.image.delete(save=False)
                except UploadedImage.DoesNotExist:
                    pass

            self.image.save(new_name, new_file, save=False)

        super().save(*args, **kwargs)


class UploadedFile(AuditUserSaveMixin, BaseModel):
    file = models.FileField(_('Файл'), upload_to='%Y/%m/%d')

    class Meta:
        managed = True
        db_table = 'upload_files'
        verbose_name = _('Загруженный файл')
        verbose_name_plural = _('Загруженные файлы')

    def __str__(self):
        return self.file.name


COMPANIES = (
    ('uztex', _('UzTex Group')),
    ('zarofat', _('Zarofat')),
)


class Role(models.Model):
    class Meta:
        verbose_name = _('Роль')
        verbose_name_plural = _('Роли')

    name = models.CharField(_('Названия'), max_length=128)
    is_master = models.BooleanField(_('Мастер'), default=False, blank=True)

    def __str__(self) -> str:
        return self.name


class ProductType(models.Model):
    name = models.CharField(
        _('Тип продукта'), max_length=64, blank=False, null=False)

    class Meta:
        managed = True
        db_table = 'product_type'
        verbose_name = _('Тип модели')
        verbose_name_plural = _('Типы модели')

    def __str__(self):
        return self.name


class Firm(AuditUserSaveMixin, BaseModel):
    TYPE_CHOICES = (
        ('customer', 'Заказчик'),
        ('provision', 'Поставщик'),
        ('customer-provision', 'Заказчик-Поставщик'),
    )
    code = models.CharField(_('Код'), max_length=128, unique=True)
    name = models.CharField(
        _('Наименование'), max_length=128, blank=False, null=False)
    type = models.CharField(_('Тип'), max_length=40,
                            choices=TYPE_CHOICES, default='customer')
    status = models.SmallIntegerField(_('Статус'), default=1)
    legal_address = models.CharField(
        _('Юридический адрес'), max_length=512, blank=True, null=True)
    actual_address = models.CharField(
        _('Фактический адрес'), max_length=512, blank=True, null=True)
    phone = models.CharField(
        'Номер телефона', max_length=30, blank=True, null=True)
    fax = models.CharField('Факс', max_length=30, blank=True, null=True)
    email = models.CharField(
        'Электронная почта', max_length=128, blank=True, null=True)
    certificate = models.CharField(
        'Номер лицензии', max_length=128, blank=True, null=True)
    material_discount = models.IntegerField('Материальная скидка', blank=True, null=True, default=0)
    logo = models.ForeignKey(UploadedImage, on_delete=models.PROTECT, null=True, blank=True)

    def save(self, *args, **kwargs):
        if Firm.objects.filter(name__iexact=self.name).exists():
            raise Exception('Повтор невозможно')
        super(Firm, self).save(*args, **kwargs)

    class Meta:
        managed = True
        db_table = 'firms'
        verbose_name = _('Фирма')
        verbose_name_plural = _('Фирмы')
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.code + ' - ' + self.name

    @staticmethod
    def fromJson(jsondata):
        for data in jsondata:
            try:
                firm = Firm(name=data['fr_tnm1'], code=data['fr_no'])
                firm.save()
            except Exception as e:
                print(data)
                print(e)


class ProcessRole(models.Model):
    class Meta:
        verbose_name = _('Роль сотрудника в процессе')
        verbose_name_plural = _('Роли сотрудников в процессе')

    process = models.ForeignKey('Process', on_delete=models.PROTECT, related_name='roles', verbose_name=_('Процесс'))
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='process_roles', verbose_name=_('Роль'))
    individual = models.BooleanField(_('Индивидуальный'), default=False, blank=True)
    salary_percent = models.FloatField(_('Процент ЗП'), default=0)
    salary_group = models.IntegerField(_('Группа ЗП'), default=1, blank=True, null=True)
    work_in_machine = models.BooleanField(_('Работа в машине'), default=False, blank=True,
                                          help_text="Может работать только в машине")
    work_in_max_machine = models.PositiveSmallIntegerField(_('Максимальное количество параллелных машин'), default=1,
                                                           blank=True, null=True,
                                                           help_text="Максимальное количество машин, которые может работать параллелно")

    def __str__(self) -> str:
        return '%s: %s' % (str(self.process), self.role.name)


class Specification(AuditUserSaveMixin, BaseModel):
    year = models.CharField(_('Год'), max_length=4, blank=False, null=False, default=str(datetime.now().year))
    name = models.CharField(_('Наименование'), max_length=128, blank=False, null=False)
    firm = models.ForeignKey('Firm', on_delete=models.PROTECT, verbose_name=_('Фирма'), null=True, blank=True)

    def save(self, *args, **kwargs):
        if Specification.objects.filter(name__iexact=self.name).exists():
            raise Exception('Повтор невозможно')
        super(Specification, self).save(*args, **kwargs)

    class Meta:
        managed = True
        db_table = 'specification'
        verbose_name = _('Спецификация')
        verbose_name_plural = _('Спецификации')


class Factory(AuditUserSaveMixin, BaseModel):
    name = models.CharField(_('Фабрика'), max_length=128)
    official_name = models.CharField(_('Официальное название'), max_length=128, blank=True, null=True)
    company = models.CharField(verbose_name=_('Компания'), blank=True, choices=COMPANIES, max_length=128,
                               default='uztex')

    class Meta:
        managed = True
        db_table = 'factories'
        verbose_name = _('Фабрика')
        verbose_name_plural = _('Фабрики')

    def __str__(self):
        return self.name


class Process(AuditUserSaveMixin, BaseModel):
    name = models.CharField(_('Названия'), max_length=128)
    order = models.SmallIntegerField(_('Порядок'), null=True, blank=True)
    is_parallel = models.BooleanField(_('Выполняется параллелно'), default=False)
    product_type = models.ForeignKey('ProductType', verbose_name=_('Тип производство'),
                                     on_delete=models.SET_NULL, null=True, blank=True)
    is_record_keeped = models.BooleanField(_('Введется учет'), default=True)
    barcode = models.CharField(_('Штрих-код'), max_length=128, blank=True, null=True, unique=True)
    replaceable_processes = models.ManyToManyField(
        'self', verbose_name=_('Заменяемые процессы'), blank=True, related_name='replaced_processes', symmetrical=False
    )
    required_process = models.ForeignKey(
        'self', verbose_name=_('Обязательный процесс'), blank=True, null=True,
        on_delete=models.SET_NULL, related_name='required_processes'
    )

    class Meta:
        db_table = 'process'
        verbose_name = _('Процесс')
        verbose_name_plural = _('Процессы')
        ordering = ('order',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)  # сначала получаем pk
        if is_new and not self.barcode:
            self.barcode = f'PROC{self.pk:04d}'
            # обновим только поле barcode без повторной полной валидации
            type(self).objects.filter(pk=self.pk).update(barcode=self.barcode)


class WorkType(AuditUserSaveMixin, BaseModel):
    name = models.CharField(_('Названия'), max_length=128)
    processes = models.ManyToManyField(Process, verbose_name=_('Процессы'), related_name='work_types')
    product_type = models.ForeignKey('ProductType', on_delete=models.PROTECT, verbose_name=_('Тип продукции'),
                                     blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'work_type'
        verbose_name = _('Вид работы')
        verbose_name_plural = _('Виды работы')

    def __str__(self):
        return self.name


class MaterialGroup(models.Model):
    name = models.CharField(_('Наименование'), max_length=512)
    code = models.CharField(_('Код'), max_length=256, unique=True)

    class Meta:
        managed = True
        db_table = 'material_group'
        verbose_name = _('Группа материалов')
        verbose_name_plural = _('Группы материалов')

    def __str__(self):
        return self.code + ' - ' + self.name

    @staticmethod
    def fromJson(jsondata):
        for data in jsondata:
            try:
                group = MaterialGroup(name=data['gr_tnm'], code=data['gr_kod'])
                group.save()
            except Exception as e:
                print(data)
                print(e)


class MeasurementUnit(models.Model):
    name = models.CharField('Единица', max_length=8)

    class Meta:
        managed = True
        db_table = 'measurement_unit'
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерении'

    def __str__(self):
        return self.name


class PriceCategory(models.Model):
    name = models.CharField(_('Наименование'), max_length=512)
    price = models.IntegerField(_('Цена'), default=0, blank=True)
    m_unit = models.ForeignKey(MeasurementUnit, verbose_name=_(
        'Единица измерения'), on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'price_category'
        verbose_name = _('Цена категория')
        verbose_name_plural = _('Цены категория')

    def __str__(self):
        return self.name + ' - ' + str(self.price)


class MaterialGroupCategory(models.Model):
    material_group = models.OneToOneField(MaterialGroup, verbose_name=_('Группа Материал'), on_delete=models.SET_NULL,
                                          related_name='price_category_material',
                                          null=True, blank=True)
    category = models.ForeignKey(PriceCategory, verbose_name=_('Группа Материал'), on_delete=models.SET_NULL,
                                 related_name='price_category_material',
                                 null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'material_group_category'
        verbose_name = _('Категория материал')
        verbose_name_plural = _('Категория материал')

    def __str__(self):
        return self.material_group.name + ' - ' + self.category.name


class MaterialSpecialGroup(models.Model):
    name = models.CharField(_('Наименование'), max_length=512)

    class Meta:
        managed = True
        db_table = 'material_special_group'
        verbose_name = _('Специальная группа')
        verbose_name_plural = _('Специальные группы')

    def __str__(self):
        return self.name


class ColorGroup(models.Model):
    name = models.CharField(_('Названия'), max_length=128)
    code = models.CharField(_('Code'), max_length=3)
    last_color_code = models.CharField(_('Последный код цвета'), max_length=10)

    class Meta:
        managed = True
        db_table = 'color_groups'
        verbose_name = _('Группа цветов')
        verbose_name_plural = _('Группы цветов')

    def __str__(self):
        return self.name


class RecipeType(models.Model):
    name = models.CharField(_('Наименование'), max_length=512)
    code = models.CharField(_('Код'), max_length=2, null=True)

    class Meta:
        managed = True
        db_table = 'recipe_type'
        verbose_name = _('Вид рецепт')
        verbose_name_plural = _('Виды Рецептов')

    def __str__(self):
        return self.name


class RecipeGroup(models.Model):
    name = models.CharField(_('Наименование'), max_length=512)

    class Meta:
        managed = True
        db_table = 'recipe_group'
        verbose_name = _('Группа рецепт')
        verbose_name_plural = _('Группа Рецептов')

    def __str__(self):
        return self.name


class TypeOrderColor(models.Model):
    name = models.CharField(_('Наименование'), max_length=512)
    code = models.CharField(_('Код'), max_length=128, null=True)

    class Meta:
        managed = True
        db_table = 'type_order_color'
        verbose_name = _('Вид заказ')
        verbose_name_plural = _('Виды Заказов')

    def __str__(self):
        return self.name


class ColorGraphic(models.Model):
    code = models.CharField(_('Код'), max_length=128, default='')
    name = models.CharField(_('Наименование'), max_length=512)

    class Meta:
        managed = True
        db_table = 'color_graphic'
        verbose_name = _('График')
        verbose_name_plural = _('График')

    def __str__(self):
        return self.name


class Material(AuditUserSaveMixin, BaseModel):
    # objects = MaterialManager()

    KIND_OF_STATIONS = (
        ('2', _('Автоматический')),
        ('5', _('Ручной')),
    )

    code = models.CharField(_('Код'), max_length=128, unique=True)
    title = models.CharField(_('Наименование'), max_length=512, db_index=True, blank=True)
    type = models.CharField(_('Тип'), max_length=128, null=True, blank=True)
    group = models.ForeignKey(MaterialGroup, verbose_name=_(
        'Группа'), on_delete=models.PROTECT, null=True, blank=True, related_name='materials')
    special_group = models.ForeignKey(MaterialSpecialGroup, verbose_name=_(
        'Специальная группа'), on_delete=models.PROTECT, null=True, blank=True, related_name='materials')
    definition_type = models.SmallIntegerField('Тип определения', default=0)
    width = models.FloatField(_('Ширина'), null=True, blank=True)
    length = models.FloatField(_('Длина'), null=True, blank=True)
    thickness = models.FloatField(_('Толщина'), null=True, blank=True)
    density = models.FloatField(_('Плотность'), null=True, blank=True)
    kind_of_station = models.CharField(verbose_name=_('Режим дозирования'), max_length=32, choices=KIND_OF_STATIONS,
                                       blank=True, null=True)
    m_unit = models.ForeignKey(MeasurementUnit, verbose_name=_(
        'Единица измерения'), on_delete=models.PROTECT)
    image = models.ForeignKey(UploadedImage, verbose_name=_(
        'Изображения'), on_delete=models.PROTECT, null=True, blank=True)
    color = models.ForeignKey('Color', verbose_name=_(
        'Цвет'), on_delete=models.PROTECT, null=True, blank=True)
    barcode_need = models.SmallIntegerField('Генерация баркода?', default=1)
    barcode = models.CharField('Баркод', max_length=128, null=True, blank=True)
    accounting_code = models.CharField('Бухгалтерский код', max_length=128, null=True, blank=True)
    producible = models.BooleanField(_('Производимый'), default=False)
    planned_cost = models.FloatField(_('Плановая цена'), default=0)
    stock_dec_places = models.PositiveSmallIntegerField(_('Десятичный разряд для склада'), default=2)
    gramaj = models.FloatField(_('Грам в метр'), default=0)

    class Meta:
        managed = True
        db_table = 'material'
        verbose_name = _('Материал')
        verbose_name_plural = _('Материалы')

        indexes = [
            GinIndex(fields=["title"], name="mat_title_trgm", opclasses=["gin_trgm_ops"]),
            GinIndex(fields=["code"], name="mat_code_trgm", opclasses=["gin_trgm_ops"]),
        ]

        # CREATE EXTENSION IF NOT EXISTS pg_trgm;
        # shu komandani 1 martta berish kere postgressda

    def __str__(self):
        return self.title

    @staticmethod
    def fromJson(jsondata):
        for data in jsondata:
            try:
                group = None
                if data['ma_grp'] != '':
                    group = MaterialGroup.objects.get(code=data['ma_grp'])
                material = Material(title=data['ma_tnm'], code=data['ma_kod'], m_unit_id=2)
                if group is not None:
                    material.group = group
                material.save()
            except Exception as e:
                print(data)
                print(e)


class SubMaterial(AuditUserSaveMixin, BaseModel):
    material = models.ForeignKey(Material, verbose_name=_('Материал'), on_delete=models.CASCADE,
                                 related_name='sub_materials')
    sub_material = models.ForeignKey(Material, verbose_name=_('Субматериал'), on_delete=models.PROTECT,
                                     related_name='as_sub_material')
    percent = models.FloatField(_('Процент'))

    class Meta:
        managed = True
        db_table = 'sub_materials'
        verbose_name = _('Определение субматериалов')
        verbose_name_plural = _('Определении субматериалов')

    def __str__(self):
        return self.material.title + ' - ' + self.sub_material.title + ' - ' + str(self.percent) + '%'


class Color(AuditUserSaveMixin, BaseModel):
    name = models.CharField(_('Наименование'), max_length=128)
    code = models.CharField(_('Код'), max_length=128, unique=True)
    group = models.ForeignKey(ColorGroup, verbose_name=_('Группа'), on_delete=models.SET_NULL, related_name='colors',
                              null=True, blank=True)
    input_date = models.DateField(_('Дата введение'), null=True, blank=True)
    create_date = models.DateField(_('Дата разработки'), null=True, blank=True)
    confirm_date = models.DateField(_('Дата подтверждения'), null=True, blank=True)
    catalog_n = models.CharField(_('Каталог №'), max_length=128, null=True, blank=True)
    tested_material = models.ForeignKey('Material', verbose_name=_('Материал добавление'), on_delete=models.PROTECT,
                                        blank=True, null=True, related_name='colors')
    color_tone = models.SmallIntegerField(_('Тон цвета'), null=True, blank=True, choices=COLOR_TONES)
    firm = models.ForeignKey('Firm', verbose_name=_('Фирма'), on_delete=models.PROTECT, blank=True, null=True,
                             related_name='colors')
    recipe_type = models.ForeignKey(RecipeType, verbose_name=_('Вид рецепт'), on_delete=models.PROTECT, blank=True,
                                    null=True, related_name='colors')
    recipe_group = models.ForeignKey(RecipeGroup, verbose_name=_('Группа рецепт'), on_delete=models.PROTECT, blank=True,
                                     null=True, related_name='colors')
    type_order = models.ForeignKey(TypeOrderColor, verbose_name=_('Вид заказ'), on_delete=models.PROTECT, blank=True,
                                   null=True, related_name='colors')
    graphic = models.ForeignKey(ColorGraphic, verbose_name=_('График'), on_delete=models.PROTECT, blank=True, null=True,
                                related_name='colors')
    rr = models.CharField(_('R'), max_length=128, default='', null=True, blank=True)
    gg = models.CharField(_('G'), max_length=128, default='', null=True, blank=True)
    bb = models.CharField(_('B'), max_length=128, default='', null=True, blank=True)
    rgb = models.CharField(_('RGB'), max_length=128, default='', null=True, blank=True)
    rgba = models.CharField(_('RGBA'), max_length=128, default='', null=True, blank=True)
    hex = models.CharField(_('HEX'), max_length=128, default='', null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'color'
        verbose_name = _('Цвет')
        verbose_name_plural = _('Цвета')

    def __str__(self):
        return self.code

    @staticmethod
    def fromJson(jsondata):
        for data in jsondata:
            try:
                color = Color(name=data['re_kod'], code=data['re_kod'])
                color.save()
            except Exception as e:
                print(data)
                print(e)


class RawMaterial(AuditUserSaveMixin, BaseModel):
    name = models.CharField('Raw Material name',
                            max_length=64, blank=False, null=False)
    price = models.FloatField('Material price', blank=False, null=False)
    product_type = models.ForeignKey(
        ProductType, on_delete=models.PROTECT, related_name='raw_materials')

    class Meta:
        managed = True
        db_table = 'raw_material'
        verbose_name = _('Сырье')
        verbose_name_plural = _('Сырье')

    def __str__(self):
        return self.name


class SewingMachineType(models.Model):
    name = models.CharField(_('Тип машины'), max_length=128)
    description = models.CharField(_('Описания'), max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'sewing_machine_types'
        verbose_name = _('Тип швейной машины')
        verbose_name_plural = _('Типы швейных машин')

    def __str__(self):
        return self.name


class Operation(models.Model):
    name = models.CharField(_("Операция"), max_length=128, unique=True)
    default_price = models.DecimalField(_("Цена по умолчанию"), max_digits=10, decimal_places=2, default=0)
    default_duration = models.PositiveIntegerField(_("Длительность, сек (по умолчанию)"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)
    notes = models.CharField(_("Примечание"), max_length=255, blank=True, null=True)

    machine_type = models.ForeignKey(
        SewingMachineType, verbose_name=_('Тип машины'),
        on_delete=models.PROTECT, related_name='operations', null=True, blank=True
    )

    class Meta:
        db_table = "sewing_operation_catalog"
        verbose_name = _("Операция (справочник)")
        verbose_name_plural = _("Операции (справочник)")

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(_("Размер"), max_length=64, unique=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    notes = models.CharField(_("Примечание"), max_length=255, blank=True, null=True)

    class Meta:
        db_table = "sewing_size_catalog"
        verbose_name = _("Размер (справочник)")
        verbose_name_plural = _("Размеры (справочник)")

    def __str__(self):
        return self.name
