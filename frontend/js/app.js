/**
 * Call Agent Frontend Application
 */

// ===== Global State =====
const state = {
    sessionId: null,
    isCallActive: false,
    isMuted: false,
    isRecording: false,
    callStartTime: null,
    callDuration: 0,
    durationInterval: null,
    mediaRecorder: null,
    browserRecognition: null,
    audioChunks: [],

    audioContext: null,
    analyser: null,
    microphone: null,
    voiceName: 'Sarah',
    serverUrl: window.location.origin,
    theme: 'dark'

};

// ===== DOM Elements =====
const elements = {
    startCallBtn: null,
    endCallBtn: null,
    muteBtn: null,
    voiceSelect: null,
    chatMessages: null,
    textInput: null,
    callStatus: null,
    agentAvatar: null,
    audioVisualizer: null,
    connectionStatus: null,
    callPanel: null,
    toastContainer: null,
    callModal: null,
    callSummary: null
};

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    initializeEventListeners();
    loadSettings();
    checkConnection();
    startVisualizer();
});

function initializeElements() {
    elements.startCallBtn = document.getElementById('startCallBtn');
    elements.endCallBtn = document.getElementById('endCallBtn');
    elements.muteBtn = document.getElementById('muteBtn');
    elements.voiceSelect = document.getElementById('voiceSelect');
    elements.chatMessages = document.getElementById('chatMessages');
    elements.textInput = document.getElementById('textInput');
    elements.callStatus = document.getElementById('callStatus');
    elements.agentAvatar = document.getElementById('agentAvatar');
    elements.audioVisualizer = document.getElementById('audioVisualizer');
    elements.connectionStatus = document.getElementById('connectionStatus');
    elements.callPanel = document.getElementById('callPanel');
    elements.toastContainer = document.getElementById('toastContainer');
    elements.callModal = document.getElementById('callModal');
    elements.callSummary = document.getElementById('callSummary');
}

function initializeEventListeners() {
    // Navigation active state
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');
        });
    });

    // Microphone select
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(() => {
            return navigator.mediaDevices.enumerateDevices();
        })
        .then(devices => {
            const microphones = devices.filter(d => d.kind === 'audioinput');
            const micSelect = document.getElementById('microphoneSelect');
            if (micSelect) {
                microphones.forEach(mic => {
                    const option = document.createElement('option');
                    option.value = mic.deviceId;
                    option.textContent = mic.label || `Microphone ${micSelect.options.length + 1}`;
                    micSelect.appendChild(option);
                });
            }
        })
        .catch(err => {
            console.log('Microphone access not available:', err);
        });
}

