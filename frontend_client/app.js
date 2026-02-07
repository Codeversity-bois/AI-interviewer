const API_BASE = 'http://localhost:8001';
const WS_BASE = 'ws://localhost:8001';

const state = {
    userId: 'candidate-001',
    sessionId: null,
    ws: null,
    videoWs: null,
    videoStream: null,
    audioStream: null,
    mediaRecorder: null,
    isRecording: false,
    frameInterval: null,
};

// DOM Elements
const elements = {
    sections: {
        resume: document.getElementById('resume-section'),
        setup: document.getElementById('setup-section'),
        interview: document.getElementById('interview-section'),
        summary: document.getElementById('summary-section'),
    },
    // Resume JSON form
    resumeName: document.getElementById('resume-name'),
    resumeExperience: document.getElementById('resume-experience'),
    resumeSkills: document.getElementById('resume-skills'),
    resumeProjects: document.getElementById('resume-projects'),
    resumeEducation: document.getElementById('resume-education'),
    processBtn: document.getElementById('btn-process-resume'),
    loading: document.getElementById('resume-loading'),
    // Setup
    userId: document.getElementById('user-id'),
    chunksCount: document.getElementById('chunks-count'),
    startBtn: document.getElementById('btn-start-interview'),
    // Interview
    chatMessages: document.getElementById('chat-messages'),
    userInput: document.getElementById('user-input'),
    sendBtn: document.getElementById('btn-send-text'),
    micBtn: document.getElementById('btn-mic'),
    endBtn: document.getElementById('btn-end-interview'),
    phaseDisplay: document.getElementById('interview-phase'),
    // Video
    videoPreview: document.getElementById('webcam-preview'),
    violationLog: document.getElementById('violation-log'),
    // Summary
    summaryStats: document.getElementById('summary-stats'),
    summaryQA: document.getElementById('summary-qa'),
    summaryContent: document.getElementById('summary-content'),
    toggleRawBtn: document.getElementById('btn-toggle-raw'),
    restartBtn: document.getElementById('btn-restart'),
    // Header
    connectionStatus: document.getElementById('connection-status'),
    statusText: document.getElementById('status-text'),
};

// --- Initialization ---
function init() {
    setupResumeForm();
    setupInterviewControls();
    elements.restartBtn.addEventListener('click', () => location.reload());
    elements.toggleRawBtn.addEventListener('click', toggleRawSummary);
    checkBackendHealth();
    setInterval(checkBackendHealth, 30000);
}

async function checkBackendHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) {
            updateStatus(true, 'Backend Connected');
        } else {
            updateStatus(false, 'Backend Error');
        }
    } catch (e) {
        updateStatus(false, 'Backend Unreachable');
    }
}

// --- Navigation ---
function showSection(sectionName) {
    Object.values(elements.sections).forEach(el => {
        el.classList.remove('active-section');
        el.classList.add('hidden-section');
    });
    elements.sections[sectionName].classList.remove('hidden-section');
    elements.sections[sectionName].classList.add('active-section');
}

function updateStatus(connected, text) {
    elements.connectionStatus.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
    elements.statusText.textContent = text;
}

// --- Resume JSON Form ---
function setupResumeForm() {
    elements.processBtn.addEventListener('click', async () => {
        const sections = {};
        const experience = elements.resumeExperience.value.trim();
        const skills = elements.resumeSkills.value.trim();
        const projects = elements.resumeProjects.value.trim();
        const education = elements.resumeEducation.value.trim();
        const username = elements.resumeName.value.trim() || 'candidate';

        if (experience) sections.experience = experience;
        if (skills) sections.skills = skills;
        if (projects) sections.projects = projects;
        if (education) sections.education = education;

        if (Object.keys(sections).length === 0) {
            alert('Please fill in at least one section.');
            return;
        }

        elements.loading.classList.remove('hidden');
        elements.processBtn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/resume/process`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, sections }),
            });
            const data = await res.json();

            if (data.success) {
                state.userId = data.user_id || state.userId;
                elements.userId.value = state.userId;
                elements.chunksCount.textContent = data.chunks_processed || 0;
                showSection('setup');
            } else {
                alert('Error: ' + data.message);
            }
        } catch (e) {
            console.error(e);
            alert('Failed to connect to backend.');
        } finally {
            elements.loading.classList.add('hidden');
            elements.processBtn.disabled = false;
        }
    });
}

// --- Interview Control ---
function setupInterviewControls() {
    elements.startBtn.addEventListener('click', startInterview);
    elements.sendBtn.addEventListener('click', () => sendUserMessage());
    elements.userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendUserMessage();
    });
    elements.endBtn.addEventListener('click', endInterview);

    // Mic button: click to toggle recording
    elements.micBtn.addEventListener('click', toggleMicRecording);
}

async function startInterview() {
    const userId = elements.userId.value;

    try {
        const res = await fetch(`${API_BASE}/interview/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                resume_context: 'Resume processed and stored in vector DB.',
            }),
        });

        const data = await res.json();

        if (data.success) {
            state.sessionId = data.session_id;
            connectWebSocket(data.ws_url);
            startVideoProctoring();
            showSection('interview');
            updateStatus(true, 'Interview Active');
        } else {
            alert('Failed to start interview: ' + data.message);
        }
    } catch (e) {
        console.error(e);
        alert('Error starting interview.');
    }
}

