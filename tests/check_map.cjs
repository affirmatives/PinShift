const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

async function check(query, expectedCenter) {
  const elements = new Map();
  const element = () => ({ textContent: '', innerHTML: '', value: '', addEventListener() {}, appendChild() {}, focus() {} });
  let options;
  const selected = [];
  const styles = [];
  const centers = [];
  const bridge = { log() {}, selectPoint: (...point) => selected.push(point) };
  const poi = { id: 'result', name: '地点', location: { getLng: () => 120.1, getLat: () => 30.2 } };
  const amap = {
    Map: class {
      constructor(id, config) { options = config; }
      setMapStyle(style) { styles.push(style); }
      on() {} off() {} resize() {} setZoomAndCenter(zoom, point) { centers.push(Array.from(point)); } add() {}
      getCity(callback) { callback({ city: '杭州市' }); }
    },
    Marker: class { setPosition() {} },
    PlaceSearch: class { search(keyword, callback) { callback('complete', { poiList: { pois: [poi] } }); } },
  };
  const window = { location: { search: query }, AMap: amap, qt: { webChannelTransport: {} }, QWebChannel: true };
  const context = {
    window, AMap: amap, URLSearchParams, setTimeout() {},
    QWebChannel: class { constructor(transport, callback) { callback({ objects: { pinShiftBridge: bridge } }); } },
    document: { documentElement: { dataset: {} }, getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); }, createElement: element },
  };
  vm.runInNewContext(fs.readFileSync('web/map.js', 'utf8'), context);
  await new Promise(setImmediate);
  assert.deepEqual(Array.from(options.center), expectedCenter);
  assert.equal(options.mapStyle, query.includes('theme=dark') ? 'amap://styles/dark' : 'amap://styles/normal');
  window.PinShiftMap.setTheme('dark');
  assert.equal(context.document.documentElement.dataset.theme, 'dark');
  window.PinShiftMap.setTheme('light');
  assert.equal(context.document.documentElement.dataset.theme, 'light');
  assert.deepEqual(styles, ['amap://styles/dark', 'amap://styles/normal']);
  assert.deepEqual(Array.from(options.center), expectedCenter);
  await window.PinShiftMap.search('地点');
  assert.deepEqual(selected, [[120.1, 30.2]]);
  window.PinShiftMap.setSelectedLocation(-77.036546, 38.897660);
  assert.deepEqual(centers.at(-1), [-77.036546, 38.897660]);
  assert.deepEqual(selected, [[120.1, 30.2]]);
}
(async () => {
  await check('?key=test&securityJsCode=test', [120.15507, 30.274085]);
  await check('?key=test&securityJsCode=test&lastLng=121.5&lastLat=31.2', [121.5, 31.2]);
  await check('?key=test&securityJsCode=test&lastLng=0&lastLat=0', [0, 0]);
  await check('?key=test&securityJsCode=test&theme=dark', [120.15507, 30.274085]);
  console.log('Map regression checks passed: default center, remembered coordinates, search selection.');
})().catch(error => { console.error(error); process.exitCode = 1; });
