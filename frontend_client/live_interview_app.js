/**
 * Live Interview Frontend — connects to the live_interview_service microservice.
 *
 * Streams mic PCM to /session/{id}/live WebSocket.
 * Streams webcam frames to /session/{id}/video WebSocket.
 * Receives audio + evaluation + proctoring updates.
 */

const API_BASE = 'http://localhost:8001';
const WS_BASE = 'ws://localhost:8001';

const SEND_SAMPLE_RATE = 16000;
const RECEIVE_SAMPLE_RATE = 24000;

const state = {
    sessionId: null,
    wsAudio: null,
    wsVideo: null,
    audioCtx: null,
    micStream: null,
    micProcessor: null,
    videoStream: null, // Webcam stream
    isMuted: false,
    transcript: [],
    currentAiText: '',
    evaluation: null,
    timerInterval: null,
    startTime: null,
};

// ── DOM ──────────────────────────────────────────────────────────────────────

const els = {
    sections: {
        input: document.getElementById('input-section'),
        live: document.getElementById('live-section'),
        results: document.getElementById('results-section'),
    },
    // Setup controls
    startBtn: document.getElementById('btn-start'),
    setupLoading: document.getElementById('setup-loading'),
    addProjectBtn: document.getElementById('btn-add-project'),
    projectsContainer: document.getElementById('projects-container'),
    
    // Live controls
    liveStatusText: document.getElementById('live-status-text'),
    micBtn: document.getElementById('btn-mic'), // Footer mic
    endBtn: document.getElementById('btn-end'), // Footer end
    micIndicator: document.getElementById('mic-status-indicator'),
    connectionDot: document.getElementById('connection-dot'),
    sessionTimer: document.getElementById('session-timer'),
    liveControls: document.getElementById('live-controls'),
    displaySessionId: document.getElementById('display-session-id'),
    
    // Visuals
    captionsBox: document.getElementById('captions-box'),
    miniVisualizer: document.getElementById('mini-visualizer'),
    
    // Video / Proctoring
    userVideo: document.getElementById('user-video'),
    videoCanvas: document.getElementById('video-canvas'),
    camStatus: document.getElementById('cam-status-indicator'),
    videoOverlay: document.getElementById('video-overlay-alert'),
    videoAlertMsg: document.getElementById('video-alert-msg'),
    statusLog: document.getElementById('status-log'),
    
    // Results
    restartBtn: document.getElementById('btn-restart'),
    resOverall: document.getElementById('res-overall'),
    resTech: document.getElementById('res-tech'),
    resComm: document.getElementById('res-comm'),
    resRec: document.getElementById('res-rec'),
    finalTranscript: document.getElementById('final-transcript'),
};

// ── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    els.startBtn.addEventListener('click', startInterview);
    els.micBtn.addEventListener('click', toggleMute);
    els.endBtn.addEventListener('click', endInterview);
    els.restartBtn.addEventListener('click', () => location.reload());
    els.addProjectBtn.addEventListener('click', addProjectField);
    
    // Load example data button
    const loadExampleBtn = document.getElementById('btn-load-example');
    if (loadExampleBtn) {
        loadExampleBtn.addEventListener('click', async () => {
            await loadExampleData();
        });
    }
    
    // Load example data automatically on page load
    await loadExampleData();
});

function showSection(name) {
    Object.values(els.sections).forEach(el => {
        el.classList.remove('active-section');
        el.classList.add('hidden-section');
    });
    els.sections[name].classList.remove('hidden-section');
    els.sections[name].classList.add('active-section');
}

function setConnected(isConnected) {
    els.connectionDot.className = `w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`;
    if (isConnected) {
        els.liveControls.classList.remove('opacity-50', 'pointer-events-none');
    } else {
        els.liveControls.classList.add('opacity-50', 'pointer-events-none');
    }
}

function addProjectField(projectData = null) {
    const div = document.createElement('div');
    div.className = 'project-entry mb-4 p-4 bg-background-dark border border-slate-700 rounded-lg';
    div.innerHTML = `
         <textarea class="proj-desc w-full bg-transparent border-none focus:ring-0 text-sm mb-2" rows="2" placeholder="Project description...">${projectData?.description || ''}</textarea>
         <input type="text" class="proj-skills w-full bg-slate-800 border border-slate-600 rounded px-3 py-1 text-sm" placeholder="Technologies used" value="${projectData?.skills || ''}">
    `;
    els.projectsContainer.appendChild(div);
}

// ── Load Example Data ────────────────────────────────────────────────────────

