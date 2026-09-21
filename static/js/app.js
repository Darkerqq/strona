const pageData = document.body.dataset;
const selectedDateStr = pageData.selectedDate;
const todayDateStr = pageData.todayDate;
const onceTaskDays = JSON.parse(pageData.onceTaskDays || '[]');
const weekDaysData = JSON.parse(pageData.weekDays || '[]');
let currentDate = new Date(selectedDateStr);

const monthNames = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"];
const dayNames = ["Pn", "Wt", "Śr", "Cz", "Pt", "Sob", "Nie"];

function toggleDaysInput(show) {
    const input = document.getElementById('duration_days');
    const field = document.getElementById('duration-field');
    if (input) input.style.display = show ? 'inline-block' : 'none';
    if (field) field.classList.toggle('hidden-field', !show);
}

function renderCalendar() {
    const calendar = document.getElementById('calendar-grid');
    const monthLabel = document.getElementById('calendar-month-year');
    if (!calendar || !monthLabel) return;
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    monthLabel.innerText = `${monthNames[month]} ${year}`;
    const grid = calendar;
    grid.innerHTML = '';

    dayNames.forEach(day => {
        const dayHead = document.createElement('div');
        dayHead.className = 'calendar-day-header';
        dayHead.innerText = day;
        grid.appendChild(dayHead);
    });

    const firstDayIndex = (new Date(year, month, 1).getDay() + 6) % 7;
    const totalDays = new Date(year, month + 1, 0).getDate();

    for (let i = 0; i < firstDayIndex; i++) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'calendar-day empty';
        grid.appendChild(emptyDiv);
    }

    for (let day = 1; day <= totalDays; day++) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'calendar-day';
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        dayDiv.innerText = day;

        if (dateStr === todayDateStr) dayDiv.classList.add('today');
        if (dateStr === selectedDateStr) dayDiv.classList.add('selected');
        if (onceTaskDays.includes(dateStr)) {
            const dot = document.createElement('div');
            dot.className = 'has-data';
            dayDiv.appendChild(dot);
        }
        dayDiv.onclick = () => { window.location.href = `/?date=${dateStr}`; };
        grid.appendChild(dayDiv);
    }
}

function changeMonth(offset) {
    currentDate.setMonth(currentDate.getMonth() + offset);
    renderCalendar();
}

function goToToday() {
    window.location.href = `/?date=${todayDateStr}`;
}

async function loadReminders() {
    const list = document.getElementById('reminder-list');
    if (!list) return;

    try {
        const response = await fetch(`/api/reminders?date=${encodeURIComponent(selectedDateStr)}`);
        if (!response.ok) throw new Error('Nie udało się pobrać przypomnień');
        const reminders = await response.json();
        list.innerHTML = '';

        if (!reminders.length) {
            list.innerHTML = '<span style="color: #8b95a5; font-size: 0.85em;">Brak aktywnych przypomnień.</span>';
            return;
        }

        reminders.forEach(reminder => {
            const item = document.createElement('div');
            item.className = 'reminder-item';
            item.innerHTML = `<span class="reminder-time">${reminder.due_time}</span> ${escapeHtml(reminder.title)}<br><small>${reminder.reminder_minutes} min przed terminem</small>`;
            list.appendChild(item);
        });
    } catch (error) {
        list.innerHTML = '<span style="color: #f87171; font-size: 0.85em;">Nie udało się załadować przypomnień.</span>';
    }
}

function escapeHtml(value) {
    const element = document.createElement('div');
    element.textContent = value || '';
    return element.innerHTML;
}

function getBezierCurvePath(points) {
    if (points.length < 2) return '';
    let path = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
        const current = points[i];
        const next = points[i + 1];
        const controlX = (current.x + next.x) / 2;
        path += ` C ${controlX} ${current.y}, ${controlX} ${next.y}, ${next.x} ${next.y}`;
    }
    return path;
}

