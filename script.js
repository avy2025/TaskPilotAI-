let currentAbortController = null;
let lastReportMarkdown = "";
const sessionId = Math.random().toString(36).substring(2, 10);
let currentActiveTask = "";

// Time formatting helper
function timeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " minutes ago";
    return Math.floor(seconds) + " seconds ago";
}

async function runAgent(customTask = null) {
    const inputEl = document.getElementById('mission-input');
    const task = customTask || inputEl.value.trim();
    if (!task) return;
    
    if (!customTask) inputEl.value = task; // Normalize if from input
    currentActiveTask = task;

    const apiKey = sessionStorage.getItem('taskpilot_api_key') || "";
    
    // Reset UI
    const timeline = document.getElementById('timeline-container');
    const reportContent = document.getElementById('report-content');
    const sourcesContainer = document.getElementById('sources-container');
    const sourcesList = document.getElementById('sources-list');
    const loader = document.getElementById('status-indicator');
    const runBtn = document.getElementById('btn-run-agent');
    const stopBtn = document.getElementById('btn-stop-agent');
    const metricsFooter = document.getElementById('metrics-footer');
    
    timeline.innerHTML = '';
    sourcesContainer.style.display = 'none';
    sourcesList.innerHTML = '';
    reportContent.innerHTML = '<h2>Initializing Agent...</h2><p class="report-p">Assembling specialized agent swarm for your mission.</p>';
    loader.style.visibility = 'visible';
    runBtn.style.display = 'none';
    stopBtn.style.display = 'inline-block';
    metricsFooter.style.display = 'none';

    currentAbortController = new AbortController();

    try {
        const response = await fetch('/run-agent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                task, 
                session_id: sessionId,
                api_key: apiKey
            }),
            signal: currentAbortController.signal
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Server error");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (let line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const event = JSON.parse(line.substring(6));
                        handleEvent(event);
                    } catch (e) {
                        console.error("Parse error:", e);
                    }
                }
            }
        }
    } catch (e) {
        if (e.name === 'AbortError') {
            reportContent.innerHTML = `<h2>Stopped</h2><p>Execution halted by user.</p>`;
        } else {
            reportContent.innerHTML = `<h2 style="color:var(--text-error)">Error: ${e.message}</h2>`;
        }
    } finally {
        loader.style.visibility = 'hidden';
        runBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
        currentAbortController = null;
    }
}

function handleEvent(event) {
    if (event.type === 'step') {
        const timeline = document.getElementById('timeline-container');
        const now = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        let colorClass = 'step-1';
        if (event.name.toLowerCase().includes('research')) colorClass = 'step-2';
        if (event.name.toLowerCase().includes('code')) colorClass = 'step-3';
        if (event.name.toLowerCase().includes('content')) colorClass = 'step-1';

        timeline.innerHTML += `
            <div class="timeline-item">
                <div class="step-circle ${colorClass}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
                </div>
                <div class="step-card">
                    <div class="step-card-top"><div class="step-name">${event.name}</div><div class="step-time">${now}</div></div>
                    <div class="step-desc">${event.desc}</div>
                </div>
            </div>
        `;
        document.querySelector('.left-col').scrollTop = document.querySelector('.left-col').scrollHeight;
    } 
    else if (event.type === 'sources') {
        const container = document.getElementById('sources-container');
        const list = document.getElementById('sources-list');
        container.style.display = 'block';
        
        event.sources.forEach(src => {
            const card = document.createElement('a');
            card.href = src.url;
            card.target = "_blank";
            card.className = "source-card";
            card.style = "display:block; padding:10px; border:1px solid var(--border-color); border-radius:8px; text-decoration:none; background:var(--bg-card); transition:transform 0.2s;";
            card.innerHTML = `
                <div style="font-size:12px; font-weight:600; color:var(--text-primary); margin-bottom:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${src.title}</div>
                <div style="font-size:10px; color:var(--text-muted);">${src.origin} &rarr;</div>
            `;
            card.onmouseover = () => card.style.transform = "translateY(-2px)";
            card.onmouseout = () => card.style.transform = "translateY(0)";
            list.appendChild(card);
        });
    }
    else if (event.type === 'result') {
        const reportContent = document.getElementById('report-content');
        const metricsFooter = document.getElementById('metrics-footer');
        const tokenDisplay = document.getElementById('token-count');
        const sessionDisplay = document.getElementById('display-session-id');

        lastReportMarkdown = event.content;
        let html = marked.parse(event.content);
        reportContent.innerHTML = `
            <h1 class="report-h1">Agent Report</h1>
            <div class="report-subtitle">Secure Build &middot; Autonomous Synthesis</div>
            <div class="divider"></div>
            <div class="markdown-body">${DOMPurify.sanitize(html)}</div>
        `;
        
        tokenDisplay.textContent = event.tokens.toLocaleString();
        sessionDisplay.textContent = sessionId;
        metricsFooter.style.display = 'block';
        
        saveToHistory(currentActiveTask);
    }
}

