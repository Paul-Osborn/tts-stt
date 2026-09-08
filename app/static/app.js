const $ = id => document.getElementById(id);
let csrf = '', deviceKey = '', busy = false, recording = false, recorder, stream;
const stt = 'large-v3-turbo';
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
  $('file').disabled = true;
  try { await work(); } catch (error) { status(error.message); }
  finally { busy = false; $('file').disabled = false; }
}
function showWorkspace() {
  $('signin').hidden = true; $('workspace').hidden = false;
  $('models').textContent = `Transcribed on this computer · ${stt}`;
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
  status('Ready when you are.');
}
async function transcribe(file) {
  if (file.size > 25000000) throw new Error('Choose a recording smaller than 25 MB.');
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
  $('record').disabled = true; $('file').disabled = true;
  let activeStream;
  const release = () => {
    activeStream?.getTracks().forEach(track => track.stop());
    recording = false; $('record').disabled = false;
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
    recorder.start(); $('record').disabled = false; $('record').textContent = 'Stop & transcribe'; status('Recording… press stop when you have finished speaking.');
  } catch (error) { release(); status(error.message); }
};
$('copy').onclick = () => task(async () => { await navigator.clipboard.writeText($('transcript').value); status('Copied.'); });
$('clear').onclick = () => { $('transcript').value = ''; status('Cleared.'); };
$('add-device').onclick = () => task(async () => {
  const data = await (await api('control/devices', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ label: $('device-name').value }) })).json();
  $('new-key').textContent = `Shown once — enter this in your device’s API key field: ${data.token}`;
  $('new-key').hidden = false; $('hide-key').hidden = false; await refresh();
});
$('hide-key').onclick = () => { $('new-key').textContent = ''; $('new-key').hidden = true; $('hide-key').hidden = true; };
$('logout').onclick = () => task(async () => { await api('control/logout', { method: 'POST' }); location.reload(); });
window.addEventListener('pagehide', () => { stream?.getTracks().forEach(track => track.stop()); });
refresh().catch(() => status('Sign in, or connect a tester device key to begin.'));
