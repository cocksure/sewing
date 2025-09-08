from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, db_index=True, verbose_name="Обновлено")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_%(class)ss", db_index=True, verbose_name="Кем создано"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="updated_%(class)ss", db_index=True, verbose_name="Кем обновлено"
    )

    class Meta:
        abstract = True
        ordering = ("-created_at",)
