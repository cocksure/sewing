from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from config import settings
from core.models import BaseModel
from info.models import Factory, UploadedImage, Process


class Position(BaseModel):
    name = models.CharField("Название должности", max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        ordering = ["name"]


class Department(BaseModel):
    name = models.CharField(_('Отдел'), max_length=128)
    factory = models.ForeignKey(Factory, verbose_name=_(
        'Фабрика'), on_delete=models.PROTECT, related_name='departments')
    employee_count = models.IntegerField(
        _('Количество сотрудников'), default=0)
    approve_employee_works = models.BooleanField(_('Одобрить рабочих дней сотрудников'), default=False)
    master = models.ForeignKey('Employee', on_delete=models.SET_NULL, verbose_name=_('Мастер'), null=True, blank=True,
                               related_name='mastered_departments')

    class Meta:
        managed = True
        db_table = 'departments'
        verbose_name = _('Отдел')
        verbose_name_plural = _('Отдели')

    def __str__(self):
        return self.name


class Employee(BaseModel):
    ROLL_STATUSES = (
        (0, _('-----------')),
        (1, _('Модель носков')),
        (2, _('Склад')),
        (3, _('Модель одежди')),
        (4, _('ТБ')),
        (5, _('Модель носков материал')),
        (6, _('Модель носков аксессуар')),
    )
    factory = models.ForeignKey(Factory, verbose_name=_(
        'Фабрика'), on_delete=models.PROTECT, related_name='employees', default=1)
    position = models.ForeignKey(Position, verbose_name=_(
        'Должность'), on_delete=models.PROTECT, blank=False, null=False, related_name='personals')
    department = models.ForeignKey(Department, verbose_name=_(
        'Департамент'), on_delete=models.PROTECT, blank=False, null=False, related_name='personals')
    full_name = models.CharField(
        _('Ф.И.О.'), max_length=128, blank=False, null=False)
    report_card = models.IntegerField(_('Табель №'), null=True, blank=True)
    employment_date = models.DateField(_('Дата приема'), null=True, blank=True)
    dismissal_date = models.DateField(_('Дата увольнения'), null=True, blank=True)
    fired = models.BooleanField(_('Уволен'), default=False, null=True, blank=True)
    black_listed = models.BooleanField(_('В черном списке'), default=False)
    black_listed_reason = models.TextField(_('Причина черного списка'), null=True, blank=True)
    birth_date = models.DateField(_('Дата рождения'))
    position_last_updated = models.DateTimeField(blank=True, null=True)
    # age = models.IntegerField(_('Возраст'))
    # work_length = models.IntegerField(_('Стаж работы'))
    address = models.CharField(_('Адрес'), max_length=512, null=True, blank=True)
    gender = models.SmallIntegerField(_('Пол'))
    passport_id = models.CharField(_('№ и серия паспорта'), max_length=9, null=True, blank=True)
    issued_by = models.CharField(_('Кем выдан'), max_length=256, null=True, blank=True)
    issued_date = models.DateField(_('Когда выдан'), null=True, blank=True)
    pinfl = models.CharField(_('PIN физического лица'), null=True, blank=True, max_length=14, unique=True)
    photo = models.ForeignKey(UploadedImage, on_delete=models.PROTECT, null=True, blank=True)
    finger1 = models.TextField(_('Отпечаток пальца'), null=True, blank=True)
    finger2 = models.TextField(_('Доп.отпечаток пальца'), null=True, blank=True)
    email = models.EmailField(_('Почта'), null=True, blank=True)
    phone = PhoneNumberField(verbose_name="Телефон", region="UZ")
    phone_number = models.CharField(_('Доп номер телефона'), max_length=13, null=True, blank=True)
    badge = models.CharField(_('№ бейджика'), max_length=128, unique=True, null=True, blank=True)
    sewing_line = models.ForeignKey('sewing.SewingLine', on_delete=models.SET_NULL, related_name='employees',
                                    verbose_name=_('Линия швейки'), null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_('Пользователь системы'), on_delete=models.PROTECT,
                                related_name='employee', null=True, blank=True)
    # warehouses = models.ManyToManyField(Warehouse, verbose_name=_('Склады'), blank=True, null=True,
    #                                     related_name='operators')

    additional_factories = models.ManyToManyField(Factory, verbose_name=_('Дополнительные фабрики'),
                                                  related_name='additional_employees', blank=True)
    telegram_id = models.BigIntegerField(_('Номер телеграма'), default=0)
    ptr = models.IntegerField(_('ID турникет (GATE)'), default=0)
    can_delete_sock_package = models.BooleanField(_('Может удалить упаковок носков'), default=False)
    # tg_approved = models.BooleanField(_('Телеграм утвержден'), default=False)
    imported = models.BooleanField(_('Импортирован из другой системы'), default=False)
    additional_role = models.SmallIntegerField(_('Дополнительное правило'), default=0, blank=True, null=True,
                                               choices=ROLL_STATUSES)
    face = models.TextField(_('Лицо'), blank=True, null=True)
    one_c_deprtment_id = models.IntegerField(_('ID отдела на 1C'), blank=True, null=True)
    one_c_deprtment_name = models.CharField(_('Название отдела на 1C'), max_length=512, blank=True, null=True)
    one_c_sync_error_log = models.TextField(_('Лог синхронизации'), blank=True, null=True, editable=False)
    one_c_registered = models.BooleanField(_('Регистрирован в 1С'), default=False)
    is_iron_book = models.BooleanField(_('Темир дафтар'), default=False)
    exclude_attendance_auto_block = models.BooleanField(_('Исключать авто блокирование входа'), default=False)
    access_control_factories = models.ManyToManyField(Factory, verbose_name=_('Фабрики для доступа'),
                                                      related_name='attendance_access_employees', blank=True)
    process_roles = models.ManyToManyField('info.ProcessRole', verbose_name=_('Роли процессов'),
                                           related_name='employees', blank=True,)
    password_date = models.DateField(_('Последняя изменение пароля'), null=True, blank=True)
    need_password_change = models.BooleanField(_('Требуется изменение пароля'), default=False)
    working_hours = models.FloatField(_('Количество рабочих часов'), blank=True, null=True)
    working_days = models.FloatField(_('Количество рабочих дней'), blank=True, null=True,
                                     validators=[MinValueValidator(0), MaxValueValidator(7)])
    process = models.ForeignKey(Process, verbose_name=_('Процесс'), on_delete=models.PROTECT, null=True, blank=True,
                                related_name='departments')

    def save(self, *args, **kwargs):
        if self.pinfl:
            if not self.pinfl.isdigit():
                raise ValidationError(_('PINFL must be exactly 14 digits.'))
        #
        # from hr.models import AccessControlDevice, AccessControlEmployeeToSync, AttendenceBlockedEmployee
        # badge_changed = False
        # face_changed = True
        # fired_changed = False
        # if self.id:
        #     old_instance = Employee.objects.get(pk=self.id)
        #     if self.badge == '' or self.badge == "" or self.badge is None:
        #         self.badge = '_{}'.format(self.id)
        #     # badge_changed = old_instance.badge != self.badge
        #     if (
        #             old_instance.position_id == 341 or old_instance.position_id == 733) and old_instance.position != self.position:
        #         self.position_last_updated = timezone.now()
        #     face_changed = old_instance.face != self.face
        #     if self.fired != old_instance.fired:
        #         fired_changed = True
        #         if self.fired:
        #             self.one_c_registered = False
        #             if hasattr(self, 'user') and self.user:
        #                 self.user.is_active = False
        #                 self.sewing_line = None
        #                 self.user.save()
        #         else:
        #             if hasattr(self, 'user') and self.user:
        #                 self.user.is_active = True
        #                 self.user.save()
        # else:
        #     if self.position_id == 341 or self.position_id == 733:
        #         self.position_last_updated = timezone.now()
        #     last_id = Employee.objects.last()
        #     if last_id:
        #         last_id = last_id.id
        #     else:
        #         last_id = 0
        #     if self.badge == '' or self.badge == "" or self.badge is None:
        #         self.badge = '_{}'.format(last_id + 1)
        #
        # super().save(*args, **kwargs)
        # if badge_changed or face_changed or fired_changed == True:
        #     for device in AccessControlDevice.objects.filter(
        #             Q(department=self.department) | Q(factory=self.factory_id) | Q(
        #                 factory=self.factory.attendance_through) | Q(
        #                 factory__in=self.access_control_factories.all().values('pk'))).filter(is_register=False):
        #         if not AttendenceBlockedEmployee.objects.filter(employee=self).exists():
        #             if not AccessControlEmployeeToSync.objects.filter(
        #                     Q(employee=self) & Q(device=device) & (Q(blocked=True) | Q(blocked_changed=True))).exists():
        #                 device_emp = AccessControlEmployeeToSync.objects.filter(employee=self, device=device).first()
        #                 if device_emp:
        #                     device_emp.badge_changed = device_emp.badge_changed or badge_changed
        #                     device_emp.face_changed = device_emp.face_changed or face_changed
        #                     device_emp.fired_changed = fired_changed
        #                     device_emp.save()
        #                 elif self.fired == False:
        #                     AccessControlEmployeeToSync.objects.create(
        #                         employee=self,
        #                         device=device,
        #                         badge_changed=True,
        #                         face_changed=True,
        #                     )

    class Meta:
        managed = True
        db_table = 'employee'
        verbose_name = _('Сотрудник')
        verbose_name_plural = _('Сотрудники')
        # unique_together = ['factory', 'report_card']

    def __str__(self):
        return self.full_name