async function loadExampleData() {
    try {
        const response = await fetch('example_input.json');
        if (!response.ok) {
            console.warn('Could not load example_input.json, using defaults');
            hideExampleIndicator();
            return;
        }
        
        const data = await response.json();
        
        // Populate form fields
        document.getElementById('inp-candidate-id').value = data.candidate_id || '';
        document.getElementById('inp-job-id').value = data.job_id || '';
        document.getElementById('inp-job-desc').value = data.job_description || '';
        document.getElementById('inp-skills').value = Array.isArray(data.skills) ? data.skills.join(', ') : (data.skills || '');
        document.getElementById('inp-education').value = data.education || '';
        document.getElementById('inp-leetcode').value = data.leetcode_profile || '';
        
        // Clear existing projects and add from JSON
        els.projectsContainer.innerHTML = '';
        if (data.projects && Array.isArray(data.projects) && data.projects.length > 0) {
            data.projects.forEach(project => {
                addProjectField(project);
            });
        } else {
            // Add one empty project field if none provided
            addProjectField();
        }
        
        showExampleIndicator();
        console.log('✅ Example data loaded successfully');
    } catch (error) {
        console.warn('Could not load example data:', error);
        hideExampleIndicator();
        // Continue with empty form - user can still fill manually
    }
}

function showExampleIndicator() {
    const indicator = document.getElementById('example-loaded-indicator');
    if (indicator) {
        indicator.classList.remove('hidden');
    }
}

