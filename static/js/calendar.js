/* ============================================================
   Harpr calendar — single page, three views (month, week, list).
   FullCalendar runs in the month container only. Week and List are
   rendered server-side and swapped in by toggling `hidden`.
   ============================================================ */
(function () {
  'use strict';

  var monthEl = document.getElementById('calendar');
  if (!monthEl) return;

  var MAX_CHIPS = 3;
  var daysMap = {};
  var fcCalendar = null;

  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function isoLocal(d) {
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }
  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // ---------- Month view ----------
  function initMonth() {
    if (fcCalendar) return;
    fcCalendar = new FullCalendar.Calendar(monthEl, {
      initialView: 'dayGridMonth',
      height: 'auto',
      headerToolbar: false,
      firstDay: 0,
      nowIndicator: true,
      dayMaxEvents: false,
      events: function (info, successCallback, failureCallback) {
        fetch(monthEl.dataset.eventsUrl, { credentials: 'same-origin' })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            daysMap = (data && data.days) || {};
            successCallback((data && data.holidays) || []);
          })
          .catch(failureCallback);
      },
      eventContent: function (arg) {
        var props = arg.event.extendedProps || {};
        if (props.holiday) {
          return { html: '<div class="chip chip-holiday">' + esc(arg.event.title) + '</div>' };
        }
        return true;
      },
      datesSet: function () { setTimeout(injectChips, 0); },
      eventsSet: function () { setTimeout(injectChips, 0); },
      dateClick: function (info) {
        if (typeof window.HARPR_openDayModal === 'function') {
          window.HARPR_openDayModal(isoLocal(info.date));
        }
      },
      eventClick: function (info) {
        info.jsEvent.preventDefault();
        if (info.event.start && typeof window.HARPR_openDayModal === 'function') {
          window.HARPR_openDayModal(isoLocal(info.event.start));
        }
      }
    });
    fcCalendar.render();
  }

  function injectChips() {
    var cells = document.querySelectorAll('#calendar .fc-daygrid-day');
    cells.forEach(function (cell) {
      var dateStr = cell.getAttribute('data-date');
      if (!dateStr) return;
      var tasks = daysMap[dateStr] || [];
      var existing = cell.querySelector('.harpr-chips');
      if (existing) existing.remove();
      if (!tasks.length) return;
      var frame = cell.querySelector('.fc-daygrid-day-frame');
      if (!frame) return;
      var stack = document.createElement('div');
      stack.className = 'harpr-chips';
      var visible = tasks.slice(0, MAX_CHIPS);
      var hidden = tasks.length - visible.length;
      visible.forEach(function (t) {
        var chip = document.createElement('div');
        var cls = ['chip', 'chip-task', 'chip-' + (t.category || 'work')];
        if (t.completed) cls.push('chip-done');
        chip.className = cls.join(' ');
        chip.innerHTML = '<span class="chip-time">' + esc(t.time || '') + '</span>' +
                         '<span class="chip-title">' + esc(t.title) + '</span>';
        stack.appendChild(chip);
      });
      if (hidden > 0) {
        var more = document.createElement('button');
        more.type = 'button';
        more.className = 'harpr-more';
        more.textContent = '+' + hidden + ' more';
        more.addEventListener('click', function (e) {
          e.stopPropagation();
          if (typeof window.HARPR_openDayModal === 'function') {
            window.HARPR_openDayModal(dateStr);
          }
        });
        stack.appendChild(more);
      }
      var target = frame.querySelector('.fc-daygrid-day-events') || frame;
      target.appendChild(stack);
    });
  }

  // ---------- View switching ----------
  var views = {
    month: document.getElementById('cal-month'),
    week:  document.getElementById('cal-week'),
    list:  document.getElementById('cal-list'),
  };
  var tabs = document.querySelectorAll('[data-cal-view]');
  var labelEl = document.getElementById('cal-label');

  function setView(name) {
    Object.keys(views).forEach(function (k) {
      if (views[k]) views[k].hidden = (k !== name);
    });
    tabs.forEach(function (t) {
      t.classList.toggle('active', t.dataset.calView === name);
    });
    if (name === 'month') {
      initMonth();
      // FullCalendar can't measure when hidden — force a resize after showing.
      if (fcCalendar) setTimeout(function () { fcCalendar.updateSize(); }, 0);
    }
  }

  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      setView(t.dataset.calView);
    });
  });

  // ---------- Prev / Today / Next ----------
  var weekAnchor = new Date();

  document.querySelectorAll('[data-cal-nav]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var action = btn.dataset.calNav;

      // Month view: FullCalendar handles its own navigation.
      if (!views.month.hidden && fcCalendar) {
        if (action === 'prev') fcCalendar.prev();
        else if (action === 'next') fcCalendar.next();
        else fcCalendar.today();
        if (labelEl) labelEl.textContent = fcCalendar.view.title;
        return;
      }

      // Week / List: shift our anchor and refetch the payload.
      if (action === 'prev') weekAnchor.setDate(weekAnchor.getDate() - 7);
      else if (action === 'next') weekAnchor.setDate(weekAnchor.getDate() + 7);
      else weekAnchor = new Date();

      var iso = weekAnchor.toISOString().slice(0, 10);
      var url = '/calendar/?start=' + iso;

      fetch(url, { credentials: 'same-origin' })
        .then(function (r) { return r.text(); })
        .then(function (html) {
          var doc = new DOMParser().parseFromString(html, 'text/html');
          var newWeek = doc.getElementById('cal-week');
          var newList = doc.getElementById('cal-list');
          var newLabel = doc.getElementById('cal-label');
          if (newWeek && views.week) {
            views.week.innerHTML = newWeek.innerHTML;
          }
          if (newList && views.list) {
            views.list.innerHTML = newList.innerHTML;
          }
          if (newLabel && labelEl) {
            labelEl.textContent = newLabel.textContent;
          }
        })
        .catch(function () {});
    });
  });

  // ---------- Initial view (default = month) ----------
  setView('month');
})();