// ===== API Functions =====
async function apiRequest(endpoint, options = {}) {
    const url = `${state.serverUrl}${endpoint}`;
    const config = {
        ...options,
        headers: {
            ...options.headers
        }
    };

    // Don't set Content-Type for FormData (let browser set it with boundary)
    if (!(options.body instanceof FormData)) {
        config.headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(url, config);
        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const data = await response.json();
                if (data.detail) {
                    if (typeof data.detail === 'string') {
                        errorMsg = data.detail;
                    } else if (Array.isArray(data.detail)) {
                        errorMsg = data.detail.map(e => e.msg || JSON.stringify(e)).join(', ');
                    } else if (typeof data.detail === 'object') {
                        errorMsg = data.detail.message || JSON.stringify(data.detail);
                    }
                }
            } catch (e) {
                // Not JSON or other error
            }
            throw new Error(errorMsg);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

async function checkConnection() {
    try {
        await fetch(`${state.serverUrl}/health`);
        updateConnectionStatus(true);
    } catch {
        updateConnectionStatus(false);
    }
}

async function startCall() {
    try {
        showToast('Starting call...', 'info');

        const formData = new FormData();
        if (state.voiceName) {
            formData.append('caller_id', 'web-user');
        }

        const response = await apiRequest('/api/calls/start', {
            method: 'POST',
            body: formData
        });

        state.sessionId = response.session_id;
        state.isCallActive = true;
        state.callStartTime = Date.now();
        state.callDuration = 0;

        // Update UI
        elements.startCallBtn.disabled = true;
        elements.endCallBtn.disabled = false;
        elements.muteBtn.disabled = false;
        elements.callStatus.textContent = 'Call in progress';
        elements.callStatus.classList.add('active');

        // Add greeting message
        addMessage('assistant', response.greeting_text);

        // Play greeting audio if available
        if (response.greeting_audio) {
            playAudio(response.greeting_audio);
        } else if (response.tts_error) {
            console.warn('TTS Error:', response.tts_error);
            showToast('Audio generation failed, using text-only.', 'warning');
        }


        // Start duration timer
        startDurationTimer();

        // Start microphone recording
        await startRecording();
        startBrowserSTT();


        showToast('Call connected!', 'success');
        updateCallStats();

    } catch (error) {
        console.error('Failed to start call:', error);
        showToast('Failed to start call. Is the server running?', 'error');
    }
}

async function endCall() {
    if (!state.sessionId) return;

    try {
        // Stop recording
        stopRecording();

        // End call on server
        const formData = new FormData();
        formData.append('session_id', state.sessionId);

        const response = await apiRequest('/api/calls/end', {
            method: 'POST',
            body: formData
        });

        // Stop duration timer
        stopDurationTimer();

        // Show summary
        showCallSummary(response.summary);

        // Reset state
        state.isCallActive = false;
        state.sessionId = null;

        // Update UI
        elements.startCallBtn.disabled = false;
        elements.endCallBtn.disabled = true;
        elements.muteBtn.disabled = true;
        elements.callStatus.textContent = 'Ready to call';
        elements.callStatus.classList.remove('active');

        addMessage('system', 'Call ended. View summary for details.');

        // Load history
        loadCallHistory();

        showToast('Call ended', 'success');

    } catch (error) {
        console.error('Failed to end call:', error);
    }
}

async function processAudio(audioBlob) {
    if (!state.sessionId || !state.isCallActive) return;

    try {
        const formData = new FormData();
        formData.append('session_id', state.sessionId);
        formData.append('audio', audioBlob, 'audio.wav');

        const response = await apiRequest('/api/calls/process', {
            method: 'POST',
            body: formData
        });

        // Add user message
        addMessage('user', response.user_text, {
            intent: response.intent,
            sentiment: response.sentiment
        });

        // Add assistant response
        addMessage('assistant', response.assistant_text);

        // Play assistant audio if available
        if (response.assistant_audio) {
            playAudio(response.assistant_audio);
        } else if (response.tts_error) {
            console.warn('TTS Error:', response.tts_error);
        }


        // Update stats
        updateCallStats(response);

        // Check for escalation
        if (response.escalation) {
            showToast('Escalating to human agent...', 'warning');
        }

        // Check if call ended
        if (response.call_ended) {
            setTimeout(() => endCall(), 1000);
        }

    } catch (error) {
        console.error('Failed to process audio:', error);
    }
}

async function sendTextMessage(text) {
    if (!state.sessionId || !state.isCallActive) return;


    const message = text || elements.textInput.value.trim();
    if (!message) return;

    elements.textInput.value = '';

    try {
        // For text input, we still need to send audio to the API
        // Create a simple audio placeholder or use speech synthesis
        addMessage('user', message);

        // Generate response using the API (we'll need to add a text endpoint)
        // For now, let's convert text to speech and process it
        const formData = new FormData();
        formData.append('session_id', state.sessionId);
        formData.append('text', message);

        const response = await apiRequest('/api/calls/process', {
            method: 'POST',
            body: formData
        });


        addMessage('assistant', response.assistant_text);
        playAudio(response.assistant_audio);
        updateCallStats(response);

    } catch (error) {
        console.error('Failed to send message:', error);
        // Fallback: just add the message locally
        addMessage('assistant', 'I received your message. Please speak for a voice response.');
    }
}

function createTextFormData(text) {
    // This is a workaround - ideally the backend should have a text endpoint
    const formData = new FormData();
    formData.append('session_id', state.sessionId);
    // Create empty audio file as placeholder
    const audioBlob = new Blob([], { type: 'audio/wav' });
    formData.append('audio', audioBlob, 'audio.wav');
    return formData;
}

// ===== Audio Functions =====
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            }
        });

        state.audioContext = new AudioContext({ sampleRate: 16000 });
        state.analyser = state.audioContext.createAnalyser();
        state.analyser.fftSize = 256;
        state.microphone = state.audioContext.createMediaStreamSource(stream);
        state.microphone.connect(state.analyser);

        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];

        state.mediaRecorder.ondataavailable = (event) => {
            state.audioChunks.push(event.data);
        };

        state.mediaRecorder.onstop = async () => {
            if (state.audioChunks.length > 0) {
                const audioBlob = new Blob(state.audioChunks, { type: state.mediaRecorder.mimeType });
                // We are now using Browser STT to avoid 404 errors from NVIDIA on the backend
                // await processAudio(audioBlob); 
            }
            state.audioChunks = [];

            
            // Restart recording if call is still active
            if (state.isCallActive && state.isRecording) {
                state.mediaRecorder.start();
                // Set a timeout for the next chunk
                setTimeout(() => {
                    if (state.isCallActive && state.mediaRecorder.state === 'recording') {
                        state.mediaRecorder.stop();
                    }
                }, 4000); // 4 second chunks
            }
        };

        state.mediaRecorder.start();
        state.isRecording = true;

        // Trigger the first stop after 4 seconds
        setTimeout(() => {
            if (state.isCallActive && state.mediaRecorder.state === 'recording') {
                state.mediaRecorder.stop();
            }
        }, 4000);

    } catch (error) {
        console.error('Failed to start recording:', error);
        showToast('Microphone access denied', 'error');
    }
}

