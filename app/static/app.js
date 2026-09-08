const $ = id => document.getElementById(id);
let csrf = '', deviceKey = '', busy = false, recording = false, recorder, stream, timer, audioURL;
const stt = 'gemini-2.5-flash', tts = 'gemini-2.5-flash-preview-tts';
const status = text => { $('status').textContent = text; };
async function api(path, options = {}) {
  const headers = { ...options.headers };
  if (deviceKey) headers.Authorization = `Bearer ${deviceKey}`;
  if (csrf) headers['X-CSRF-Token'] = csrf;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error?.message || 'Request failed. Check your connection.');
  }
  return response;
}
async function task(work) {
  if (busy || recording) return;
  busy = true;
  $('speak').disabled = true; $('file').disabled = true;
  try { await work(); } catch (error) { status(error.message); }
  finally { busy = false; $('speak').disabled = false; $('file').disabled = false; }
}
function showWorkspace() {
  $('signin').hidden = true; $('workspace').hidden = false;
  $('models').textContent = `Google Gemini · Transcription: ${stt} · Speech: ${tts}`;
}
async function refresh() {
  const data = await (await api('control')).json();
  csrf = data.csrf;
  showWorkspace(); $('settings').hidden = false;
  $('devices').replaceChildren();
  for (const device of data.devices) {
    const item = document.createElement('li');
    item.append(document.createTextNode(device.label + ' '));
    const button = document.createElement('button'); button.textContent = 'Revoke';
    button.onclick = () => task(async () => { await api(`control/devices/${device.id}`, { method: 'DELETE' }); await refresh(); status('Device key revoked.'); });
    item.append(button); $('devices').append(item);
  }
  status(data.ready ? 'Ready when you are.' : 'Setup needed: add a Gemini key and confirm Free Tier in the local .env file.');
}
async function transcribe(file) {
  if (file.size > 1000000) throw new Error('Choose a recording smaller than 1 MB.');
  status('Listening to your recording…');
  const body = new FormData(); body.append('file', file); body.append('model', stt);
  const data = await (await api('v1/audio/transcriptions', { method: 'POST', body })).json();
  $('transcript').value = data.text; status(data.text ? 'Your words are ready.' : 'No speech detected.');
}
$('connect').onclick = () => task(async () => {
  deviceKey = $('token').value.trim(); $('token').value = '';
  await api('v1/models'); showWorkspace(); status('Tester connected.');
});
$('file').onchange = () => task(async () => { if ($('file').files[0]) await transcribe($('file').files[0]); $('file').value = ''; });
$('record').onclick = async () => {
  if (recorder?.state === 'recording') { recorder.stop(); return; }
  if (busy || recording) return;
  recording = true;
  $('record').disabled = true; $('speak').disabled = true; $('file').disabled = true;
  let activeStream;
  const release = () => {
    clearTimeout(timer); activeStream?.getTracks().forEach(track => track.stop());
    recording = false; $('record').disabled = false; $('speak').disabled = false;
    $('file').disabled = false; $('record').textContent = 'Start recording';
  };
  try {
    if (!navigator.mediaDevices || !window.MediaRecorder) throw new Error('Microphone recording needs a supported browser on HTTPS or localhost.');
    activeStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream = activeStream;
    const mimeType = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4'].find(type => MediaRecorder.isTypeSupported(type));
    if (!mimeType) throw new Error('This browser cannot record a supported format. Choose an audio file instead.');
    recorder = new MediaRecorder(activeStream, { mimeType });
    const chunks = [];
    recorder.ondataavailable = event => chunks.push(event.data);
    recorder.onstop = () => {
      release();
      const ext = mimeType.includes('webm') ? 'webm' : mimeType.includes('ogg') ? 'ogg' : 'm4a';
      task(() => transcribe(new File(chunks, `recording.${ext}`, { type: mimeType })));
    };
    recorder.onerror = () => { recorder.onstop = release; release(); status('Recording failed. Please try again.'); };
    recorder.start(); $('record').disabled = false; $('record').textContent = 'Stop & transcribe'; status('Recording… stops automatically after 20 seconds.');
    timer = setTimeout(() => { if (recorder.state === 'recording') recorder.stop(); }, 20000);
  } catch (error) { release(); status(error.message); }
};
$('speak').onclick = () => task(async () => {
  if (!$('text').value.trim()) throw new Error('Enter some words first.');
  status('Creating your audio…');
  const response = await api('v1/audio/speech', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: tts, input: $('text').value, voice: $('voice').value, response_format: 'wav' }) });
  if (audioURL) URL.revokeObjectURL(audioURL);
  audioURL = URL.createObjectURL(await response.blob()); $('player').src = audioURL;
  await $('player').play().catch(() => {}); status('Your audio is ready.');
});
$('copy').onclick = () => task(async () => { await navigator.clipboard.writeText($('transcript').value); status('Copied.'); });
$('clear').onclick = () => { $('transcript').value = ''; $('text').value = ''; $('player').pause(); $('player').removeAttribute('src'); if (audioURL) URL.revokeObjectURL(audioURL); status('Cleared.'); };
$('save-provider').onclick = () => task(async () => {
  const key = $('provider-key').value; $('provider-key').value = '';
  await api('control/provider', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key }) }); status('Gemini key saved securely.');
});
$('delete-provider').onclick = () => task(async () => {
  const data = await (await api('control/provider', { method: 'DELETE' })).json();
  status(data.env_key_present ? 'Vault key deleted. A key still exists in .env; remove it there to disconnect Gemini.' : 'Gemini key deleted.');
});
$('add-device').onclick = () => task(async () => {
  const data = await (await api('control/devices', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ label: $('device-name').value }) })).json();
  $('new-key').textContent = `Shown once — enter this in your device’s API key field: ${data.token}`;
  $('new-key').hidden = false; $('hide-key').hidden = false; await refresh();
});
$('hide-key').onclick = () => { $('new-key').textContent = ''; $('new-key').hidden = true; $('hide-key').hidden = true; };
$('logout').onclick = () => task(async () => { await api('control/logout', { method: 'POST' }); location.reload(); });
window.addEventListener('pagehide', () => { clearTimeout(timer); stream?.getTracks().forEach(track => track.stop()); if (audioURL) URL.revokeObjectURL(audioURL); });
refresh().catch(() => status('Sign in, or connect a tester device key to begin.'));
