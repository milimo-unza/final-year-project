/* ============================================================
   Harpr calendar — month view chips, week + list handled server-side.
   Chips are injected by walking the DOM after the fetch resolves —
   dayCellDidMount fires too early and doesn't reliably re-fire.
   ============================================================ */
(function () {
  'use strict';
  var el = document.getElementById('calendar');
  if (!el) return;

  var eventsUrl = el.dataset.eventsUrl;
  var MAX_CHIPS = 3;
  var daysMap = {};

  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function isoLocal(d) {
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }
  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  var calendar = new FullCalendar.Calendar(el, {
    initialView: 'dayGridMonth',
    height: 'auto',
    headerToolbar: false,
    firstDay: 0,
    nowIndicator: true,
    dayMaxEvents: false,

    events: function (info, successCallback, failureCallback) {
      fetch(eventsUrl, { credentials: 'same-origin' })
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

    // After FullCalendar finishes layout, inject our chips via direct DOM walk.
    datesSet: function () {
      setTimeout(injectAllChips, 0);
    },
    eventsSet: function () {
      setTimeout(injectAllChips, 0);
    },

    dateClick: function (info) {
      var iso = isoLocal(info.date);
      if (typeof window.HARPR_openDayModal === 'function') {
        window.HARPR_openDayModal(iso);
      }
    },
    eventClick: function (info) {
      info.jsEvent.preventDefault();
      var d = info.event.start;
      if (!d) return;
      var iso = isoLocal(d);
      if (typeof window.HARPR_openDayModal === 'function') {
        window.HARPR_openDayModal(iso);
      }
    }
  });

  function injectAllChips() {
    var cells = document.querySelectorAll('#calendar .fc-daygrid-day');
    cells.forEach(function (cell) {
      var dateStr = cell.getAttribute('data-date');
      if (!dateStr) return;
      var tasks = daysMap[dateStr] || [];

      // Remove any previous stack so we don't double-inject.
      var existing = cell.querySelector('.harpr-chips');
      if (existing) existing.remove();

      if (!tasks.length) return;

      var frame = cell.querySelector('.fc-daygrid-day-frame');
      if (!frame) return;

      var stack = document.createElement('div');
      stack.className = 'harpr-chips';

      var visible = tasks.slice(0, MAX_CHIPS);
      var hidden  = tasks.length - visible.length;

      visible.forEach(function (t) {
        var chip = document.createElement('div');
        var cls = ['chip', 'chip-task', 'chip-' + (t.category || 'work')];
        if (t.priority === 'urgent') cls.push('chip-urgent');
        if (t.completed) cls.push('chip-done');
        chip.className = cls.join(' ');
        chip.innerHTML =
          '<span class="chip-time">' + esc(t.time || '') + '</span>' +
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

      // Append inside the day's events container (or fall back to the frame).
      var target = frame.querySelector('.fc-daygrid-day-events') || frame;
      target.appendChild(stack);
    });
  }

  calendar.render();
})();