function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
    }

    stopBrowserSTT();

    if (state.audioContext) {
        state.audioContext.close();
        state.audioContext = null;
    }
}

function startBrowserSTT() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Web Speech API not supported');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    state.browserRecognition = new SpeechRecognition();
    state.browserRecognition.continuous = true;
    state.browserRecognition.interimResults = false;
    state.browserRecognition.lang = 'en-US';

    state.browserRecognition.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript.trim();
        if (transcript) {
            console.log('Browser STT result:', transcript);
            sendTextMessage(transcript);
        }
    };

    state.browserRecognition.onerror = (event) => {
        console.error('Browser STT error:', event.error);
    };

    state.browserRecognition.onend = () => {
        if (state.isCallActive) {
            state.browserRecognition.start();
        }
    };

    state.browserRecognition.start();
}

function stopBrowserSTT() {
    if (state.browserRecognition) {
        state.browserRecognition.onend = null;
        state.browserRecognition.stop();
        state.browserRecognition = null;
    }
}


function playAudio(audioBase64) {
    if (!audioBase64) return;

    try {
        const binaryString = window.atob(audioBase64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        const audioBlob = new Blob([bytes], { type: 'audio/mpeg' }); // ElevenLabs usually returns mp3
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);


        audio.onstart = () => {
            elements.agentAvatar.classList.add('speaking');
        };

        audio.onend = () => {
            elements.agentAvatar.classList.remove('speaking');
            URL.revokeObjectURL(audioUrl);
        };

        audio.onerror = () => {
            elements.agentAvatar.classList.remove('speaking');
        };

        audio.play();
    } catch (error) {
        console.error('Failed to play audio:', error);
    }
}

function toggleMute() {
    state.isMuted = !state.isMuted;
    elements.muteBtn.innerHTML = state.isMuted
        ? '<i class="fas fa-microphone-slash"></i><span>Unmute</span>'
        : '<i class="fas fa-microphone"></i><span>Mute</span>';

    if (state.microphone) {
        state.microphone.disconnect();
        if (!state.isMuted) {
            state.microphone.connect(state.analyser);
        }
    }
}

