/* ============================================================
   English → Santali (Ol Chiki) Translator — script.js
   ============================================================ */

// ---------- DOM Elements ----------
const micBtn          = document.getElementById('micBtn');
const micLabel        = document.getElementById('micLabel');
const statusEl        = document.getElementById('status');
const englishOut      = document.getElementById('englishOutput');
const santaliOut      = document.getElementById('santaliOutput');
const pronunciationEl = document.getElementById('pronunciation');
const outputSection   = document.getElementById('outputSection');

// Text modal
const typeToggle      = document.getElementById('typeToggle');
const textModalOvl    = document.getElementById('textModalOverlay');
const textModal       = document.getElementById('textModal');
const textModalClose  = document.getElementById('textModalClose');
const typedInput      = document.getElementById('typedInput');
const translateBtn    = document.getElementById('translateBtn');

// History panel
const historyToggle   = document.getElementById('historyToggleBtn');
const historyPanel    = document.getElementById('historyPanel');
const panelOverlay    = document.getElementById('panelOverlay');
const panelCloseBtn   = document.getElementById('panelCloseBtn');
const historyList     = document.getElementById('historyList');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const historyBadge    = document.getElementById('historyBadge');

const HISTORY_KEY = 'santali_translation_history';

let mediaRecorder = null;
let audioChunks   = [];
let isRecording   = false;


/* ==============================================================
   STATUS HELPERS
   ============================================================== */
function setStatus(msg, isError = false) {
    statusEl.className = 'status' + (isError ? ' error' : '');
    statusEl.innerHTML = msg;
}

function setLoading(msg) {
    setStatus('<span class="loader"></span>' + msg);
}


/* ==============================================================
   TEXT INPUT MODAL
   ============================================================== */
function openTextModal() {
    textModal.classList.add('open');
    textModalOvl.classList.add('open');
    setTimeout(() => typedInput.focus(), 350);
}

function closeTextModal() {
    textModal.classList.remove('open');
    textModalOvl.classList.remove('open');
}

typeToggle.addEventListener('click', openTextModal);
textModalClose.addEventListener('click', closeTextModal);
textModalOvl.addEventListener('click', closeTextModal);


/* ==============================================================
   DISPLAY RESULTS
   ============================================================== */
function showResults(english, santali, pronunciation) {
    englishOut.textContent = english;
    santaliOut.textContent = santali;
    pronunciationEl.textContent = pronunciation ? '(' + pronunciation + ')' : '';
    outputSection.classList.add('visible');
}


/* ==============================================================
   HISTORY (localStorage)
   ============================================================== */
function getHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
    catch { return []; }
}

function saveHistory(arr) {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(arr));
    updateBadge(arr.length);
}

function addHistory(en, sat, pr) {
    const history = getHistory();
    history.unshift({ en, sat, pr: pr || '', time: new Date().toLocaleString() });
    if (history.length > 100) history.length = 100;
    saveHistory(history);
    renderHistory();
}

function renderHistory() {
    const history = getHistory();
    updateBadge(history.length);

    if (history.length === 0) {
        historyList.innerHTML = '<div class="panel-empty">No translations yet.<br>Start speaking or typing!</div>';
        return;
    }
    historyList.innerHTML = history.map(function(h) {
        return '<div class="history-item">'
            + '<div class="hi-time">' + (h.time || '') + '</div>'
            + '<div class="hi-en">EN: ' + h.en + '</div>'
            + '<div class="hi-sat">\u1C65\u1C5F: ' + h.sat + '</div>'
            + (h.pr ? '<div class="hi-pr">(' + h.pr + ')</div>' : '')
            + '</div>';
    }).join('');
}

function updateBadge(count) {
    historyBadge.textContent = count;
    historyBadge.style.display = count > 0 ? 'inline-block' : 'none';
}

function openHistoryPanel() {
    historyPanel.classList.add('open');
    panelOverlay.classList.add('open');
    renderHistory();
}

function closeHistoryPanel() {
    historyPanel.classList.remove('open');
    panelOverlay.classList.remove('open');
}

