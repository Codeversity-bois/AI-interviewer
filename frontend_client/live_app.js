/**
 * Gemini Live Interview — Frontend
 *
 * Streams mic audio (16kHz PCM) to the backend WebSocket proxy,
 * which forwards it to Gemini Live API. Audio responses (24kHz PCM)
 * come back and are played through speakers via Web Audio API.
 */

const WS_BASE = 'ws://localhost:8000';

const SEND_SAMPLE_RATE = 16000;
const RECEIVE_SAMPLE_RATE = 24000;

// State
const state = {
    ws: null,
    audioCtx: null,
    micStream: null,
    micProcessor: null,
    isMuted: false,
    transcript: [],       // {role, text} for end-of-interview display
    currentAiText: '',    // accumulates AI transcript chunks
};

// DOM
const els = {
    sections: {
        setup: document.getElementById('setup-section'),
        live: document.getElementById('live-section'),
        done: document.getElementById('done-section'),
    },
    resumeContext: document.getElementById('resume-context'),
    startBtn: document.getElementById('btn-start'),
    setupLoading: document.getElementById('setup-loading'),
    chatMessages: document.getElementById('chat-messages'),
    liveStatus: document.getElementById('live-status'),
    micBtn: document.getElementById('btn-mic'),
    endBtn: document.getElementById('btn-end'),
    restartBtn: document.getElementById('btn-restart'),
    transcriptLog: document.getElementById('transcript-log'),
    visualizer: document.getElementById('audio-visualizer'),
    connectionStatus: document.getElementById('connection-status'),
    statusText: document.getElementById('status-text'),
};

// ── Initialization ───────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    els.startBtn.addEventListener('click', startLiveInterview);
    els.micBtn.addEventListener('click', toggleMute);
    els.endBtn.addEventListener('click', endInterview);
    els.restartBtn.addEventListener('click', () => location.reload());
});

function showSection(name) {
    Object.values(els.sections).forEach(el => {
        el.classList.remove('active-section');
        el.classList.add('hidden-section');
    });
    els.sections[name].classList.remove('hidden-section');
    els.sections[name].classList.add('active-section');
}

function setStatus(connected, text) {
    els.connectionStatus.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
    els.statusText.textContent = text;
}

// ── Start Interview ──────────────────────────────────────────────────────────

async function startLiveInterview() {
    els.startBtn.disabled = true;
    els.setupLoading.classList.remove('hidden');

    try {
        // 1. Open WebSocket to backend proxy
        state.ws = new WebSocket(`${WS_BASE}/interview/live`);
        state.ws.binaryType = 'arraybuffer';

        await new Promise((resolve, reject) => {
            state.ws.onopen = resolve;
            state.ws.onerror = () => reject(new Error('WebSocket connection failed'));
            setTimeout(() => reject(new Error('Connection timeout')), 10000);
        });

        // 2. Send config
        state.ws.send(JSON.stringify({
            type: 'config',
            resume_context: els.resumeContext.value.trim(),
        }));

        // 3. Wait for "ready" from server
        await new Promise((resolve, reject) => {
            state.ws.onmessage = (event) => {
                if (typeof event.data === 'string') {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'ready') resolve();
                    else if (msg.type === 'error') reject(new Error(msg.message));
                }
            };
            setTimeout(() => reject(new Error('Gemini connection timeout')), 30000);
        });

        // 4. Set up the full message handler
        state.ws.onmessage = handleServerMessage;
        state.ws.onclose = () => {
            setStatus(false, 'Disconnected');
        };

        // 5. Start mic capture
        await startMicCapture();

        // 6. Switch to live view
        showSection('live');
        setStatus(true, 'Live — Speak now');
        els.liveStatus.textContent = 'Listening';

    } catch (err) {
        console.error('Start failed:', err);
        alert('Failed to start: ' + err.message);
        if (state.ws) state.ws.close();
    } finally {
        els.startBtn.disabled = false;
        els.setupLoading.classList.add('hidden');
    }
}

// ── WebSocket message handler ────────────────────────────────────────────────

function handleServerMessage(event) {
    if (event.data instanceof ArrayBuffer) {
        // Binary = PCM audio from Gemini — play it
        playAudioChunk(event.data);
        return;
    }

    // Text = JSON control message
    const msg = JSON.parse(event.data);

    if (msg.type === 'transcript') {
        // Gemini's text transcript of what it said
        state.currentAiText += msg.text;
        appendOrUpdateAiMessage(state.currentAiText);
    } else if (msg.type === 'turn_complete') {
        // AI finished speaking
        if (state.currentAiText.trim()) {
            state.transcript.push({ role: 'ai', text: state.currentAiText.trim() });
        }
        state.currentAiText = '';
        currentAiMsgEl = null;
        els.liveStatus.textContent = 'Listening';
    } else if (msg.type === 'error') {
        console.error('Server error:', msg.message);
        appendSystemMessage('Error: ' + msg.message);
    }
}