function renderLineChart() {
    const container = document.getElementById('chart-content');
    if (!container || !weekDaysData || weekDaysData.length === 0) return;
    container.innerHTML = '';

    const startX = 60;
    const endX = 940;
    const minY = 175;
    const stepX = (endX - startX) / (weekDaysData.length - 1);
    const points = weekDaysData.map((day, idx) => {
        const x = startX + (idx * stepX);
        const pct = Math.min(100, Math.max(-100, day.percentage || 0));
        const y = 102.5 - ((pct / 100) * 72.5);
        let colorClass = 'color-low';
        let hexColor = '#ef4444';
        if (pct >= 50) { colorClass = 'color-high'; hexColor = '#10b981'; }
        else if (pct >= 0) { colorClass = 'color-mid'; hexColor = '#f59e0b'; }
        const isToday = day.date === todayDateStr;
        return { x, y, pct, date: day.date, label: day.label, dayNum: day.day_num, isSelected: day.is_selected, isToday, colorClass, hexColor };
    });

    const svgNS = 'http://www.w3.org/2000/svg';
    const defs = document.createElementNS(svgNS, 'defs');
    const areaGrad = document.createElementNS(svgNS, 'linearGradient');
    areaGrad.setAttribute('id', 'dynamic-area-grad');
    areaGrad.setAttribute('x1', startX); areaGrad.setAttribute('y1', '0');
    areaGrad.setAttribute('x2', endX); areaGrad.setAttribute('y2', '0');
    areaGrad.setAttribute('gradientUnits', 'userSpaceOnUse');
    const lineGrad = document.createElementNS(svgNS, 'linearGradient');
    lineGrad.setAttribute('id', 'dynamic-line-grad');
    lineGrad.setAttribute('x1', startX); lineGrad.setAttribute('y1', '0');
    lineGrad.setAttribute('x2', endX); lineGrad.setAttribute('y2', '0');
    lineGrad.setAttribute('gradientUnits', 'userSpaceOnUse');

    points.forEach((point, idx) => {
        const offset = `${(idx / (points.length - 1)) * 100}%`;
        const stopArea = document.createElementNS(svgNS, 'stop');
        stopArea.setAttribute('offset', offset); stopArea.setAttribute('stop-color', point.hexColor); stopArea.setAttribute('stop-opacity', '0.3');
        areaGrad.appendChild(stopArea);
        const stopLine = document.createElementNS(svgNS, 'stop');
        stopLine.setAttribute('offset', offset); stopLine.setAttribute('stop-color', point.hexColor);
        lineGrad.appendChild(stopLine);
    });
    defs.appendChild(areaGrad); defs.appendChild(lineGrad); container.appendChild(defs);

    const curvePathD = getBezierCurvePath(points);
    const areaPath = document.createElementNS(svgNS, 'path');
    areaPath.setAttribute('d', `${curvePathD} L ${points[points.length - 1].x} ${minY} L ${points[0].x} ${minY} Z`);
    areaPath.setAttribute('fill', 'url(#dynamic-area-grad)');
    container.appendChild(areaPath);

    const linePath = document.createElementNS(svgNS, 'path');
    linePath.setAttribute('d', curvePathD); linePath.setAttribute('fill', 'none');
    linePath.setAttribute('stroke', 'url(#dynamic-line-grad)'); linePath.setAttribute('stroke-width', '4.5');
    linePath.setAttribute('stroke-linecap', 'round'); linePath.setAttribute('stroke-linejoin', 'round');
    container.appendChild(linePath);

    points.forEach(point => {
        if (point.isToday) {
            const todayLine = document.createElementNS(svgNS, 'line');
            todayLine.setAttribute('x1', point.x); todayLine.setAttribute('y1', point.y); todayLine.setAttribute('x2', point.x); todayLine.setAttribute('y2', minY);
            todayLine.setAttribute('stroke', '#6366f1'); todayLine.setAttribute('stroke-width', '2'); todayLine.setAttribute('stroke-dasharray', '4 4');
            container.appendChild(todayLine);
            const todayAura = document.createElementNS(svgNS, 'circle');
            todayAura.setAttribute('cx', point.x); todayAura.setAttribute('cy', point.y); todayAura.setAttribute('r', '18'); todayAura.setAttribute('fill', '#6366f1'); todayAura.setAttribute('fill-opacity', '0.25');
            container.appendChild(todayAura);
        }

        const link = document.createElementNS(svgNS, 'a');
        link.setAttribute('href', `/?date=${point.date}`); link.setAttribute('class', 'chart-point-link');
        const outer = document.createElementNS(svgNS, 'circle');
        outer.setAttribute('cx', point.x); outer.setAttribute('cy', point.y); outer.setAttribute('r', point.isToday ? '15' : '12'); outer.setAttribute('class', `chart-node-outer ${point.colorClass}`); link.appendChild(outer);
        const inner = document.createElementNS(svgNS, 'circle');
        inner.setAttribute('cx', point.x); inner.setAttribute('cy', point.y); inner.setAttribute('r', point.isToday ? '8.5' : '6.5'); inner.setAttribute('class', `chart-node ${point.colorClass} ${point.isSelected ? 'selected' : ''}`); link.appendChild(inner);
        const textLabel = document.createElementNS(svgNS, 'text');
        textLabel.setAttribute('x', point.x); textLabel.setAttribute('y', minY + 22); textLabel.setAttribute('class', `chart-label-text ${point.isSelected ? 'selected' : ''}`); textLabel.textContent = `${point.label} ${point.dayNum}${point.isToday ? ' (Dziś)' : ''}`; container.appendChild(textLabel);
        const valLabel = document.createElementNS(svgNS, 'text');
        valLabel.setAttribute('x', point.x); valLabel.setAttribute('y', point.y - 16); valLabel.setAttribute('class', `chart-val-text ${point.colorClass}`); valLabel.textContent = `${point.pct}%`; container.appendChild(valLabel);
        container.appendChild(link);
    });
}

function toggleEdit(taskId) {
    const editDiv = document.getElementById(`edit-form-${taskId}`);
    if (!editDiv) return;
    editDiv.classList.toggle('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
    renderCalendar();
    renderLineChart();
    loadReminders();
});
