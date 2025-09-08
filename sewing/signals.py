# sewing/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import VariantMaterial, VariantAccessory, ModelVariant, SewingProductModel


def _recalc_direct(variant: ModelVariant):
    # прямой UPDATE без вызова save() => без повторных сигналов/логики в save()
    ModelVariant.objects.filter(pk=variant.pk).update(unit_price=variant.recalc_price())


@receiver([post_save, post_delete], sender=VariantMaterial)
def _vm_changed(sender, instance, **kwargs):
    _recalc_direct(instance.variant)


@receiver([post_save, post_delete], sender=VariantAccessory)
def _va_changed(sender, instance, **kwargs):
    _recalc_direct(instance.variant)


# (необязательно, но полезно) — если изменились базовые цены/проценты у модели,
# пересчитать ВСЕ её варианты.
@receiver(post_save, sender=SewingProductModel)
def _spm_prices_changed(sender, instance: SewingProductModel, **kwargs):
    for v in instance.variants.all():
        _recalc_direct(v)
