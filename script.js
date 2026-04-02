let currentAbortController = null;
const sessionId = Math.random().toString(36).substring(2, 15);

async function runAgent() {
    const inputEl = document.getElementById('mission-input');
    const task = inputEl.value.trim();
    if (!task) return;

    stepCount = 0;
    // Reset UI
    const timeline = document.getElementById('timeline-container');
    const reportContent = document.getElementById('report-content');
    const loader = document.getElementById('status-indicator');
    const runBtn = document.getElementById('btn-run-agent');
    const stopBtn = document.getElementById('btn-stop-agent');
    
    timeline.innerHTML = '';
    reportContent.innerHTML = '<h2>Initializing Agent...</h2><p class="report-p">Waiting for task execution to complete.</p>';
    loader.style.visibility = 'visible';
    runBtn.style.display = 'none';
    stopBtn.style.display = 'inline-block';

    currentAbortController = new AbortController();

    try {
        const response = await fetch('/run-agent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task, session_id: sessionId }),
            signal: currentAbortController.signal
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep remainder

            for (let line of lines) {
                if (line.trim() === '') continue;
                try {
                    let jsonStr = line;
                    if (line.startsWith('data: ')) {
                        jsonStr = line.substring(6).trim();
                    }
                    if (!jsonStr) continue;
                    const event = JSON.parse(jsonStr);
                    handleEvent(event);
                } catch (e) {
                    console.error("Parse error:", e, line);
                }
            }
        }
    } catch (e) {
        if (e.name === 'AbortError') {
            console.log("Agent execution stopped by user.");
            reportContent.innerHTML = `<h2>Execution Stopped</h2><p class="report-p">The agent was manually stopped.</p>`;
        } else {
            console.error("Stream error:", e);
            reportContent.innerHTML = `<h2 style="color:red">Error submitting request: ${e.message}</h2>`;
        }
    } finally {
        loader.style.visibility = 'hidden';
        runBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
        currentAbortController = null;
    }
}

let stepCount = 0;
function handleEvent(event) {
    if (event.type === 'step') {
        stepCount++;
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const timeline = document.getElementById('timeline-container');
        
        let colorClass = stepCount % 3 === 1 ? 'step-1' : (stepCount % 3 === 2 ? 'step-2' : 'step-3');

        // Optional: you could make SVG icon dynamic based on the tool.
        timeline.innerHTML += `
            <div class="timeline-item">
            <div class="step-circle ${colorClass}">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </div>
            <div class="step-line active"><div class="flowing-dashes"></div></div>
            <div class="step-card">
              <div class="step-card-top">
                <div class="step-name">${event.name}</div>
                <div class="step-time">${timeStr}</div>
              </div>
              <div class="step-desc">${event.desc}</div>
            </div>
          </div>
        `;
        // Auto scroll to bottom of left-col
        const leftCol = document.querySelector('.left-col');
        leftCol.scrollTop = leftCol.scrollHeight;
    } else if (event.type === 'result') {
        const reportContent = document.getElementById('report-content');
        
        // Use external markdown parser and sanitize with DOMPurify
        let rawHtml = typeof marked !== 'undefined' ? marked.parse(event.content) : `<pre style="white-space:pre-wrap; font-family:inherit;">${event.content}</pre>`;
        let htmlRendered = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(rawHtml) : rawHtml;
        
        reportContent.innerHTML = `
            <h1 class="report-h1">Agent Report</h1>
            <div class="report-subtitle">Generated just now &middot; 🔒 Encrypted</div>
            <div class="divider"></div>
            <div style="font-size: 14px; line-height: 1.75; color: var(--text-secondary); margin-bottom: 24px;">
                ${htmlRendered}
            </div>
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="metric-label">CONFIDENCE SCORE</div>
                <div class="metric-value text-gradient">${event.confidence || '99.9%'}</div>
                <div class="progress-track">
                  <div class="progress-fill" style="width: ${event.confidence || '99.9%'}"></div>
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">TOKENS USED</div>
                <div class="metric-value">${event.tokens || 0}</div>
                <div class="metric-sub">Optimised for Gemini 1.5 Flash</div>
              </div>
            </div>
        `;
    } else if (event.type === 'error') {
        const reportContent = document.getElementById('report-content');
        reportContent.innerHTML = `<h2 style="color:red">Backend Error</h2><p>${event.message}</p>`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const runBtn = document.getElementById('btn-run-agent');
    if(runBtn) {
        runBtn.addEventListener('click', runAgent);
    }

    const stopBtn = document.getElementById('btn-stop-agent');
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            if (currentAbortController) {
                currentAbortController.abort();
            }
        });
    }
    
    const textarea = document.getElementById('mission-input');
    const charCount = document.querySelector('.char-count');
    if (textarea && charCount) {
      textarea.addEventListener('input', () => {
        const len = textarea.value.length;
        charCount.textContent = len + ' / 500';
        if (len > 500) {
          charCount.style.color = '#DC2626';
        } else {
          charCount.style.color = '';
        }
      });
    }

    if (textarea) {
      textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
          runAgent();
        }
      });
    }
});
