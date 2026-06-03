let appData = {
    updated_at: "",
    events: [],
    reminders: [],
    ai_report: ""
};

let currentFilter = "all";
let searchQuery = "";
let currentView = "timeline";

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}

function init() {
    loadData();
    
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value.toLowerCase();
            renderDashboard();
        });
    }
}

async function loadData() {
    try {
        const response = await fetch("data.json?v=" + new Date().getTime());
        if (!response.ok) {
            throw new Error(`Failed to load data.json: ${response.status}`);
        }
        appData = await response.json();
        
        const updateTimeEl = document.getElementById("update-time");
        if (updateTimeEl) {
            updateTimeEl.textContent = `更新時間: ${appData.updated_at}`;
        }
        
        updateCounts();
        renderDashboard();
    } catch (error) {
        console.error("Error loading dashboard data:", error);
        
        const timelineEl = document.getElementById("event-timeline");
        const gridEl = document.getElementById("reminder-grid");
        
        if (timelineEl) {
            timelineEl.innerHTML = `<div class="loading-spinner">載入數據失敗。請確認是否已在 Synology NAS / 本機執行過 update_data.py，且生成了 data.json！<br><br><span style="color:var(--text-muted)">錯誤資訊: ${error.message}</span></div>`;
        }
        if (gridEl) {
            gridEl.innerHTML = `<div class="loading-spinner">無法讀取 Notion 備忘錄。</div>`;
        }
    }
}

function updateCounts() {
    const total = appData.events.length;
    const work = appData.events.filter(e => e.category === "work").length;
    const family = appData.events.filter(e => e.category === "family").length;
    const health = appData.events.filter(e => e.category === "health").length;
    const admin = appData.events.filter(e => e.category === "admin").length;
    
    document.getElementById("count-all").textContent = total;
    document.getElementById("count-work").textContent = work;
    document.getElementById("count-family").textContent = family;
    document.getElementById("count-health").textContent = health;
    document.getElementById("count-admin").textContent = admin;
}

function filterCategory(category) {
    if (currentView !== "timeline") {
        switchView("timeline");
    }
    
    currentFilter = category;
    
    const cards = document.querySelectorAll(".stat-card");
    cards.forEach(card => {
        card.classList.remove("active");
        if (card.classList.contains(category)) {
            card.classList.add("active");
        }
    });
    
    renderDashboard();
}

function switchView(viewName) {
    currentView = viewName;
    
    const btnTimeline = document.getElementById("btn-timeline");
    const btnAi = document.getElementById("btn-ai");
    const viewTimeline = document.getElementById("view-timeline");
    const viewAi = document.getElementById("view-ai");
    const statsSection = document.getElementById("stats-section");
    
    if (viewName === "timeline") {
        btnTimeline.classList.add("active");
        btnAi.classList.remove("active");
        viewTimeline.classList.remove("hidden");
        viewAi.classList.add("hidden");
        statsSection.classList.remove("hidden");
        renderTimeline();
    } else {
        btnTimeline.classList.remove("active");
        btnAi.classList.add("active");
        viewTimeline.classList.add("hidden");
        viewAi.classList.remove("hidden");
        statsSection.classList.add("hidden"); // Hide statistics card for distraction-free reading
        renderAiReport();
    }
}

