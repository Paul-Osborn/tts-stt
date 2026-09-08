// Regression for competing work during microphone acquisition/recording.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map();
const element = id => {
  if (!elements.has(id)) elements.set(id, { value: '', disabled: false });
  return elements.get(id);
};
let grant, acquisitions = 0, stopped = 0, uploads = 0;
class Recorder {
  static isTypeSupported() { return true; }
  constructor() { this.state = 'inactive'; }
  start() { this.state = 'recording'; }
  stop() { this.state = 'inactive'; this.onstop(); }
}
const context = vm.createContext({
  document: { getElementById: element }, window: { MediaRecorder: Recorder, addEventListener() {} },
  MediaRecorder: Recorder, File, FormData, URL, setTimeout, clearTimeout,
  navigator: { mediaDevices: { getUserMedia() { acquisitions++; return new Promise(resolve => { grant = resolve; }); } } },
  fetch: async path => {
    if (path === 'control') return { ok: false, json: async () => ({}) };
    uploads++;
    return { ok: true, json: async () => ({ text: 'Recorded words.' }) };
  },
});
vm.runInContext(fs.readFileSync('app/static/app.js', 'utf8'), context);
(async () => {
  const starting = element('record').onclick();
  await element('record').onclick();
  assert.equal(acquisitions, 1, 'double click must not open another microphone');
  assert.equal(element('record').disabled, true);
  assert.equal(await vm.runInContext('task(() => { throw Error("must not run"); })', context), undefined);
  grant({ getTracks: () => [{ stop() { stopped++; } }] });
  await starting;
  assert.equal(element('record').disabled, false, 'Stop must remain available');
  assert.equal(element('speak').disabled, true);
  await element('speak').onclick();
  assert.equal(uploads, 0, 'competing speech must not start');
  await element('record').onclick();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(stopped, 1);
  assert.equal(uploads, 1, 'completed recording must be submitted');
  assert.equal(element('transcript').value, 'Recorded words.');
  console.log('Recorder regression passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
