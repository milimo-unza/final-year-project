/* ============================================================
   Harpr — calendar
   Month view: task chips injected directly into day cells
   via dayCellDidMount (bypassing FullCalendar's event renderer,
   which kept fighting us). Holidays still use the event system.
   Week view: default FullCalendar hour grid.
   List view: default FullCalendar list.
   ============================================================ */
(function () {
  'use strict';
  var el = document.getElementById('calendar');
  if (!el) return;

  var eventsUrl = el.dataset.eventsUrl;
  var initialView = window.matchMedia('(max-width: 768px)').matches ? 'listMonth' : 'dayGridMonth';

  var MAX_CHIPS = 3;
  var daysMap = {};   // populated from /calendar/events/

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
    initialView: initialView,
    height: 'auto',
    headerToolbar: false,   // our own toolbar lives in the template
    firstDay: 1,
    nowIndicator: true,
    dayMaxEvents: false,
    listDayFormat: { weekday: 'long', month: 'short', day: 'numeric' },
    listDaySideFormat: false,

    // Holidays only — tasks are injected manually below.
    events: function (info, successCallback, failureCallback) {
      fetch(eventsUrl, { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          daysMap = (data && data.days) || {};
          successCallback((data && data.holidays) || []);
          // Re-render so dayCellDidMount fires with daysMap populated.
          calendar.render();
        })
        .catch(failureCallback);
    },

    // Holiday chip rendering — stays as a FullCalendar event
    eventContent: function (arg) {
      var props = arg.event.extendedProps || {};
      if (props.holiday) {
        return { html: '<div class="chip chip-holiday">' + esc(arg.event.title) + '</div>' };
      }
      return true;
    },

    // Inject task chips into the day cell
    dayCellDidMount: function (arg) {
      var iso = isoLocal(arg.date);
      var tasks = daysMap[iso] || [];
      if (!tasks.length) return;

      // The frame is where FC renders the day number + events.
      var frame = arg.el.querySelector('.fc-daygrid-day-frame');
      if (!frame) return;

      // Build (or find) our own stack container under the day number.
      var stack = frame.querySelector('.harpr-chips');
      if (!stack) {
        stack = document.createElement('div');
        stack.className = 'harpr-chips';
        // Append after FC's own events container (which we hide via CSS).
        var eventsBox = frame.querySelector('.fc-daygrid-day-events');
        if (eventsBox) {
          eventsBox.appendChild(stack);
        } else {
          frame.appendChild(stack);
        }
      }

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
            window.HARPR_openDayModal(iso);
          }
        });
        stack.appendChild(more);
      }
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

  calendar.render();
})();