function hideExampleIndicator() {
    const indicator = document.getElementById('example-loaded-indicator');
    if (indicator) {
        indicator.classList.add('hidden');
    }
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function startTimer() {
    state.startTime = Date.now();
    state.timerInterval = setInterval(() => {
        const diff = Math.floor((Date.now() - state.startTime) / 1000);
        const m = Math.floor(diff / 60).toString().padStart(2, '0');
        const s = (diff % 60).toString().padStart(2, '0');
        els.sessionTimer.textContent = `${m}:${s}`;
    }, 1000);
}

function stopTimer() {
    if (state.timerInterval) clearInterval(state.timerInterval);
}

// ── Start Interview ──────────────────────────────────────────────────────────

async function startInterview() {
    els.startBtn.disabled = true;
    els.startBtn.textContent = 'Starting...';
    els.setupLoading.classList.remove('hidden');

    // Collect Data
    const projects = [];
    document.querySelectorAll('.project-entry').forEach(entry => {
        const desc = entry.querySelector('.proj-desc').value.trim();
        const skills = entry.querySelector('.proj-skills').value.trim();
        if (desc) projects.push({ description: desc, skills });
    });

    const payload = {
        candidate_id: document.getElementById('inp-candidate-id').value.trim() || 'cand-001',
        job_id: document.getElementById('inp-job-id').value.trim() || 'job-001',
        job_description: document.getElementById('inp-job-desc').value.trim() || '',
        skills: document.getElementById('inp-skills').value.split(',').map(s => s.trim()).filter(Boolean),
        education: document.getElementById('inp-education').value.trim(),
        leetcode_profile: document.getElementById('inp-leetcode').value.trim(),
        projects,
    };

    if (!payload.job_description) {
        alert('Please enter a job description.');
        els.startBtn.disabled = false;
        els.setupLoading.classList.add('hidden');
        return;
    }

    try {
        // 1. Create session via REST
        const res = await fetch(`${API_BASE}/session/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.detail || 'Failed to create session');

        state.sessionId = data.session_id;
        els.displaySessionId.textContent = data.session_id;

        // 2. Connect Audio WebSocket
        state.wsAudio = new WebSocket(`${WS_BASE}${data.ws_url}`); // /session/ID/live
        state.wsAudio.binaryType = 'arraybuffer';
        
        await new Promise((resolve, reject) => {
            state.wsAudio.onopen = resolve;
            state.wsAudio.onerror = () => reject(new Error('Audio WebSocket failed'));
        });

        // 3. Connect Video WebSocket
        state.wsVideo = new WebSocket(`${WS_BASE}/session/${state.sessionId}/video`);
        state.wsVideo.onopen = () => console.log('Video WS connected');
        state.wsVideo.onmessage = handleVideoMessage;

        // 4. Wait for Audio Ready
        await new Promise((resolve, reject) => {
            state.wsAudio.onmessage = (event) => {
                if (typeof event.data === 'string') {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'ready') resolve();
                    else if (msg.type === 'error') reject(new Error(msg.message));
                }
            };
            setTimeout(() => reject(new Error('Gemini timeout')), 15000);
        });

        // 5. Setup Audio Handlers
        state.wsAudio.onmessage = handleAudioMessage;
        state.wsAudio.onclose = () => setConnected(false);

        // 6. Start Media (Mic + Cam)
        await startMedia();

        // 7. UI Transition
        showSection('live');
        setConnected(true);
        startTimer();
        els.liveStatusText.textContent = 'Listening...';

    } catch (err) {
        console.error(err);
        alert('Failed to start: ' + err.message);
        if (state.wsAudio) state.wsAudio.close();
        if (state.wsVideo) state.wsVideo.close();
    } finally {
        els.startBtn.disabled = false;
        els.startBtn.textContent = 'Start Live Interview';
        els.setupLoading.classList.add('hidden');
    }
}

// ── Audio / Video Handling ───────────────────────────────────────────────────

async function startMedia() {
    try {
        // Mic
        state.micStream = await navigator.mediaDevices.getUserMedia({
            audio: { sampleRate: SEND_SAMPLE_RATE, channelCount: 1, echoCancellation: true, noiseSuppression: true },
        });
        
        // Webcam
        try {
            state.videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
            els.userVideo.srcObject = state.videoStream;
            startVideoSending(); // Start frame loop
        } catch (e) {
            console.warn('Camera not available:', e);
            logStatus('Camera access denied - proctoring limit', 'warning');
        }

        // Mic Processing
        const micCtx = new AudioContext({ sampleRate: SEND_SAMPLE_RATE });
        const source = micCtx.createMediaStreamSource(state.micStream);
        const processor = micCtx.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = (e) => {
            if (state.isMuted || !state.wsAudio || state.wsAudio.readyState !== WebSocket.OPEN) return;
            const f32 = e.inputBuffer.getChannelData(0);
            const i16 = new Int16Array(f32.length);
            for (let i = 0; i < f32.length; i++) {
                const s = Math.max(-1, Math.min(1, f32[i]));
                i16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            // Send raw PCM bytes directly
            state.wsAudio.send(i16.buffer);
            drawMiniVisualizer(f32); // Visual feedback
        };

        source.connect(processor);
        processor.connect(micCtx.destination);
        state.micProcessor = { processor, source, context: micCtx };

    } catch (e) {
        throw new Error('Microphone access failed: ' + e.message);
    }
}

// ── Video Sending Loop ──────────────────────────────────────────────────────
function startVideoSending() {
    const canvas = els.videoCanvas;
    const ctx = canvas.getContext('2d');
    const video = els.userVideo;

    const sendFrame = () => {
        if (!state.wsVideo || state.wsVideo.readyState !== WebSocket.OPEN) return;
        if (video.videoWidth === 0) {
           requestAnimationFrame(sendFrame);
           return;
        }

        canvas.width = 640;
        canvas.height = 480;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // JPEG encode
        const dataUrl = canvas.toDataURL('image/jpeg', 0.6);
        state.wsVideo.send(dataUrl); // Server parses base64

        // 2 FPS roughly
        setTimeout(() => requestAnimationFrame(sendFrame), 500); 
    };

    requestAnimationFrame(sendFrame);
}


// ── WebSocket Handlers ──────────────────────────────────────────────────────

function handleAudioMessage(event) {
    if (event.data instanceof ArrayBuffer) {
        playAudio(event.data);
        return;
    }

    const msg = JSON.parse(event.data);

    if (msg.type === 'transcript') {
        state.currentAiText += msg.text;
        showCaptions(state.currentAiText);
        
    } else if (msg.type === 'turn_complete') {
        if (state.currentAiText.trim()) {
            state.transcript.push({ role: 'interviewer', text: state.currentAiText.trim() });
        }
        state.currentAiText = '';
        setTimeout(() => showCaptions('Listening...'), 1500);
        els.liveStatusText.textContent = 'Listening...';

    } else if (msg.type === 'evaluation_update') {
        state.evaluation = msg.evaluation; // Store for end screen
    }
}

function handleVideoMessage(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'frame_analysis') {
        // Proctoring data
        const violations = data.violations || [];
        
        if (violations.length > 0) {
            // Show alert overlay
            const v = violations[0]; // Show highest priority
            els.videoOverlay.classList.remove('hidden');
            els.videoAlertMsg.textContent = v.message;
            els.camStatus.className = "absolute top-2 right-2 bg-red-500 p-1 rounded-full animate-pulse";
            
            // Log it
            logStatus(v.message, 'error');
        } else {
            els.videoOverlay.classList.add('hidden');
            els.camStatus.className = "absolute top-2 right-2 bg-primary/90 p-1 rounded-full";
        }
    }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function showCaptions(text) {
    els.captionsBox.textContent = text;
    els.captionsBox.classList.remove('opacity-0');
    // Hide after delay if it's user turn? No, keep it.
}

function logStatus(text, type='info') {
    const div = document.createElement('div');
    if (type === 'error') {
        div.className = "bg-red-500/10 border border-red-500/30 rounded-lg p-3";
        div.innerHTML = `
            <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-red-500 text-[18px] shrink-0">warning</span>
                 <p class="text-xs text-red-300">${escapeHtml(text)}</p>
            </div>
        `;
    } else if (type === 'warning') {
        div.className = "bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3";
        div.innerHTML = `
            <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-yellow-500 text-[18px] shrink-0">info</span>
                 <p class="text-xs text-yellow-300">${escapeHtml(text)}</p>
            </div>
        `;
    } else {
        div.className = "bg-slate-800/50 border border-slate-700 rounded-lg p-3";
        div.innerHTML = `<p class="text-xs text-slate-300">${escapeHtml(text)}</p>`;
    }
    els.statusLog.prepend(div);
}

// ── Audio Playback ───────────────────────────────────────────────────────────

let nextPlayTime = 0;

function ensureAudioCtx() {
    if (!state.audioCtx) {
        state.audioCtx = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: RECEIVE_SAMPLE_RATE,
        });
    }
    if (state.audioCtx.state === 'suspended') state.audioCtx.resume();
}

function playAudio(arrayBuffer) {
    ensureAudioCtx();
    els.liveStatusText.textContent = 'Zenith Speaking...';

    const ctx = state.audioCtx;
    const int16 = new Int16Array(arrayBuffer);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;

    const buf = ctx.createBuffer(1, float32.length, RECEIVE_SAMPLE_RATE);
    buf.getChannelData(0).set(float32);

    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(ctx.destination);

    const now = ctx.currentTime;
    if (nextPlayTime < now) nextPlayTime = now;
    src.start(nextPlayTime);
    nextPlayTime += buf.duration;
}

function drawMiniVisualizer(data) {
    // Simple mock animation or actual data driving the 7 bars
    const bars = els.miniVisualizer.querySelectorAll('.bar');
    // We have 7 bars. data is 4096 length. 
    // Simply pick 7 distinct points
    const step = Math.floor(data.length / 7);
    bars.forEach((bar, i) => {
        const val = Math.abs(data[i * step]) * 50; // Scale
        const h = Math.max(0.5, Math.min(3, val)); // rems roughly
        // If we want to animate height, we can set style
        // But CSS animation is already running 'sound-wave'.
        // Let's just adjust animation duration based on volume?
        // Or simpler: just let CSS handle it for now as requested by user mockup.
    });
}

function toggleMute() {
    state.isMuted = !state.isMuted;
    
    // Toggle UI
    if (state.isMuted) {
        els.micBtn.classList.remove('bg-slate-700', 'hover:bg-slate-600');
        els.micBtn.classList.add('bg-red-500', 'hover:bg-red-600');
        els.micIndicator.className = "absolute bottom-0 right-0 bg-red-500 border-4 border-surface-dark w-8 h-8 rounded-full flex items-center justify-center";
    } else {
        els.micBtn.classList.remove('bg-red-500', 'hover:bg-red-600');
        els.micBtn.classList.add('bg-slate-700', 'hover:bg-slate-600');
        els.micIndicator.className = "absolute bottom-0 right-0 bg-green-500 border-4 border-surface-dark w-8 h-8 rounded-full flex items-center justify-center";
    }
}

// ── End & Results ────────────────────────────────────────────────────────────

async function endInterview() {
    stopTimer();
    setConnected(false);

    // Close WebSockets
    if (state.wsAudio) state.wsAudio.close();
    if (state.wsVideo) state.wsVideo.close();

    // Stop Media
    if (state.micStream) state.micStream.getTracks().forEach(t => t.stop());
    if (state.videoStream) state.videoStream.getTracks().forEach(t => t.stop());
    
    if (state.micProcessor) {
        state.micProcessor.processor.disconnect();
        state.micProcessor.source.disconnect();
        state.micProcessor.context.close();
    }

    // Fetch Final Eval
    try {
        const res = await fetch(`${API_BASE}/session/${state.sessionId}/end`, { method: 'POST' });
        const data = await res.json();
        
        if (data.success) {
            showResults(data);
        }
    } catch (err) {
        console.error(err);
    }
    
    showSection('results');
}

function showResults(data) {
    const ev = data.evaluation;
    els.resOverall.textContent = ev ? `${ev.overall_score || 0}/10` : '--';
    els.resTech.textContent = ev ? `${ev.technical_competency || 0}/10` : '--';
    els.resComm.textContent = ev ? `${ev.communication_skills || 0}/10` : '--';
    els.resRec.textContent = ev ? (ev.recommendation || '--') : '--';

    // Transcript
    const transcript = data.transcript || [];
    els.finalTranscript.innerHTML = transcript.map(t => {
        const name = t.role === 'interviewer' ? 'Zenith' : 'Candidate';
        const color = t.role === 'interviewer' ? 'text-primary' : 'text-slate-300';
        return `
            <div class="mb-2">
                <span class="text-xs font-bold uppercase ${color} tracking-wide">${name}</span>
                <p class="text-sm text-slate-200 mt-1">${escapeHtml(t.text)}</p>
            </div>
        `;
    }).join('');
}
