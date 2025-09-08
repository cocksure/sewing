# sewing/utils.py
import re

from .models import ModelVariant

_COPY_SUFFIX_RE = re.compile(r"\s*\(копия(?:\s*\d+)?\)$", re.IGNORECASE)


def _strip_copy_suffixes(name: str) -> str:
    """Убирает все хвосты вида '(копия)' или '(копия N)' многократно."""
    base = name.strip()
    while True:
        new = _COPY_SUFFIX_RE.sub("", base).strip()
        if new == base:
            return base
        base = new


def make_clone_name(product_model_id: int, original_name: str) -> str:
    """
    Делает уникальное имя внутри одной модели изделия:
      base -> base (копия) -> base (копия 2) -> base (копия 3) ...
    """
    base = _strip_copy_suffixes(original_name)
    # первый кандидат без номера
    candidate = f"{base} (копия)"
    if not ModelVariant.objects.filter(product_model_id=product_model_id, name=candidate).exists():
        return candidate

    # дальше с номером
    n = 2
    while True:
        candidate = f"{base} (копия {n})"
        if not ModelVariant.objects.filter(product_model_id=product_model_id, name=candidate).exists():
            return candidate
        n += 1