function changeVoice() {
    state.voiceName = elements.voiceSelect.value;
    showToast(`Voice changed to ${state.voiceName}`, 'success');
}

// ===== Visualizer =====
function startVisualizer() {
    const canvas = elements.audioVisualizer;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    function draw() {
        requestAnimationFrame(draw);

        ctx.fillStyle = 'rgba(30, 41, 59, 0.3)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        if (state.analyser && state.isCallActive && !state.isMuted) {
            const dataArray = new Uint8Array(state.analyser.frequencyBinCount);
            state.analyser.getByteFrequencyData(dataArray);

            const barWidth = canvas.width / dataArray.length;
            let x = 0;

            for (let i = 0; i < dataArray.length; i++) {
                const barHeight = (dataArray[i] / 255) * canvas.height;

                const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
                gradient.addColorStop(0, '#6366f1');
                gradient.addColorStop(1, '#8b5cf6');

                ctx.fillStyle = gradient;
                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

                x += barWidth + 1;
            }
        } else {
            // Draw idle state
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, canvas.height / 2);
            ctx.lineTo(canvas.width, canvas.height / 2);
            ctx.stroke();
        }
    }

    draw();
}

// ===== Chat Functions =====
function addMessage(role, content, meta = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    const contentSpan = document.createElement('span');
    contentSpan.className = 'message-content';
    contentSpan.textContent = content;

    messageDiv.appendChild(contentSpan);

    if (meta.intent || meta.sentiment) {
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        const parts = [];
        if (meta.intent) parts.push(`Intent: ${meta.intent}`);
        if (meta.sentiment) parts.push(`Sentiment: ${meta.sentiment}`);
        metaDiv.textContent = parts.join(' • ');
        messageDiv.appendChild(metaDiv);
    }

    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function clearChat() {
    elements.chatMessages.innerHTML = `
        <div class="message system-message">
            <span class="message-content">Chat cleared</span>
        </div>
    `;
}

function handleTextKeyPress(event) {
    if (event.key === 'Enter') {
        sendTextMessage();
    }
}

// ===== Stats Functions =====
function startDurationTimer() {
    state.durationInterval = setInterval(() => {
        state.callDuration = Math.floor((Date.now() - state.callStartTime) / 1000);
        updateCallStats();
    }, 1000);
}

function stopDurationTimer() {
    if (state.durationInterval) {
        clearInterval(state.durationInterval);
        state.durationInterval = null;
    }
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function updateCallStats(apiResponse = null) {
    document.getElementById('durationStat').textContent = formatDuration(state.callDuration);

    if (apiResponse) {
        document.getElementById('intentStat').textContent = apiResponse.intent || '-';

        const sentimentEl = document.getElementById('sentimentStat');
        sentimentEl.textContent = apiResponse.sentiment || '-';
        sentimentEl.className = 'stat-value';
        if (apiResponse.sentiment === 'positive') sentimentEl.style.color = '#10b981';
        else if (apiResponse.sentiment === 'negative') sentimentEl.style.color = '#ef4444';
        else sentimentEl.style.color = '';
    }

    const messageCount = elements.chatMessages.querySelectorAll('.message').length;
    document.getElementById('messagesStat').textContent = messageCount;
}

// ===== History Functions =====
async function loadCallHistory() {
    try {
        const response = await apiRequest('/api/calls/calls/recent?limit=20');
        renderHistory(response.calls || []);
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function renderHistory(calls) {
    const container = document.getElementById('historyList');
    if (!container) return;

    if (!calls || calls.length === 0) {
        container.innerHTML = `
            <div class="history-empty">
                <i class="fas fa-inbox"></i>
                <p>No call history yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = calls.map(call => `
        <div class="history-item" data-session="${call.session_id}">
            <div class="history-info">
                <h3>Call #${call.id || call.session_id.slice(0, 8)}</h3>
                <p>${new Date(call.timestamp).toLocaleString()}</p>
            </div>
            <div class="history-meta">
                <span class="history-badge ${call.resolution_status || 'completed'}">
                    ${call.resolution_status || 'completed'}
                </span>
                <span class="history-badge ${call.sentiment_label || 'neutral'}">
                    ${call.sentiment_label || 'neutral'}
                </span>
            </div>
            <div class="history-actions">
                <button class="btn btn-primary btn-small" onclick="viewCallDetails('${call.session_id}')">
                    View Details
                </button>
            </div>
        </div>
    `).join('');
}

function filterHistory() {
    const search = document.getElementById('searchHistory').value.toLowerCase();
    const status = document.getElementById('filterStatus').value;
    const items = document.querySelectorAll('.history-item');

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        const matchesSearch = text.includes(search);
        const matchesStatus = !status || item.querySelector(`.${status}`);

        item.style.display = matchesSearch && matchesStatus ? '' : 'none';
    });
}

async function viewCallDetails(sessionId) {
    try {
        const response = await apiRequest(`/api/calls/calls/${sessionId}`);
        showCallSummary(response.call);
    } catch (error) {
        showToast('Failed to load call details', 'error');
    }
}

// ===== Modal Functions =====
function showCallSummary(summary) {
    if (!summary) return;

    elements.callSummary.innerHTML = `
        <div class="summary-stat">
            <span class="summary-label">Session ID</span>
            <span class="summary-value">${summary.session_id?.slice(0, 12)}...</span>
        </div>
        <div class="summary-stat">
            <span class="summary-label">Duration</span>
            <span class="summary-value">${formatDuration(Math.floor(summary.duration_seconds || 0))}</span>
        </div>
        <div class="summary-stat">
            <span class="summary-label">Messages</span>
            <span class="summary-value">${summary.message_count || 0}</span>
        </div>
        <div class="summary-stat">
            <span class="summary-label">Primary Intent</span>
            <span class="summary-value">${summary.primary_intent || 'unknown'}</span>
        </div>
        <div class="summary-stat">
            <span class="summary-label">Overall Sentiment</span>
            <span class="summary-value">${summary.sentiment || 'neutral'}</span>
        </div>
        <div class="summary-stat">
            <span class="summary-label">Status</span>
            <span class="summary-value">${summary.escalated ? 'Escalated' : 'Completed'}</span>
        </div>
    `;

    elements.callModal.classList.add('active');
}

function closeModal() {
    elements.callModal.classList.remove('active');
}

// ===== Settings Functions =====
function loadSettings() {
    const saved = localStorage.getItem('callAgentSettings');
    if (saved) {
        const settings = JSON.parse(saved);
        if (settings.serverUrl) {
            state.serverUrl = settings.serverUrl;
            document.getElementById('serverUrl').value = settings.serverUrl;
        }
        if (settings.theme) {
            state.theme = settings.theme;
            document.getElementById('themeSelect').value = settings.theme;
            applyTheme(settings.theme);
        }
    }
}

function saveSettings() {
    const settings = {
        serverUrl: document.getElementById('serverUrl').value,
        theme: state.theme
    };
    localStorage.setItem('callAgentSettings', JSON.stringify(settings));
}

function changeTheme() {
    const theme = document.getElementById('themeSelect').value;
    state.theme = theme;
    applyTheme(theme);
    saveSettings();
}

function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
}

// ===== Utility Functions =====
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let displayMessage = message;
    if (typeof message === 'object' && message !== null) {
        displayMessage = message.message || message.detail || JSON.stringify(message);
    }


    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${displayMessage}</span>
    `;


    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function updateConnectionStatus(connected) {
    const badge = elements.connectionStatus;
    if (connected) {
        badge.classList.add('connected');
        badge.querySelector('span:last-child').textContent = 'Connected';
    } else {
        badge.classList.remove('connected');
        badge.querySelector('span:last-child').textContent = 'Disconnected';
    }
}

function scrollToCall() {
    document.getElementById('call').scrollIntoView({ behavior: 'smooth' });
}

// Auto-load history on page load
loadCallHistory();

// Periodic connection check
setInterval(checkConnection, 30000);
