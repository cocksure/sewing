// static/js/select2-init.js

;(function () {
  // Настройки по умолчанию
  const DEFAULTS = {
    minimumInputLength: 0,
    width: '100%',
  };

  // Определяет опции Select2 для конкретного элемента
  function buildOptions(el) {
    const modal = el.closest('.modal');
    const opts = {
      minimumInputLength: +(el.dataset.minimumInputLength || DEFAULTS.minimumInputLength),
      width: el.dataset.width || DEFAULTS.width,
      placeholder: el.dataset.placeholder || el.getAttribute('placeholder') || undefined,
      allowClear: el.dataset.allowClear === 'true' || el.getAttribute('data-allow-clear') === 'true',
    };
    if (modal && window.jQuery) {
      opts.dropdownParent = window.jQuery(modal); // важно для модалок
    }
    return opts;
  }

  // Инициализация одного элемента: либо djangoSelect2, либо обычный select2
  function initOne(el) {
    if (!window.jQuery) return;
    const $el = window.jQuery(el);

    // Уже инициализирован?
    if ($el.data('select2')) return;

    const opts = buildOptions(el);

    // Если доступен django-select2 (для ModelSelect2Widget)
    if (typeof $el.djangoSelect2 === 'function' && (el.classList.contains('django-select2') || el.classList.contains('django-select2-heavy'))) {
      try {
        $el.djangoSelect2(opts);
        return;
      } catch (e) {
        // если что-то пошло не так — попробуем обычный select2
      }
    }

    // Обычный select2 (для Select2Widget или «ручных» select'ов)
    if (typeof $el.select2 === 'function') {
      $el.select2(opts);
    }
  }

  // Инициализирует все select'ы внутри контейнера
  function initAll(container) {
    const root = container || document;

    // 1) django-select2 (ajax/«тяжёлые»)
    root.querySelectorAll('select.django-select2, select.django-select2-heavy').forEach(initOne);

    // 2) простые (помечай их в виджете: attrs={"data-select2":"1"} или классом .select2-basic)
    root.querySelectorAll('select[data-select2], select.select2-basic, select.select2').forEach(initOne);
  }

  // Автоинициализация при загрузке страницы
  document.addEventListener('DOMContentLoaded', () => {
    initAll(document);

    // Инициализация при показе любой модалки
    document.querySelectorAll('.modal').forEach(m => {
      m.addEventListener('shown.bs.modal', () => initAll(m));
    });

    // На случай динамических вставок HTML (AJAX) — MutationObserver
    const obs = new MutationObserver(muts => {
      for (const m of muts) {
        m.addedNodes.forEach(node => {
          if (!(node instanceof Element)) return;
          // если внутри есть селекты — инициализируем только этот фрагмент
          if (node.matches('select, .modal') || node.querySelector('select, .modal')) {
            initAll(node);
          }
        });
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });

    // Хелпер глобально
    window.reinitSelect2 = initAll;
  });
})();