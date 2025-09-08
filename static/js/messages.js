// static/js/messages.js
(function(){
  const BOX_ID = 'global-messages';
  const HIDE_MS = 3200;

  function bsClose(el){
    try {
      const inst = window.bootstrap?.Alert?.getOrCreateInstance(el);
      if (inst) inst.close();
      else {
        el.classList.remove('show');
        el.addEventListener('transitionend', ()=> el.remove(), {once:true});
      }
    } catch(_) {}
  }

  function armAutoHide(el){
    if (!el || el.dataset.autoclose) return;
    el.dataset.autoclose = '1';
    setTimeout(()=> bsClose(el), HIDE_MS);
  }

  // Публичный вызов (можно дергать вручную)
  window.showGlobalMessage = function(text, type){
    if (!text || !String(text).trim()) return;
    const box = document.getElementById(BOX_ID);
    if (!box) return;

    // Bootstrap-мэппинг
    const map = { error:'danger', danger:'danger', warning:'warning', info:'info', success:'success' };
    const cls = map[type] || 'info';

    // Без крестика, по центру
    const el = document.createElement('div');
    el.className = `alert alert-${cls} fade show shadow-sm mb-2 text-center`;
    el.setAttribute('role', 'alert');
    el.style.pointerEvents = 'auto'; // кликабельно поверх модалки, если надо
    el.textContent = text;

    box.appendChild(el);
    armAutoHide(el);
  };

  // Перехват fetch → читаем заголовки от вьюх (работает и из модалок)
  const origFetch = window.fetch;
  window.fetch = async function(...args){
    const resp = await origFetch(...args);
    try {
      const typ = resp.headers.get('X-Message-Type');
      const b64 = resp.headers.get('X-Message-B64');
      const raw = resp.headers.get('X-Message');
      if (b64) {
        const msg = decodeURIComponent(escape(atob(b64)));
        window.showGlobalMessage(msg, typ);
      } else if (raw) {
        window.showGlobalMessage(raw, typ);
      }
    } catch(_) {}
    return resp;
  };

  // При загрузке: автозакрыть уже отрендеренные Django-сообщения
  document.addEventListener('DOMContentLoaded', ()=>{
    const box = document.getElementById(BOX_ID);
    if (!box) return;

    // гарантируем поверх всего
    if (!box.style.zIndex) box.style.zIndex = '2000';

    // навесим авто-скрытие на уже существующие .alert (из шаблона)
    box.querySelectorAll('.alert').forEach(armAutoHide);

    // следим за новыми вставками (AJAX/модалки)
    new MutationObserver(muts=>{
      for (const m of muts) {
        m.addedNodes.forEach(node=>{
          if (!(node instanceof Element)) return;
          if (node.classList?.contains('alert')) armAutoHide(node);
          node.querySelectorAll?.('.alert').forEach(armAutoHide);
        });
      }
    }).observe(box, {childList:true, subtree:true});
  });
})();