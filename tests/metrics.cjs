// Exercise the actual inline aggregation without a browser or chart mocks.
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const template = readFileSync(resolve(__dirname, '../mergeprint/template.html'), 'utf8');
const source = template.split('<script>')[1].split('const tipEl =')[0];
const fixture = {
  account: 'fixture', start: '2026-01-01', end: '2026-01-31', bigPr: 10000, backlogComplete: true,
  settings: { country: '', timezone: 'UTC', holidays: [], offDays: [], events: [] }, holidays: {},
  repos: ['fixture/a', 'fixture/b'],
  prs: [
    ['2026-01-01T12:00:00Z', '2026-01-05T12:00:00Z', '2026-01-05T12:00:00Z', 0, [10, 0, 1], 1],
    ['2026-01-01T12:00:00Z', '2026-01-20T12:00:00Z', '2026-01-20T12:00:00Z', 1, [30, 0, 1], 2],
    ['2025-12-01T12:00:00Z', '', '', 0, null, 3],
  ],
  issues: [['2026-01-03T12:00:00Z', 0], ['2026-01-04T12:00:00Z', 1]],
};
function run(code, data = fixture, saved = {}) {
  const context = vm.createContext({ localStorage: { getItem: () => JSON.stringify(saved) } });
  vm.runInContext(source.replace('__DATA__', JSON.stringify(data)), context);
  return JSON.parse(vm.runInContext(`JSON.stringify((() => { ${code} })())`, context));
}
test('repository filters include issues and selected repository counts', () => {
  assert.deepEqual(run('repoSel=0; const r=compute(); return [r.stats.merged,r.stats.issues,r.stats.repoCount];'), [1, 1, 1]);
});
test('backlog includes open PRs and later closures, regardless of selected end date', () => {
  assert.deepEqual(run("return [compute().wkOpenEnd[1],compute('2026-01-01','2026-01-11').wkOpenEnd[1]];"), [2, 2]);
});
test('last partial week is evaluated at the selected end date', () => {
  assert.equal(run("return compute('2026-01-01','2026-01-19').stats.openAtEnd;"), 2);
});
test('single-day and empty selections produce finite values', () => {
  assert.deepEqual(run("const r=compute('2026-01-02','2026-01-02'); return [r.days.length,r.stats.merged,r.stats.issues,r.stats.perBiz,r.stats.openAtEnd];"), [1, 0, 0, 0, 3]);
});
test('median averages the two central values for even samples', () => {
  assert.deepEqual(run('const r=compute(); return [r.stats.ttmMedian,r.stats.locMedian];'), [276, 20]);
});
test('rolling windows retain data before the selected start', () => {
  assert.deepEqual(run("return [compute().rollPr[9],compute('2026-01-10','2026-01-31').rollPr[0]];"), [0.14, 0.14]);
});
test('timezone boundaries and DST use local calendar dates', () => {
  assert.deepEqual(run("const loc=localizer('Europe/Copenhagen');return [loc('2026-03-28T23:30:00Z'),loc('2026-03-29T01:30:00Z')].map(t=>[t.date,t.hour]);"), [['2026-03-29', 0], ['2026-03-29', 3]]);
});
test('invalid dates and enormous off-day ranges do not crash or expand unboundedly', () => {
  assert.equal(run("return parseDates('0001-01-01..9999-12-31\\n2026-99-99..2026-99-99').size;"), 31);
});
test('saved date ranges outside the new snapshot reset to its collected range', () => {
  assert.deepEqual(run('return [ST.from,ST.to];', fixture, {from:'2025-01-01',to:'2025-01-31'}), ['2026-01-01', '2026-01-31']);
});
test('legacy snapshots do not claim a complete backlog', () => {
  assert.equal(run('return compute().stats.openAtEnd;', {...fixture, backlogComplete:false}), null);
});
