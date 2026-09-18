(function () {
  'use strict';
  var el = document.getElementById('calendar');
  if (!el) return;

  var eventsUrl = el.dataset.eventsUrl;
  var initialView = window.matchMedia('(max-width: 768px)').matches ? 'listMonth' : 'dayGridMonth';

  // Cache of dates that have at least one task, used by dayCellDidMount
  var datesWithEvents = {};

  var calendar = new FullCalendar.Calendar(el, {
    initialView: initialView,
    height: 'auto',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,listMonth'
    },
    buttonText: { today: 'Today', month: 'Month', week: 'Week', list: 'List' },
    firstDay: 1,
    nowIndicator: true,
    dayMaxEvents: 0,        // we use dots instead of event chips
    events: function (info, successCallback, failureCallback) {
      fetch(eventsUrl, { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          datesWithEvents = {};
          (data || []).forEach(function (e) {
            var d = (e.start || '').slice(0, 10);
            if (d) datesWithEvents[d] = true;
          });
          successCallback(data);
          // Re-render so dayCellDidMount fires with the new dates set
          calendar.render();
        })
        .catch(failureCallback);
    },
    dayCellDidMount: function (arg) {
      var iso = arg.date.toISOString().slice(0, 10);
      // Use local date (avoid UTC shift): build YYYY-MM-DD from local parts
      var d = arg.date;
      var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
      var localIso = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
      if (datesWithEvents[localIso] || datesWithEvents[iso]) {
        arg.el.classList.add('has-tasks');
      }
    },
    dateClick: function (info) {
      // Convert to local YYYY-MM-DD for the API call
      var d = info.date;
      var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
      var iso = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
      if (typeof window.HARPR_openDayModal === 'function') {
        window.HARPR_openDayModal(iso);
      }
    },
    eventClick: function (info) {
      info.jsEvent.preventDefault();
      var d = info.event.start;
      if (!d) return;
      var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
      var iso = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
      if (typeof window.HARPR_openDayModal === 'function') {
        window.HARPR_openDayModal(iso);
      }
    }
  });

  calendar.render();
})();