historyToggle.addEventListener('click', openHistoryPanel);
panelCloseBtn.addEventListener('click', closeHistoryPanel);
panelOverlay.addEventListener('click', closeHistoryPanel);

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeHistoryPanel();
        closeTextModal();
    }
});

clearHistoryBtn.addEventListener('click', function() {
    if (confirm('Clear all translation history?')) {
        localStorage.removeItem(HISTORY_KEY);
        renderHistory();
    }
});

// Initial badge count
renderHistory();


/* ==============================================================
   MIME TYPE DETECTION
   ============================================================== */
function getSupportedMimeType() {
    var types = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/mp4',
        'audio/wav',
        ''
    ];
    for (var i = 0; i < types.length; i++) {
        if (types[i] === '' || MediaRecorder.isTypeSupported(types[i])) {
            return types[i];
        }
    }
    return '';
}


/* ==============================================================
   MIC RECORDING
   ============================================================== */
micBtn.addEventListener('click', async function() {
    if (isRecording) {
        stopRecording();
        return;
    }

    try {
        var stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        var mimeType = getSupportedMimeType();
        var options  = mimeType ? { mimeType: mimeType } : {};
        mediaRecorder = new MediaRecorder(stream, options);
        audioChunks = [];

        mediaRecorder.ondataavailable = function(e) {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async function() {
            stream.getTracks().forEach(function(t) { t.stop(); });

            if (audioChunks.length === 0) {
                setStatus('No audio captured. Please try again.', true);
                return;
            }

            var blob = new Blob(audioChunks, {
                type: mediaRecorder.mimeType || 'audio/webm'
            });

            if (blob.size < 100) {
                setStatus('Recording too short. Speak for at least 1 second.', true);
                return;
            }

            await sendAudio(blob);
        };

        mediaRecorder.onerror = function(e) {
            setStatus('Recording error: ' + (e.error ? e.error.message : 'unknown'), true);
            stopRecording();
        };

        mediaRecorder.start(1000);
        isRecording = true;
        micBtn.classList.add('recording');
        micBtn.textContent = '⏹️';
        micLabel.textContent = 'Recording… tap to stop';
        setStatus('🔴 Listening…');

    } catch (err) {
        setStatus('Microphone access denied. Please allow mic permission.', true);
    }
});

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    isRecording = false;
    micBtn.classList.remove('recording');
    micBtn.textContent = '🎤';
    micLabel.textContent = 'Tap to speak';
}

async function sendAudio(blob) {
    setLoading('Transcribing & translating…');
    var form = new FormData();
    var ext = blob.type.includes('ogg') ? '.ogg'
            : blob.type.includes('mp4') ? '.mp4'
            : blob.type.includes('wav') ? '.wav'
            : '.webm';
    form.append('audio', blob, 'recording' + ext);

    try {
        var res = await fetch('/transcribe', { method: 'POST', body: form });
        var data = await res.json();

        if (data.error) {
            setStatus(data.error, true);
            return;
        }

        showResults(data.english, data.santali, data.pronunciation);
        addHistory(data.english, data.santali, data.pronunciation);
        setStatus('✅ Done!');

    } catch (err) {
        setStatus('Network error: ' + err.message + '. Is the server running?', true);
    }
}


/* ==============================================================
   TEXT TRANSLATION
   ============================================================== */
translateBtn.addEventListener('click', translateTyped);
typedInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        translateTyped();
    }
});

async function translateTyped() {
    var text = typedInput.value.trim();
    if (!text) return;

    translateBtn.disabled = true;
    setLoading('Translating…');
    closeTextModal();

    try {
        var res = await fetch('/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        var data = await res.json();

        if (data.error) {
            setStatus(data.error, true);
            translateBtn.disabled = false;
            return;
        }

        showResults(data.english, data.santali, data.pronunciation);
        addHistory(data.english, data.santali, data.pronunciation);
        setStatus('✅ Done!');

    } catch (err) {
        setStatus('Network error: ' + err.message, true);
    }

    translateBtn.disabled = false;
}