function highlightReminder(reminderId) {
    const allReminders = document.querySelectorAll(".reminder-card");
    allReminders.forEach(r => r.classList.remove("highlighted"));
    
    if (!reminderId) return;
    
    const reminderCard = document.getElementById(`reminder-${reminderId}`);
    if (reminderCard) {
        reminderCard.classList.add("highlighted");
        reminderCard.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

function highlightEventByDependency(reminderId) {
    const events = document.querySelectorAll(".timeline-event");
    events.forEach(ev => ev.classList.remove("highlighted"));
    
    const matchingEvent = appData.events.find(e => 
        e.dependencies && e.dependencies.some(d => d.target_id === reminderId)
    );
    
    if (matchingEvent) {
        const evEl = document.getElementById(`event-${matchingEvent.id}`);
        if (evEl) {
            evEl.scrollIntoView({ behavior: "smooth", block: "center" });
            evEl.style.boxShadow = "0 0 20px rgba(0, 229, 255, 0.3)";
            setTimeout(() => {
                evEl.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.1)";
            }, 3000);
        }
    }
}

function renderDashboard() {
    if (currentView === "timeline") {
        renderTimeline();
        renderReminders();
    } else {
        renderAiReport();
    }
}

function renderTimeline() {
    const timelineEl = document.getElementById("event-timeline");
    if (!timelineEl) return;
    
    let filteredEvents = appData.events;
    if (currentFilter !== "all") {
        filteredEvents = filteredEvents.filter(e => e.category === currentFilter);
    }
    
    if (searchQuery) {
        filteredEvents = filteredEvents.filter(e => 
            e.title.toLowerCase().includes(searchQuery) || 
            (e.description && e.description.toLowerCase().includes(searchQuery))
        );
    }
    
    if (filteredEvents.length === 0) {
        timelineEl.innerHTML = `<div class="loading-spinner">沒有符合條件的事件。</div>`;
        return;
    }
    
    timelineEl.innerHTML = filteredEvents.map(ev => {
        const month = parseInt(ev.date.substring(5, 7));
        const day = parseInt(ev.date.substring(8, 10));
        const cleanDate = isNaN(month) ? ev.date : `${month}月${day}日`;
        
        let depHtml = "";
        if (ev.dependencies && ev.dependencies.length > 0) {
            depHtml = ev.dependencies.map(dep => `
                <div class="dependency-box" onclick="highlightReminder('${dep.target_id}'); event.stopPropagation();">
                    <span class="dep-label">🔗 關聯備忘提醒</span>
                    <span class="dep-text">${dep.text}</span>
                    <span class="dep-target">點擊查看備忘: "${dep.target_title.substring(0, 30)}..."</span>
                </div>
            `).join("");
        }
        
        return `
            <div class="timeline-event ${ev.category}" id="event-${ev.id}">
                <div class="event-header">
                    <div class="event-date-time">
                        <span>📅 ${cleanDate}</span>
                        ${ev.time !== "00:00" ? `<span>⏰ ${ev.time}</span>` : ""}
                    </div>
                    <div style="display:flex; gap:6px;">
                        <span class="badge badge-${ev.category}">${getCategoryChineseName(ev.category)}</span>
                        <span class="badge badge-source">${ev.source === "calendar" ? "📅 行事曆" : "📝 Notion"}</span>
                    </div>
                </div>
                <div class="event-title">${ev.title}</div>
                ${ev.description ? `<div class="event-description">${ev.description}</div>` : ""}
                ${depHtml}
            </div>
        `;
    }).join("");
}

function renderReminders() {
    const gridEl = document.getElementById("reminder-grid");
    if (!gridEl) return;
    
    let filteredReminders = appData.reminders;
    if (currentFilter !== "all") {
        filteredReminders = filteredReminders.filter(r => r.category === currentFilter);
    }
    
    if (searchQuery) {
        filteredReminders = filteredReminders.filter(r => 
            r.content.toLowerCase().includes(searchQuery)
        );
    }
    
    if (filteredReminders.length === 0) {
        gridEl.innerHTML = `<div class="loading-spinner">沒有符合條件的備忘筆記。</div>`;
        return;
    }
    
    gridEl.innerHTML = filteredReminders.map(rem => {
        return `
            <div class="reminder-card ${rem.category}" id="reminder-${rem.id}" onclick="highlightEventByDependency('${rem.id}')">
                <div class="reminder-header">
                    <span>分類: ${getCategoryChineseName(rem.category)}</span>
                    <span>建立時間: ${rem.created_time}</span>
                </div>
                <div class="reminder-content">${rem.content}</div>
            </div>
        `;
    }).join("");
}

function renderAiReport() {
    const aiReportEl = document.getElementById("ai-report-content");
    if (!aiReportEl) return;
    
    if (!appData.ai_report) {
        aiReportEl.innerHTML = `<div class="loading-spinner">沒有 AI 報告資料。請確認已在 '.env' 中設定 'GEMINI_API_KEY' 並重新執行了同步腳本！</div>`;
        return;
    }
    
    aiReportEl.innerHTML = parseMarkdown(appData.ai_report);
}

function getCategoryChineseName(cat) {
    switch (cat) {
        case "work": return "公務專案";
        case "family": return "家庭生活";
        case "health": return "健康醫療";
        case "admin": return "財務雜務";
        default: return "未分類";
    }
}

// Simple and robust line-by-line Markdown to HTML Parser
function parseMarkdown(md) {
    if (!md) return "無 AI 報告資料。";
    
    const lines = md.split('\n');
    let html = '';
    let inList = false;
    let inBlockquote = false;
    let inTable = false;
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        
        // Handle Tables
        if (line.startsWith('|')) {
            if (line.includes('---|') || line.includes('--|')) {
                continue; // Skip table header separator line
            }
            if (!inTable) {
                inTable = true;
                html += '<table>';
            }
            const cells = line.split('|').slice(1, -1).map(c => c.trim());
            const tag = html.endsWith('<table>') ? 'th' : 'td';
            html += '<tr>' + cells.map(c => `<${tag}>${formatInline(c)}</${tag}>`).join('') + '</tr>';
            continue;
        } else if (inTable) {
            inTable = false;
            html += '</table>';
        }
        
        // Handle Blockquote
        if (line.startsWith('>')) {
            if (!inBlockquote) {
                inBlockquote = true;
                html += '<blockquote>';
            }
            html += `<p>${formatInline(line.substring(1).trim())}</p>`;
            continue;
        } else if (inBlockquote) {
            inBlockquote = false;
            html += '</blockquote>';
        }
        
        // Handle Unordered Lists
        if (line.startsWith('- ') || line.startsWith('* ')) {
            if (!inList) {
                inList = true;
                html += '<ul>';
            }
            html += `<li>${formatInline(line.substring(2))}</li>`;
            continue;
        } else if (inList) {
            inList = false;
            html += '</ul>';
        }
        
        // Handle Headers
        if (line.startsWith('### ')) {
            html += `<h3>${formatInline(line.substring(4))}</h3>`;
        } else if (line.startsWith('## ')) {
            html += `<h2>${formatInline(line.substring(3))}</h2>`;
        } else if (line.startsWith('# ')) {
            html += `<h1>${formatInline(line.substring(2))}</h1>`;
        } else if (line === '') {
            continue;
        } else {
            html += `<p>${formatInline(line)}</p>`;
        }
    }
    
    // Close lingering tags
    if (inList) html += '</ul>';
    if (inBlockquote) html += '</blockquote>';
    if (inTable) html += '</table>';
    
    return html;
}

function formatInline(text) {
    // Bold **text**
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}
