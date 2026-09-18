(function () {
  'use strict';
  var el = document.getElementById('calendar');
  if (!el) return;

  var eventsUrl = el.dataset.eventsUrl;
  var initialView = window.matchMedia('(max-width: 768px)').matches ? 'listMonth' : 'dayGridMonth';

  // dot data: { 'YYYY-MM-DD': { cls: 'dot-work', color: '#3B82F6' } }
  var dotsByDate = {};

  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function isoLocal(d) {
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }

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
    dayMaxEvents: false,    // tasks render as dots; holidays render as actual events
    // List view: "Monday, Apr 28"
    listDayFormat: { weekday: 'long', month: 'short', day: 'numeric' },
    listDaySideFormat: false,
    events: function (info, successCallback, failureCallback) {
      fetch(eventsUrl, { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          dotsByDate = (data && data.dots) || {};
          successCallback((data && data.events) || []);
          // Re-render so dayCellDidMount picks up the dot data
          calendar.render();
        })
        .catch(failureCallback);
    },
    dayCellDidMount: function (arg) {
      var iso = isoLocal(arg.date);
      var dot = dotsByDate[iso];
      if (dot) {
        arg.el.classList.add('has-tasks');
        if (dot.cls) arg.el.classList.add(dot.cls);
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
