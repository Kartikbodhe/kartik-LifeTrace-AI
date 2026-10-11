/**
 * LifeTrace AI — Interactive Calendar Component
 * Supports Month View & Agenda View
 */

document.addEventListener('DOMContentLoaded', () => {
  const calendarContainer = document.getElementById('calendarMount');
  if (!calendarContainer) return;

  let currentDate = new Date();
  let eventsData = [];
  let currentView = 'month'; // 'month' or 'agenda'

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  function fetchEventsAndRender() {
    fetch('/calendar/api/events')
      .then(res => res.json())
      .then(data => {
        eventsData = data.events || [];
        render();
      })
      .catch(err => {
        console.error('Failed to load events:', err);
      });
  }

  function render() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const titleEl = document.getElementById('calendarTitle');
    if (titleEl) {
      titleEl.textContent = `${monthNames[month]} ${year}`;
    }

    if (currentView === 'month') {
      renderMonthView(year, month);
    } else {
      renderAgendaView(year, month);
    }
  }

  function renderMonthView(year, month) {
    const firstDayIndex = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();

    let html = `
      <div class="calendar-grid">
        <div class="cal-weekday">Sun</div>
        <div class="cal-weekday">Mon</div>
        <div class="cal-weekday">Tue</div>
        <div class="cal-weekday">Wed</div>
        <div class="cal-weekday">Thu</div>
        <div class="cal-weekday">Fri</div>
        <div class="cal-weekday">Sat</div>
    `;

    // Blank cells before first day
    for (let i = 0; i < firstDayIndex; i++) {
      html += `<div class="cal-day cal-day-empty"></div>`;
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const isToday =
        today.getFullYear() === year &&
        today.getMonth() === month &&
        today.getDate() === day;

      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayEvents = eventsData.filter(e => e.start.startsWith(dateStr));

      html += `
        <div class="cal-day ${isToday ? 'cal-today' : ''}">
          <div class="cal-day-num">${day}</div>
          <div class="cal-day-events">
            ${dayEvents.map(e => `
              <div class="cal-event-pill" style="border-left: 3px solid ${e.color};" onclick="showEventModal('${e.id}')">
                <span class="cal-event-title">${escapeHtml(e.title)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    html += `</div>`;
    calendarContainer.innerHTML = html;
  }

  function renderAgendaView(year, month) {
    const monthPrefix = `${year}-${String(month + 1).padStart(2, '0')}`;
    const sortedEvents = eventsData
      .filter(e => e.start.startsWith(monthPrefix))
      .sort((a, b) => a.start.localeCompare(b.start));

    if (sortedEvents.length === 0) {
      calendarContainer.innerHTML = `
        <div class="empty-state" style="padding: 3rem 1rem;">
          <div class="empty-state-icon">📅</div>
          <div class="empty-state-title">No events this month</div>
          <p class="empty-state-desc">You don't have any tasks, payment deadlines, or follow-ups scheduled for ${monthNames[month]} ${year}.</p>
        </div>
      `;
      return;
    }

    let html = `<div class="agenda-list">`;
    sortedEvents.forEach(e => {
      const datePart = e.start.split('T')[0];
      const timePart = e.start.includes('T') ? e.start.split('T')[1].substring(0, 5) : 'All Day';

      html += `
        <div class="agenda-item card" style="margin-bottom: 0.75rem; border-left: 4px solid ${e.color};">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
            <div>
              <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.25rem;">
                <a href="${e.url}" style="color: inherit;">${escapeHtml(e.title)}</a>
              </div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">
                <span class="badge" style="background: rgba(255,255,255,0.06); color: #fff;">${e.category}</span>
                <span style="margin-left: 0.5rem;">📅 ${datePart} (${timePart})</span>
              </div>
              ${e.description ? `<p style="font-size: 0.84rem; color: var(--text-muted); margin-top: 0.4rem;">${escapeHtml(e.description)}</p>` : ''}
            </div>
            <a href="${e.url}" class="btn btn-secondary btn-sm">View</a>
          </div>
        </div>
      `;
    });
    html += `</div>`;
    calendarContainer.innerHTML = html;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Navigation handlers
  const prevBtn = document.getElementById('calPrev');
  const nextBtn = document.getElementById('calNext');
  const todayBtn = document.getElementById('calToday');
  const viewToggle = document.getElementById('calViewToggle');

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      currentDate.setMonth(currentDate.getMonth() - 1);
      render();
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      currentDate.setMonth(currentDate.getMonth() + 1);
      render();
    });
  }

  if (todayBtn) {
    todayBtn.addEventListener('click', () => {
      currentDate = new Date();
      render();
    });
  }

  if (viewToggle) {
    viewToggle.addEventListener('change', (e) => {
      currentView = e.target.value;
      render();
    });
  }

  // Event modal preview
  window.showEventModal = function(eventId) {
    const event = eventsData.find(e => e.id === eventId);
    if (!event) return;

    const modalTitle = document.getElementById('calModalTitle');
    const modalBody = document.getElementById('calModalBody');
    const modalLink = document.getElementById('calModalLink');

    if (modalTitle) modalTitle.textContent = event.title;
    if (modalBody) {
      modalBody.innerHTML = `
        <p style="margin-bottom: 0.5rem;"><strong>Category:</strong> ${event.category}</p>
        <p style="margin-bottom: 0.5rem;"><strong>When:</strong> ${event.start.replace('T', ' ')}</p>
        <p style="margin-bottom: 0.5rem;"><strong>Status:</strong> ${event.status || 'Active'}</p>
        <p style="color: var(--text-muted); margin-top: 0.75rem;">${escapeHtml(event.description)}</p>
      `;
    }
    if (modalLink) {
      modalLink.href = event.url;
    }

    window.openModal('calendarEventModal');
  };

  // Initial load
  fetchEventsAndRender();
});
