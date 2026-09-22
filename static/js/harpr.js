/* ============================================================
   Harpr — global UI behaviour
   - Toast notifications
   - Modal popups (task create/edit, delete confirm, day-tasks)
   - Keyboard shortcuts
   - Browser notifications + reminder polling
   - Natural-language date parser (regex — chrono-free)
   - Default-task-value autofill (today + 2hrs rounded to 30min, remind 5)
   - AJAX task-toggle (no page reload)
   ============================================================ */
(function () {
  'use strict';

  var H = window.HARPR || {};
  var URLS = H.urls || {};

  // ---------- helpers -------------------------------------------------------

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function pad(n) { return n < 10 ? '0' + n : '' + n; }

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

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
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
    requestAnimationFrame(function () { el.classList.add('show'); });
    setTimeout(function () {
      el.classList.remove('show');
      setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 250);
    }, 3000);
  }

  function tagToKind(tag) {
    if (tag === 'success') return 'success';
    if (tag === 'error')   return 'error';
    return 'info';
  }

  function popServerMessages() {
    var box = document.querySelector('[data-messages]');
    if (!box) return;
    $all('.message', box).forEach(function (m) {
      toast(m.textContent.trim(), tagToKind(m.getAttribute('data-tag') || 'info'));
    });
  }

  function popQueuedToasts() {
    try {
      var raw = sessionStorage.getItem('harpr-pending-toasts');
      if (!raw) return;
      sessionStorage.removeItem('harpr-pending-toasts');
      JSON.parse(raw).forEach(function (t) { toast(t.message, t.kind || 'success'); });
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
          attachNaturalDateParser(form);
          // Apply default values only on CREATE (not edit)
          if (form.getAttribute('data-is-edit') !== '1') {
            applyDefaultTaskValues(form);
          }
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
          var hasErrors = formInResponse && formInResponse.querySelector('.errorlist');
          if (hasErrors) {
            var modalBody = document.querySelector('#' + modalId + ' .modal-body');
            if (modalBody && formInResponse) {
              modalBody.innerHTML = '';
              modalBody.appendChild(formInResponse);
              attachModalSubmit(formInResponse, modalId, opts);
              attachNaturalDateParser(formInResponse);
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
          queueToast('Task deleted', 'info');
          window.location.reload();
        })
        .catch(function () { window.location.reload(); });
    });
  })();

  // ---------- AJAX task-toggle (no page reload) ----------------------------

  function ajaxToggleHandler(form) {
    if (form.dataset.ajaxBound === '1') return;
    form.dataset.ajaxBound = '1';
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      var btn = form.querySelector('.checkbox-btn');
      if (btn) btn.disabled = true;
      fetch(form.action, {
        method: 'POST',
        body: data,
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
      })
        .then(function (r) { return r.json(); })
        .then(function (resp) {
          if (btn) btn.disabled = false;
          var row = form.closest('.task-row, .day-modal-task');
          if (!row) return;
          row.classList.toggle('done', !!resp.completed);
          if (btn) btn.classList.toggle('checked', !!resp.completed);

          // Update KPI on dashboard
          var kpi = document.querySelector('[data-pending-kpi]');
          if (kpi && typeof resp.today_someday_count === 'number') {
            kpi.textContent = resp.today_someday_count;
          }
          // On dashboard, completed rows fade out (they don't belong in pending lists).
          if (resp.completed && row.dataset.removeOnComplete === '1') {
            row.classList.add('removing');
            setTimeout(function () {
              if (row.parentNode) row.parentNode.removeChild(row);
              maybeShowEmptyState();
            }, 280);
          }
          if (window.HARPR && window.HARPR.toast) {
            window.HARPR.toast(resp.completed ? 'Task completed' : 'Task re-opened',
                               resp.completed ? 'success' : 'info');
          }
        })
        .catch(function () {
          if (btn) btn.disabled = false;
          // Fall back to a plain reload on error.
          form.submit();
        });
    });
  }

  function maybeShowEmptyState() {
    $all('[data-section]').forEach(function (sec) {
      if (sec.children.length === 0 && !sec.dataset.emptyShown) {
        var msg = document.createElement('div');
        msg.className = 'empty';
        msg.textContent = 'Nothing left in this section.';
        sec.parentNode.appendChild(msg);
        sec.dataset.emptyShown = '1';
      }
    });
  }

  function bindAjaxToggleForms(root) {
    $all('form[data-ajax-toggle]', root || document).forEach(ajaxToggleHandler);
  }
  document.addEventListener('DOMContentLoaded', function () { bindAjaxToggleForms(); });
  // Expose so the day-modal renderer can re-bind freshly inserted rows.
  window.HARPR_bindAjaxToggle = bindAjaxToggleForms;

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
        var html = '';
        if (data.holidays && data.holidays.length) {
          data.holidays.forEach(function (h) {
            html += '<div class="day-modal-holiday">🇿🇲 ' + escapeHtml(h) + ' (public holiday)</div>';
          });
        }
        if (!data.tasks || data.tasks.length === 0) {
          html += '<div class="empty">No tasks on this day.</div>';
          body.innerHTML = html;
          return;
        }
        data.tasks.forEach(function (t) {
          html += '<div class="day-modal-task ' + (t.completed ? 'done' : '') + '">'
                +   '<form method="post" action="' + t.toggle_url + '" class="task-form-toggle" data-ajax-toggle>'
                +     '<input type="hidden" name="csrfmiddlewaretoken" value="' + getCSRFToken() + '">'
                +     '<input type="hidden" name="next" value="' + window.location.pathname + '">'
                +     '<button type="submit" class="checkbox-btn ' + (t.completed ? 'checked' : '') + '" aria-label="Toggle"></button>'
                +   '</form>'
                +   '<div class="time">' + (t.time || '') + '</div>'
                +   '<div class="title">'
                +     '<a href="' + t.edit_url + '" data-modal="task-edit">' + escapeHtml(t.title) + '</a>'
                +     ' <span class="cat-chip cat-' + escapeHtml(t.category_key) + '">' + escapeHtml(t.category) + '</span>'
                +   '</div>'
                +   '<span class="pill ' + escapeHtml(t.priority_key) + '">' + escapeHtml(t.priority) + '</span>'
                + '</div>';
        });
        body.innerHTML = html;
        bindAjaxToggleForms(body);
      })
      .catch(function () {
        body.innerHTML = '<div class="empty">Could not load tasks.</div>';
      });
  };

  // ---------- natural-language date parser (regex; no chrono) -------------

  var WEEKDAYS = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'];
  var MONTHS = {
    jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
    jul: 6, aug: 7, sep: 8, sept: 8, oct: 9, nov: 10, dec: 11,
    january: 0, february: 1, march: 2, april: 3, june: 5,
    july: 6, august: 7, september: 8, october: 9, november: 10, december: 11
  };

  function parseNaturalDate(text) {
    if (!text) return null;
    var lower = ' ' + text.toLowerCase() + ' ';
    var now = new Date();
    var date = null;
    var matchedText = null;

    // tomorrow
    if (/\btomorrow\b/.test(lower)) {
      date = new Date(now); date.setDate(date.getDate() + 1);
      matchedText = 'tomorrow';
    }
    // in N days / weeks
    if (!date) {
      var inDays = lower.match(/\bin\s+(\d+)\s+day(s)?\b/);
      if (inDays) {
        date = new Date(now); date.setDate(date.getDate() + parseInt(inDays[1], 10));
        matchedText = 'in ' + inDays[1] + ' day' + (parseInt(inDays[1], 10) === 1 ? '' : 's');
      }
    }
    if (!date) {
      var inWeeks = lower.match(/\bin\s+(\d+)\s+week(s)?\b/);
      if (inWeeks) {
        var w = parseInt(inWeeks[1], 10);
        date = new Date(now); date.setDate(date.getDate() + w * 7);
        matchedText = 'in ' + w + ' week' + (w === 1 ? '' : 's');
      }
    }
    // next <weekday>
    if (!date) {
      var wd = lower.match(/\bnext\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b/);
      if (wd) {
        var t1 = WEEKDAYS.indexOf(wd[1]);
        var diff = (t1 - now.getDay() + 7) % 7;
        if (diff === 0) diff = 7;
        date = new Date(now); date.setDate(date.getDate() + diff);
        matchedText = 'next ' + wd[1];
      }
    }
    // this <weekday> / on <weekday> / bare <weekday>
    if (!date) {
      var wd2 = lower.match(/\b(?:on|this)?\s*(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b/);
      if (wd2) {
        var t2 = WEEKDAYS.indexOf(wd2[1]);
        var diff2 = (t2 - now.getDay() + 7) % 7;
        if (diff2 === 0) diff2 = 7;
        date = new Date(now); date.setDate(date.getDate() + diff2);
        matchedText = wd2[1];
      }
    }
    // on Apr 30 / on April 30 / Apr 30 / April 30th
    if (!date) {
      var m = lower.match(/\b(?:on\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sept|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?\b/);
      if (m) {
        var mi = MONTHS[m[1]];
        var dayN = parseInt(m[2], 10);
        if (mi != null && dayN >= 1 && dayN <= 31) {
          date = new Date(now.getFullYear(), mi, dayN);
          var todayMid = new Date(now.getFullYear(), now.getMonth(), now.getDate());
          if (date < todayMid) date = new Date(now.getFullYear() + 1, mi, dayN);
          matchedText = m[1].charAt(0).toUpperCase() + m[1].slice(1) + ' ' + dayN;
        }
      }
    }
    // bare "today" — only if no other anchor matched
    if (!date && /\btoday\b/.test(lower)) {
      date = new Date(now);
      matchedText = 'today';
    }

    if (!date) return null;

    // Time: "at 5pm", "5pm", "5:30pm", "at 17:30", "17:30"
    var hour = null, minute = 0, timeText = '';
    var tm = lower.match(/\b(?:at\s+)?(\d{1,2}):(\d{2})\s*(am|pm)\b/);
    if (tm) {
      hour = parseInt(tm[1], 10); minute = parseInt(tm[2], 10);
      if (tm[3] === 'pm' && hour < 12) hour += 12;
      if (tm[3] === 'am' && hour === 12) hour = 0;
      timeText = ' at ' + tm[1] + ':' + tm[2] + tm[3];
    } else {
      var tm2 = lower.match(/\b(?:at\s+)?(\d{1,2})\s*(am|pm)\b/);
      if (tm2) {
        hour = parseInt(tm2[1], 10); minute = 0;
        if (tm2[2] === 'pm' && hour < 12) hour += 12;
        if (tm2[2] === 'am' && hour === 12) hour = 0;
        timeText = ' at ' + tm2[1] + tm2[2];
      } else {
        var tm3 = lower.match(/\b(?:at\s+)(\d{1,2}):(\d{2})\b/);
        if (tm3) {
          hour = parseInt(tm3[1], 10); minute = parseInt(tm3[2], 10);
          timeText = ' at ' + tm3[1] + ':' + tm3[2];
        }
      }
    }

    if (hour !== null) {
      date.setHours(hour, minute, 0, 0);
    } else {
      date.setHours(9, 0, 0, 0); // default 9am
    }
    return { date: date, text: matchedText + timeText };
  }

  function attachNaturalDateParser(formRoot) {
    var titleInput = formRoot.querySelector('input[data-chrono="1"]');
    if (!titleInput) return;
    var dueInput = formRoot.querySelector('input[type="datetime-local"]');
    if (!dueInput) return;
    var hint = formRoot.querySelector('[data-chrono-hint]');
    if (!hint) {
      hint = document.createElement('div');
      hint.className = 'chrono-hint';
      titleInput.parentNode.appendChild(hint);
    }
    var lastParsed = null;

    function parse() {
      var txt = titleInput.value || '';
      if (!txt.trim()) {
        hint.classList.remove('shown'); hint.hidden = true; return;
      }
      var res = parseNaturalDate(txt);
      if (!res) {
        hint.classList.remove('shown'); hint.hidden = true; return;
      }
      var dt = res.date;
      var iso = dt.getFullYear() + '-' + pad(dt.getMonth() + 1) + '-' + pad(dt.getDate())
              + 'T' + pad(dt.getHours()) + ':' + pad(dt.getMinutes());
      // Only fill if user hasn't manually set a value (or matches our last parsed)
      if (!dueInput.value || dueInput.value === lastParsed) {
        dueInput.value = iso;
        lastParsed = iso;
      }
      hint.hidden = false;
      hint.innerHTML = 'Parsed: <strong>' + escapeHtml(res.text) + '</strong> → '
                     + escapeHtml(dt.toLocaleString())
                     + ' <span class="undo-link" data-undo>clear</span>';
      hint.classList.add('shown');
    }

    var debounceTimer = null;
    titleInput.addEventListener('input', function () {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(parse, 250);
    });
    hint.addEventListener('click', function (e) {
      if (e.target && e.target.matches('[data-undo]')) {
        if (dueInput.value === lastParsed) dueInput.value = '';
        lastParsed = null;
        hint.classList.remove('shown'); hint.hidden = true;
      }
    });
    parse();
  }

  // ---------- default values for the New-task modal ------------------------

  function applyDefaultTaskValues(form) {
    var dueInput = form.querySelector('input[type="datetime-local"]');
    if (dueInput && !dueInput.value) {
      var d = new Date(Date.now() + 2 * 60 * 60 * 1000);
      // Round to nearest 30 min
      var min = d.getMinutes();
      if (min === 0 || min === 30) {
        d.setSeconds(0, 0);
      } else if (min < 30) {
        d.setMinutes(30, 0, 0);
      } else {
        d.setHours(d.getHours() + 1);
        d.setMinutes(0, 0, 0);
      }
      d.setSeconds(0, 0);
      dueInput.value = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
                     + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    }
    var remindSelect = form.querySelector('select[name="remind_minutes_before"]');
    if (remindSelect && (remindSelect.value === '' || remindSelect.value === '0')) {
      for (var i = 0; i < remindSelect.options.length; i++) {
        if (remindSelect.options[i].value === '5') {
          remindSelect.selectedIndex = i;
          break;
        }
      }
    }
  }

  // ---------- quick add on Today -------------------------------------------

  (function () {
    var input = document.getElementById('quick-add-input');
    var btn = document.getElementById('quick-add-btn');
    if (!input || !btn) return;

    function submit() {
      var raw = (input.value || '').trim();
      if (!raw) return;

      var due = null;
      try {
        var parsed = window.HARPR.parseNaturalDate ? window.HARPR.parseNaturalDate(raw) : null;
        if (parsed && parsed.date) {
          var d = parsed.date;
          var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
          due = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
              + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes());
        }
      } catch (e) { due = null; }

      var data = new FormData();
      data.append('title', raw);
      if (due) data.append('due_date', due);
      data.append('category', 'work');
      data.append('csrfmiddlewaretoken', getCSRFToken());

      btn.disabled = true;
      fetch('/tasks/quick-add/', {
        method: 'POST',
        body: data,
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (r) { return r.json(); })
        .then(function (resp) {
          btn.disabled = false;
          if (resp && resp.ok) {
            try { sessionStorage.setItem('harpr-pending-toasts', JSON.stringify([{ message: 'Task added', kind: 'success' }])); } catch (e) {}
            window.location.reload();
          }
        })
        .catch(function () { btn.disabled = false; });
    }

    btn.addEventListener('click', submit);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); submit(); }
    });
  })();


  // ---------- log-time modal ----------------------------------------------

  document.addEventListener('click', function (e) {
    var link = e.target.closest('[data-logtime-task]');
    if (!link) return;
    e.preventDefault();
    var url = link.getAttribute('href');

    var body = document.getElementById('logtime-modal-body');
    if (!body) return;
    body.innerHTML = '<div class="modal-loading">Loading...</div>';
    openModal('logtime-modal');

    fetch(url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        var temp = document.createElement('div');
        temp.innerHTML = html;
        var form = temp.querySelector('form.form-grid') || temp.querySelector('form');
        if (form) {
          body.innerHTML = '';
          body.appendChild(form);
          // Also grab the descriptive paragraph if present
          var desc = temp.querySelector('.card > p');
          if (desc) body.insertBefore(desc, body.firstChild);

          form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            var data = new FormData(form);
            fetch(form.action || window.location.pathname, {
              method: 'POST', body: data, credentials: 'same-origin',
              headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
              .then(function (r) {
                try { sessionStorage.setItem('harpr-pending-toasts', JSON.stringify([{ message: 'Time logged', kind: 'success' }])); } catch (err) {}
                window.location.reload();
              })
              .catch(function () { window.location.reload(); });
          });
        } else {
          body.innerHTML = '<div class="empty">Could not load form.</div>';
        }
      })
      .catch(function () {
        body.innerHTML = '<div class="empty">Could not load form.</div>';
      });
  });


  // ---------- expose -------------------------------------------------------

  window.HARPR.toast = toast;
  window.HARPR.openModal = openModal;
  window.HARPR.closeModal = closeModal;
  window.HARPR.parseNaturalDate = parseNaturalDate;
})();