// ── Audio Playback via Web Audio API ─────────────────────────────────────────

function ensureAudioContext() {
    if (!state.audioCtx) {
        state.audioCtx = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: RECEIVE_SAMPLE_RATE,
        });
    }
    if (state.audioCtx.state === 'suspended') {
        state.audioCtx.resume();
    }
}

let nextPlayTime = 0;

function playAudioChunk(arrayBuffer) {
    ensureAudioContext();
    els.liveStatus.textContent = 'Zenith speaking...';

    const ctx = state.audioCtx;
    const int16 = new Int16Array(arrayBuffer);
    const float32 = new Float32Array(int16.length);

    // Convert Int16 PCM to Float32 for Web Audio
    for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768;
    }

    const buffer = ctx.createBuffer(1, float32.length, RECEIVE_SAMPLE_RATE);
    buffer.getChannelData(0).set(float32);

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    // Schedule playback sequentially to avoid gaps
    const now = ctx.currentTime;
    if (nextPlayTime < now) {
        nextPlayTime = now;
    }
    source.start(nextPlayTime);
    nextPlayTime += buffer.duration;
}

// ── Mic Capture ──────────────────────────────────────────────────────────────

async function startMicCapture() {
    state.micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
            sampleRate: SEND_SAMPLE_RATE,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
        }
    });

    // Use AudioContext + ScriptProcessor to get raw PCM
    const micCtx = new AudioContext({ sampleRate: SEND_SAMPLE_RATE });
    const source = micCtx.createMediaStreamSource(state.micStream);

    // ScriptProcessor: 4096 buffer, 1 input channel, 1 output channel
    const processor = micCtx.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
        if (state.isMuted || !state.ws || state.ws.readyState !== WebSocket.OPEN) return;

        const float32 = e.inputBuffer.getChannelData(0);

        // Convert Float32 [-1,1] to Int16 PCM
        const int16 = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i]));
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        state.ws.send(int16.buffer);

        // Update visualizer
        drawVisualizer(float32);
    };

    source.connect(processor);
    processor.connect(micCtx.destination); // required for processing to work

    state.micProcessor = { processor, source, context: micCtx };
}

// ── Visualizer ───────────────────────────────────────────────────────────────

function drawVisualizer(float32) {
    const canvas = els.visualizer;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;

    const step = Math.floor(float32.length / w);
    for (let i = 0; i < w; i++) {
        const val = float32[i * step] || 0;
        const y = (val + 1) / 2 * h;
        if (i === 0) ctx.moveTo(i, y);
        else ctx.lineTo(i, y);
    }
    ctx.stroke();
}

// ── Mute Toggle ──────────────────────────────────────────────────────────────

function toggleMute() {
    state.isMuted = !state.isMuted;
    els.micBtn.className = `mic-btn ${state.isMuted ? 'muted' : 'active'}`;
    els.micBtn.querySelector('.mic-label').textContent = state.isMuted ? 'Muted' : 'Mic Active';
}

// ── Chat Display ─────────────────────────────────────────────────────────────

let currentAiMsgEl = null;

function appendOrUpdateAiMessage(text) {
    if (!currentAiMsgEl) {
        currentAiMsgEl = document.createElement('div');
        currentAiMsgEl.className = 'message ai';
        currentAiMsgEl.innerHTML = `
            <div class="avatar">Z</div>
            <div class="content"></div>
        `;
        els.chatMessages.appendChild(currentAiMsgEl);
    }
    currentAiMsgEl.querySelector('.content').textContent = text;
    els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
}

function appendSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'message backchannel';
    div.innerHTML = `<div class="avatar">!</div><div class="content backchannel-text">${escapeHtml(text)}</div>`;
    els.chatMessages.appendChild(div);
    els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ── End Interview ────────────────────────────────────────────────────────────

function endInterview() {
    // Send end signal
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ type: 'end' }));
        state.ws.close();
    }

    // Stop mic
    if (state.micStream) {
        state.micStream.getTracks().forEach(t => t.stop());
    }
    if (state.micProcessor) {
        state.micProcessor.processor.disconnect();
        state.micProcessor.source.disconnect();
        state.micProcessor.context.close();
    }

    // Show transcript
    showSection('done');
    setStatus(false, 'Interview Ended');

    const log = els.transcriptLog;
    if (state.transcript.length === 0) {
        log.innerHTML = '<p style="color:var(--text-muted)">No transcript recorded.</p>';
    } else {
        log.innerHTML = state.transcript.map(entry => {
            return `<div class="transcript-entry ${entry.role}">${escapeHtml(entry.text)}</div>`;
        }).join('');
    }
}
