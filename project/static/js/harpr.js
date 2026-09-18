/* ============================================================
   Harpr — global UI behaviour
   - Toast notifications
   - Modal popups (task create/edit, delete confirm, day-tasks, pomodoro settings, shortcuts)
   - Keyboard shortcuts
   - Browser notifications + reminder polling
   - Natural-language date parser (chrono-node) on task title input
   ============================================================ */
(function () {
  'use strict';

  var H = window.HARPR || {};
  var URLS = H.urls || {};

  // ---------- helpers -------------------------------------------------------

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function getCSRFToken() {
    var name = 'csrftoken';
    var cookies = document.cookie ? document.cookie.split('; ') : [];
    for (var i = 0; i < cookies.length; i++) {
      var parts = cookies[i].split('=');
      if (parts[0] === name) return decodeURIComponent(parts[1]);
    }
    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  // ---------- toast notifications ------------------------------------------

  function toast(message, kind) {
    if (!message) return;
    var c = document.getElementById('toast-container');
    if (!c) return;
    var el = document.createElement('div');
    el.className = 'toast ' + (kind || 'info');
    el.textContent = message;
    c.appendChild(el);
    // trigger transition
    requestAnimationFrame(function () { el.classList.add('show'); });
    setTimeout(function () {
      el.classList.remove('show');
      setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 250);
    }, 3000);
  }

  // Map Django message tags to toast kinds.
  function tagToKind(tag) {
    if (tag === 'success') return 'success';
    if (tag === 'error')   return 'error';
    return 'info';
  }

  // On load: lift any server-rendered Django messages into toasts.
  function popServerMessages() {
    var box = document.querySelector('[data-messages]');
    if (!box) return;
    $all('.message', box).forEach(function (m) {
      toast(m.textContent.trim(), tagToKind(m.getAttribute('data-tag') || 'info'));
    });
  }

  // Pop toasts queued by the modal-submit flow before page reload.
  function popQueuedToasts() {
    try {
      var raw = sessionStorage.getItem('harpr-pending-toasts');
      if (!raw) return;
      sessionStorage.removeItem('harpr-pending-toasts');
      var arr = JSON.parse(raw);
      arr.forEach(function (t) { toast(t.message, t.kind || 'success'); });
    } catch (e) {}
  }

  function queueToast(message, kind) {
    try {
      var raw = sessionStorage.getItem('harpr-pending-toasts');
      var arr = raw ? JSON.parse(raw) : [];
      arr.push({ message: message, kind: kind || 'success' });
      sessionStorage.setItem('harpr-pending-toasts', JSON.stringify(arr));
    } catch (e) {}
  }

  document.addEventListener('DOMContentLoaded', function () {
    popQueuedToasts();
    popServerMessages();
  });

  // ---------- modal management ---------------------------------------------

  var openModals = [];

  function openModal(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    el.hidden = false;
    document.body.classList.add('modal-open');
    openModals.push(el);
    return el;
  }

  function closeModal(el) {
    if (!el) return;
    el.hidden = true;
    var idx = openModals.indexOf(el);
    if (idx >= 0) openModals.splice(idx, 1);
    if (openModals.length === 0) document.body.classList.remove('modal-open');
  }

  function closeTopModal() {
    if (openModals.length === 0) return false;
    closeModal(openModals[openModals.length - 1]);
    return true;
  }

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t.classList && t.classList.contains('modal-backdrop')) {
      closeModal(t);
    } else if (t.closest && t.closest('.modal-close')) {
      var modal = t.closest('.modal-backdrop');
      closeModal(modal);
    }
  });

  // ---------- task create/edit modal (loads form via fetch) ---------------

  function loadFormIntoModal(modalId, bodyId, url, opts) {
    var body = document.getElementById(bodyId);
    if (!body) return;
    body.innerHTML = '<div class="modal-loading">Loading…</div>';
    openModal(modalId);

    fetch(url + (url.indexOf('?') >= 0 ? '&' : '?') + 'embed=1', {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        var temp = document.createElement('div');
        temp.innerHTML = html;
        var form = temp.querySelector('form.form-grid') || temp.querySelector('form');
        if (form) {
          if (!form.querySelector('input[name="next"]')) {
            var n = document.createElement('input');
            n.type = 'hidden';
            n.name = 'next';
            n.value = window.location.pathname + window.location.search;
            form.appendChild(n);
          }
          body.innerHTML = '';
          body.appendChild(form);
          attachModalSubmit(form, modalId, opts || {});
          attachChronoToForm(form);
        } else {
          body.innerHTML = '<div class="empty">Could not load form.</div>';
        }
      })
      .catch(function () {
        body.innerHTML = '<div class="empty">Could not load form.</div>';
      });
  }

  function attachModalSubmit(form, modalId, opts) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      fetch(form.action || window.location.pathname, {
        method: 'POST',
        body: data,
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (r) { return r.text().then(function (text) { return { r: r, text: text }; }); })
        .then(function (res) {
          var temp = document.createElement('div');
          temp.innerHTML = res.text;
          var formInResponse = temp.querySelector('form.form-grid') || temp.querySelector('form');
          var hasErrors = formInResponse && (
            formInResponse.querySelector('.errorlist') ||
            formInResponse.querySelector('.form-help')
          );
          if (hasErrors) {
            var modalBody = document.querySelector('#' + modalId + ' .modal-body');
            if (modalBody && formInResponse) {
              modalBody.innerHTML = '';
              modalBody.appendChild(formInResponse);
              attachModalSubmit(formInResponse, modalId, opts);
              attachChronoToForm(formInResponse);
            } else {
              window.location.reload();
            }
          } else {
            queueToast(opts.successToast || 'Saved', 'success');
            window.location.reload();
          }
        })
        .catch(function () { window.location.reload(); });
    });
  }

  // ---------- click handlers for modal triggers ----------------------------

  document.addEventListener('click', function (e) {
    var newTaskBtn = e.target.closest('[data-modal="task-new"]');
    if (newTaskBtn) {
      e.preventDefault();
      loadFormIntoModal('task-modal', 'task-modal-body', URLS.taskCreate, { successToast: 'Task added' });
      var title = document.getElementById('task-modal-title');
      if (title) title.textContent = 'New task';
      return;
    }
    var editTaskBtn = e.target.closest('[data-modal="task-edit"]');
    if (editTaskBtn) {
      e.preventDefault();
      var url = editTaskBtn.getAttribute('href') || editTaskBtn.dataset.url;
      loadFormIntoModal('task-modal', 'task-modal-body', url, { successToast: 'Task updated' });
      var title2 = document.getElementById('task-modal-title');
      if (title2) title2.textContent = 'Edit task';
      return;
    }
    var del = e.target.closest('[data-delete-task]');
    if (del) {
      e.preventDefault();
      openDeleteModal(del.getAttribute('data-delete-task'), del.getAttribute('data-task-title') || 'this task');
      return;
    }
  });

  // ---------- delete confirmation modal -----------------------------------

  function openDeleteModal(actionUrl, taskTitle) {
    var form = document.getElementById('delete-modal-form');
    if (!form) return;
    form.action = actionUrl;
    var titleEl = document.getElementById('delete-modal-task-title');
    if (titleEl) titleEl.textContent = taskTitle;
    var nextEl = document.getElementById('delete-modal-next');
    if (nextEl) nextEl.value = window.location.pathname + window.location.search;
    openModal('delete-modal');
  }

  // Intercept delete-modal submit so we can show a toast.
  (function () {
    var form = document.getElementById('delete-modal-form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      fetch(form.action, {
        method: 'POST',
        body: data,
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function () {
          queueToast('Task moved to trash', 'info');
          window.location.reload();
        })
        .catch(function () { window.location.reload(); });
    });
  })();

  // ---------- calendar day-tasks modal -------------------------------------

  window.HARPR_openDayModal = function (dateStr) {
    var body = document.getElementById('day-modal-body');
    var titleEl = document.getElementById('day-modal-title');
    if (!body) return;
    body.innerHTML = '<div class="modal-loading">Loading…</div>';
    if (titleEl) titleEl.textContent = 'Tasks';
    openModal('day-modal');

    fetch(URLS.calendarDayBase + dateStr + '/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (titleEl) titleEl.textContent = data.label || 'Tasks';
        if (!data.tasks || data.tasks.length === 0) {
          body.innerHTML = '<div class="empty">No tasks on this day.</div>';
          return;
        }
        var html = '';
        data.tasks.forEach(function (t) {
          html += '<div class="day-modal-task ' + (t.completed ? 'done' : '') + '">'
                +   '<form method="post" action="' + t.toggle_url + '" class="task-form-toggle" data-day-toggle>'
                +     '<input type="hidden" name="csrfmiddlewaretoken" value="' + getCSRFToken() + '">'
                +     '<input type="hidden" name="next" value="' + window.location.pathname + '">'
                +     '<button type="submit" class="checkbox-btn ' + (t.completed ? 'checked' : '') + '" aria-label="Toggle"></button>'
                +   '</form>'
                +   '<div class="time">' + (t.time || '') + '</div>'
                +   '<div class="title"><a href="' + t.edit_url + '" data-modal="task-edit">' + escapeHtml(t.title) + '</a></div>'
                +   '<span class="pill ' + escapeHtml(t.priority.toLowerCase()) + '">' + escapeHtml(t.priority) + '</span>'
                + '</div>';
        });
        body.innerHTML = html;
      })
      .catch(function () {
        body.innerHTML = '<div class="empty">Could not load tasks.</div>';
      });
  };

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // ---------- keyboard shortcuts -------------------------------------------

  function isTyping(t) {
    if (!t) return false;
    var tag = (t.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
    if (t.isContentEditable) return true;
    return false;
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      if (closeTopModal()) e.preventDefault();
      return;
    }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (isTyping(e.target)) return;

    var k = e.key.toLowerCase();
    switch (k) {
      case 'n':
        e.preventDefault();
        loadFormIntoModal('task-modal', 'task-modal-body', URLS.taskCreate, { successToast: 'Task added' });
        var t = document.getElementById('task-modal-title');
        if (t) t.textContent = 'New task';
        break;
      case 't':
        e.preventDefault();
        window.location.href = URLS.timeline;
        break;
      case 'c':
        e.preventDefault();
        window.location.href = URLS.calendar;
        break;
      case 'd':
        e.preventDefault();
        window.location.href = URLS.dashboard;
        break;
      case '?':
        e.preventDefault();
        openModal('shortcuts-modal');
        break;
    }
  });

  var helpBtn = document.getElementById('shortcuts-help');
  if (helpBtn) {
    helpBtn.addEventListener('click', function () { openModal('shortcuts-modal'); });
  }

  // ---------- browser notifications + reminders ----------------------------

  function ensureNotificationPermission() {
    if (!('Notification' in window)) return Promise.resolve('unsupported');
    if (Notification.permission === 'granted') return Promise.resolve('granted');
    if (Notification.permission === 'denied') return Promise.resolve('denied');
    return Notification.requestPermission();
  }

  var firedReminders = (function () {
    try { return JSON.parse(sessionStorage.getItem('harpr-fired-reminders') || '{}'); }
    catch (e) { return {}; }
  })();

  function recordFired(key) {
    firedReminders[key] = Date.now();
    try { sessionStorage.setItem('harpr-fired-reminders', JSON.stringify(firedReminders)); } catch (e) {}
  }

  function checkReminders() {
    if (!H.notificationsEnabled) return;
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    if (!URLS.remindersDue) return;
    fetch(URLS.remindersDue, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        (data.reminders || []).forEach(function (rem) {
          var key = 'task-' + rem.id + '-due-' + rem.due;
          if (firedReminders[key]) return;
          try {
            new Notification('Harpr — ' + rem.title, {
              body: 'Due at ' + rem.due,
              tag: key,
              icon: '/static/favicon.svg'
            });
            recordFired(key);
          } catch (err) { /* ignore */ }
        });
      })
      .catch(function () { /* ignore */ });
  }

  if (H.notificationsEnabled && 'Notification' in window) {
    if (Notification.permission === 'default') {
      var asked = false;
      var ask = function () {
        if (asked) return;
        asked = true;
        ensureNotificationPermission();
        document.removeEventListener('click', ask);
        document.removeEventListener('keydown', ask);
      };
      document.addEventListener('click', ask);
      document.addEventListener('keydown', ask);
    }
    setInterval(checkReminders, 60 * 1000);
    setTimeout(checkReminders, 5000);
  }

  // ---------- chrono-node natural language date parser ---------------------

  function attachChronoToForm(formRoot) {
    if (typeof chrono === 'undefined') return;
    var titleInput = formRoot.querySelector('input[data-chrono="1"]');
    if (!titleInput) return;
    var dueInput = formRoot.querySelector('input[type="datetime-local"]');
    if (!dueInput) return;

    // Hint area placed right after the title input
    var hint = document.createElement('div');
    hint.className = 'chrono-hint';
    titleInput.parentNode.appendChild(hint);

    var lastParsed = null; // remember so we can undo

    function parse() {
      var txt = titleInput.value || '';
      if (!txt.trim()) { hint.classList.remove('shown'); return; }
      var results = chrono.parse(txt, new Date(), { forwardDate: true });
      if (!results || results.length === 0) {
        hint.classList.remove('shown');
        return;
      }
      var r = results[0];
      var dt = r.start.date();
      // Format for datetime-local input: YYYY-MM-DDTHH:MM
      var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
      var iso = dt.getFullYear() + '-' + pad(dt.getMonth() + 1) + '-' + pad(dt.getDate())
              + 'T' + pad(dt.getHours()) + ':' + pad(dt.getMinutes());
      // Only fill if user hasn't manually set a value (or matches our last parsed)
      if (!dueInput.value || dueInput.value === lastParsed) {
        dueInput.value = iso;
        lastParsed = iso;
      }
      hint.innerHTML = 'Detected: <strong>' + escapeHtml(r.text) + '</strong> → '
                     + escapeHtml(dt.toLocaleString())
                     + ' <span class="undo-link" data-undo>clear</span>';
      hint.classList.add('shown');
    }

    var debounceTimer = null;
    titleInput.addEventListener('input', function () {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(parse, 300);
    });
    hint.addEventListener('click', function (e) {
      if (e.target && e.target.matches('[data-undo]')) {
        if (dueInput.value === lastParsed) dueInput.value = '';
        lastParsed = null;
        hint.classList.remove('shown');
      }
    });
    // run once on load
    parse();
  }

  // expose for use by inline scripts (e.g. settings page) and other modals
  window.HARPR.toast = toast;
  window.HARPR.openModal = openModal;
  window.HARPR.closeModal = closeModal;
})();