// --- WebSocket & Chat ---
function connectWebSocket(path) {
    state.ws = new WebSocket(`${WS_BASE}${path}`);

    state.ws.onopen = () => {
        console.log('WS Connected');
        updateStatus(true, 'Connected to Zenith');
    };

    state.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleWsMessage(msg);
    };

    state.ws.onclose = () => {
        console.log('WS Closed');
        updateStatus(false, 'Disconnected');
    };

    state.ws.onerror = (e) => {
        console.error('WS Error', e);
        updateStatus(false, 'Connection Error');
    };
}

function handleWsMessage(msg) {
    if (msg.type === 'ai_message') {
        appendMessage('ai', msg.text);
        if (msg.phase) {
            elements.phaseDisplay.textContent = formatPhase(msg.phase);
        }
    } else if (msg.type === 'backchannel') {
        appendMessage('backchannel', msg.text);
    } else if (msg.type === 'interview_ended') {
        showSummary(msg.summary);
    } else if (msg.type === 'violation') {
        logViolation(msg);
    } else if (msg.type === 'error') {
        console.error('Server Error:', msg.message);
    }
}

function formatPhase(phase) {
    return phase.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function sendUserMessage() {
    const text = elements.userInput.value.trim();
    if (!text || !state.ws) return;

    appendMessage('user', text);
    state.ws.send(JSON.stringify({ type: 'user_text', text }));
    elements.userInput.value = '';
}

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    if (role === 'backchannel') {
        div.innerHTML = `
            <div class="avatar">Z</div>
            <div class="content backchannel-text">${escapeHtml(text)}</div>
        `;
    } else {
        const avatar = role === 'ai' ? 'Z' : 'Me';
        div.innerHTML = `
            <div class="avatar">${avatar}</div>
            <div class="content">${escapeHtml(text)}</div>
        `;
    }

    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// --- Mic Recording (STT) ---
async function toggleMicRecording() {
    if (state.isRecording) {
        stopMicRecording();
    } else {
        await startMicRecording();
    }
}

async function startMicRecording() {
    try {
        state.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.mediaRecorder = new MediaRecorder(state.audioStream, { mimeType: 'audio/webm' });
        const chunks = [];

        state.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) chunks.push(e.data);
        };

        state.mediaRecorder.onstop = async () => {
            const blob = new Blob(chunks, { type: 'audio/webm' });
            await transcribeAndSend(blob);
        };

        state.mediaRecorder.start();
        state.isRecording = true;
        elements.micBtn.classList.add('recording');
        elements.micBtn.title = 'Click to stop';
    } catch (e) {
        console.error('Mic access denied:', e);
        alert('Microphone access is required for voice input.');
    }
}

function stopMicRecording() {
    if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') {
        state.mediaRecorder.stop();
    }
    if (state.audioStream) {
        state.audioStream.getTracks().forEach(t => t.stop());
        state.audioStream = null;
    }
    state.isRecording = false;
    elements.micBtn.classList.remove('recording');
    elements.micBtn.title = 'Click to speak';
}