function saveToHistory(task) {
    const history = JSON.parse(localStorage.getItem('taskpilot_history') || '[]');
    // Prevent duplicates if re-run immediately
    if (history.length > 0 && history[0].task === task) return;
    
    history.unshift({ task, timestamp: Date.now() });
    localStorage.setItem('taskpilot_history', JSON.stringify(history.slice(0, 10)));
    renderSidebar();
}

function renderSidebar() {
    const list = document.getElementById('sidebar-list');
    const history = JSON.parse(localStorage.getItem('taskpilot_history') || '[]');
    
    if (history.length === 0) {
        list.innerHTML = '<p class="empty-state">No history yet.</p>';
        return;
    }

    list.innerHTML = history.map(item => `
        <div class="history-item-mini" onclick="runAgent('${item.task.replace(/'/g, "\\'")}')">
            <div class="hi-mini-title">${item.task.substring(0, 60)}${item.task.length > 60 ? '...' : ''}</div>
            <div class="hi-mini-time">${timeAgo(item.timestamp)}</div>
        </div>
    `).join('');
}

document.addEventListener("DOMContentLoaded", () => {
    // API KEY LOGIC
    const keyInput = document.getElementById('input-api-key');
    const toggleView = document.getElementById('toggle-key-view');
    const settingsBtn = document.getElementById('btn-settings');
    const settingsPanel = document.getElementById('settings-panel');

    keyInput.value = sessionStorage.getItem('taskpilot_api_key') || "";
    keyInput.addEventListener('input', () => sessionStorage.setItem('taskpilot_api_key', keyInput.value));
    
    toggleView.addEventListener('click', () => {
        keyInput.type = keyInput.type === 'password' ? 'text' : 'password';
        toggleView.textContent = keyInput.type === 'password' ? '👁️' : '🔒';
    });

    settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        settingsPanel.classList.toggle('active');
    });

    document.addEventListener('click', () => settingsPanel.classList.remove('active'));
    settingsPanel.addEventListener('click', (e) => e.stopPropagation());

    // SIDEBAR LOGIC
    const sidebar = document.getElementById('sidebar-history');
    const wrapper = document.getElementById('main-wrapper');
    const toggleSidebar = document.getElementById('btn-toggle-sidebar');
    const closeSidebar = document.getElementById('close-sidebar');

    toggleSidebar.addEventListener('click', () => {
        sidebar.classList.toggle('active');
        wrapper.classList.toggle('sidebar-active');
    });
    closeSidebar.addEventListener('click', () => {
        sidebar.classList.remove('active');
        wrapper.classList.remove('sidebar-active');
    });

    // CHAR COUNTER
    const textarea = document.getElementById('mission-input');
    const counter = document.getElementById('char-counter');
    textarea.addEventListener('input', () => {
        const len = textarea.value.length;
        counter.textContent = `${len} / 2000`;
        counter.style.color = len > 1800 ? '#EF4444' : '';
    });

    // RUN/STOP
    document.getElementById('btn-run-agent').addEventListener('click', () => runAgent());
    document.getElementById('btn-stop-agent').addEventListener('click', () => currentAbortController?.abort());
    
    document.getElementById('btn-copy-report').addEventListener('click', () => {
        navigator.clipboard.writeText(lastReportMarkdown);
        alert('Report copied!');
    });

    // INIT
    renderSidebar();
});