async function transcribeAndSend(audioBlob) {
    // Send to /transcribe endpoint for STT
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');

    try {
        appendMessage('user', '(transcribing audio...)');
        const res = await fetch(`${API_BASE}/transcribe`, {
            method: 'POST',
            body: formData,
        });

        if (res.ok) {
            const data = await res.json();
            const transcript = data.transcript || '';
            if (transcript.trim()) {
                // Remove the "transcribing" placeholder
                const msgs = elements.chatMessages.querySelectorAll('.message.user');
                const last = msgs[msgs.length - 1];
                if (last && last.textContent.includes('transcribing audio')) {
                    last.querySelector('.content').textContent = transcript;
                }
                // Send transcribed text to interview WS
                if (state.ws) {
                    state.ws.send(JSON.stringify({ type: 'user_text', text: transcript }));
                }
            } else {
                // Remove placeholder if no transcript
                const msgs = elements.chatMessages.querySelectorAll('.message.user');
                const last = msgs[msgs.length - 1];
                if (last && last.textContent.includes('transcribing audio')) {
                    last.remove();
                }
            }
        } else {
            console.error('STT failed:', res.status);
            // Remove placeholder
            const msgs = elements.chatMessages.querySelectorAll('.message.user');
            const last = msgs[msgs.length - 1];
            if (last && last.textContent.includes('transcribing audio')) {
                last.querySelector('.content').textContent = '(voice input failed)';
            }
        }
    } catch (e) {
        console.error('STT error:', e);
    }
}

// --- Video Proctoring ---
async function startVideoProctoring() {
    try {
        state.videoStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        elements.videoPreview.srcObject = state.videoStream;

        const videoWsUrl = `${WS_BASE}/interview/${state.sessionId}/video`;
        state.videoWs = new WebSocket(videoWsUrl);

        state.videoWs.onopen = () => {
            console.log('Video WS Connected');
            startFrameSending();
        };

        state.videoWs.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.violations && data.violations.length > 0) {
                data.violations.forEach(v => logViolation(v));
            }
        };
    } catch (e) {
        console.error('Video access denied or error:', e);
    }
}

function startFrameSending() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    state.frameInterval = setInterval(() => {
        if (state.videoWs && state.videoWs.readyState === WebSocket.OPEN && elements.videoPreview.readyState === 4) {
            canvas.width = 320;
            canvas.height = 240;
            ctx.drawImage(elements.videoPreview, 0, 0, canvas.width, canvas.height);
            const base64Data = canvas.toDataURL('image/jpeg', 0.6);
            state.videoWs.send(base64Data);
        }
    }, 500);
}

function logViolation(v) {
    const div = document.createElement('div');
    div.className = 'violation-item';
    div.innerHTML = `<strong>${escapeHtml(v.violation_type || v.type)}</strong>: ${escapeHtml(v.message)}`;
    elements.violationLog.prepend(div);
}

// --- End Interview ---
async function endInterview() {
    if (!state.sessionId) return;

    if (state.ws) state.ws.close();
    if (state.videoWs) state.videoWs.close();
    if (state.videoStream) state.videoStream.getTracks().forEach(t => t.stop());
    if (state.frameInterval) clearInterval(state.frameInterval);
    stopMicRecording();

    try {
        const res = await fetch(`${API_BASE}/interview/${state.sessionId}/end`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showSummary(data.summary);
        }
    } catch (e) {
        console.error(e);
    }
}

// --- Summary ---
function showSummary(summary) {
    showSection('summary');
    updateStatus(false, 'Interview Ended');

    // Render high-level stats
    const stats = summary || {};
    elements.summaryStats.innerHTML = `
        <div class="stat-row">
            <span class="stat-label">Duration</span>
            <span class="stat-value">${stats.duration_mins || '—'} min</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Questions Asked</span>
            <span class="stat-value">${stats.total_questions || '—'}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Phases Completed</span>
            <span class="stat-value">${(stats.phases_completed || []).map(formatPhase).join(', ') || '—'}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Violations</span>
            <span class="stat-value">${stats.violation_count || 0}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Avg. Attention</span>
            <span class="stat-value">${stats.avg_attention_score != null ? (stats.avg_attention_score * 100).toFixed(0) + '%' : '—'}</span>
        </div>
    `;

    // Render Q&A history
    const qaList = stats.qa_history || [];
    if (qaList.length > 0) {
        elements.summaryQA.innerHTML = '<h3>Q&A History</h3>' + qaList.map((qa, i) => `
            <div class="qa-item">
                <div class="qa-question"><strong>Q${i + 1}:</strong> ${escapeHtml(qa.question || '')}</div>
                <div class="qa-answer"><strong>A:</strong> ${escapeHtml(qa.answer || '(no answer)')}</div>
            </div>
        `).join('');
    }

    // Raw JSON
    elements.summaryContent.textContent = JSON.stringify(summary, null, 2);
}

function toggleRawSummary() {
    elements.summaryContent.classList.toggle('hidden');
    elements.toggleRawBtn.textContent =
        elements.summaryContent.classList.contains('hidden') ? 'Show Raw Data' : 'Hide Raw Data';
}

// Start
document.addEventListener('DOMContentLoaded', init);
