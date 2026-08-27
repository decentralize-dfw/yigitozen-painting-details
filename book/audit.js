// Ikinci basimin denetimi. book.py sicili ve aile ritmini derlerken tutar;
// burada cizilmis sayfa olculur: bicimi bozuk gorsel, tasan gorsel, ustuste
// binme, marj disina cikan yazi, bos sayfa, urkek ara boy, ve tartisma ile
// dizi serimlerinde egemenin payi. Sifir donmeyen her sey bir sayfa hatasidir.
const path = require('path');
function load() {
  for (const m of ['playwright', 'playwright-core']) {
    try { return require(m); } catch (e) { /* sonrakine bak */ }
  }
  throw new Error('playwright bulunamadi: npm i -D playwright-core');
}
const { chromium } = load();
const EXE = process.env.PLAYWRIGHT_CHROMIUM || '';

(async () => {
  const b = await chromium.launch(EXE ? { executablePath: EXE, args: ['--no-sandbox'] } : {});
  const p = await b.newPage({ viewport: { width: 1400, height: 1867 } });
  await p.goto('file://' + path.join(__dirname, 'book.html'),
               { waitUntil: 'load', timeout: 300000 });
  await p.waitForFunction(
    () => Array.from(document.images).every(i => i.complete && i.naturalWidth > 0),
    { timeout: 300000 });
  const r = await p.evaluate(() => {
    const MM = 96 / 25.4;
    const out = { pages: 0, distorted: [], overflow: [], overlap: [], textout: [],
                  blank: [], timid: [], weakDom: [], bleedPer32: [], spans: [] };
    const secs = [...document.querySelectorAll('section.pg')];
    out.pages = secs.length;
    const fam = secs.map(s => s.dataset.fam || 'E');
    const info = secs.map((s, i) => {
      const sb = s.getBoundingClientRect();
      const imgs = [...s.querySelectorAll('img')].map(im => {
        const r0 = im.getBoundingClientRect();
        return { f: im.src.split('/').pop(),
                 cut: im.classList.contains('cut'),
                 butt: im.classList.contains('butt'),
                 ix: im.classList.contains('ix') || im.src.endsWith('.svg'),
                 l: (r0.left - sb.left) / MM, t: (r0.top - sb.top) / MM,
                 w: r0.width / MM, h: r0.height / MM,
                 nat: im.naturalWidth / im.naturalHeight,
                 drawn: r0.width / r0.height };
      });
      if (!imgs.length && s.textContent.trim().length < 14) out.blank.push(i + 1);
      let bleed = false;
      imgs.forEach(im => {
        if (!im.cut && Math.abs(im.drawn - im.nat) / im.nat > 0.02)
          out.distorted.push([i + 1, im.f, +im.drawn.toFixed(3), +im.nat.toFixed(3)]);
        if (im.l < -0.5 || im.t < -0.5 || im.l + im.w > 240.5 || im.t + im.h > 320.5) {
          if (im.cut || im.w > 200 || im.l < -4 || im.t < -4 ||
              im.l + im.w > 244 || im.t + im.h > 324) bleed = true;
          else out.overflow.push([i + 1, im.f]);
        }
        // 49-64 mm arasi urkek ara boy: ne SUP ne INDEX. Yapisik kutle
        // hucreleri tek resim sayilir ve muaftir.
        if (!im.ix && !im.butt && im.w > 49.5 && im.w < 64.5)
          out.timid.push([i + 1, im.f, +im.w.toFixed(1)]);
      });
      if (imgs.some(im => im.w >= 240 && im.h >= 200)) bleed = true;
      if (bleed) out.bleedPer32.push(i + 1);
      for (let a = 0; a < imgs.length; a++) for (let c = a + 1; c < imgs.length; c++) {
        const A = imgs[a], B = imgs[c];
        if (A.butt && B.butt) continue;
        const ox = Math.min(A.l + A.w, B.l + B.w) - Math.max(A.l, B.l);
        const oy = Math.min(A.t + A.h, B.t + B.h) - Math.max(A.t, B.t);
        if (ox > 0.5 && oy > 0.5) out.overlap.push([i + 1, A.f, B.f]);
      }
      [...s.querySelectorAll('.b')].forEach(el => {
        const r1 = el.getBoundingClientRect();
        if (r1.bottom > sb.bottom - 1 || r1.right > sb.right + 1 || r1.left < sb.left - 1)
          out.textout.push([i + 1, el.className, el.textContent.slice(0, 40)]);
      });
      return imgs;
    });
    // Serimler: (2,3), (4,5)... B ve C serimlerinde egemen, serimdeki gorsel
    // alaninin yarisindan azsa serim zayiftir.
    for (let i = 1; i < secs.length - 1; i += 2) {
      let all = (info[i] || []).concat(info[i + 1] || []);
      // sirti gecen bant iki sayfada ayni dosyayla cizilir; bir kez sayilir
      const seen = new Set();
      all = all.filter(im => {
        const k2 = im.f + '|' + im.w.toFixed(1) + '|' + im.h.toFixed(1);
        if (seen.has(k2)) return false;
        seen.add(k2); return true;
      });
      const k = fam[i];
      if ((k === 'B' || k === 'C') && all.length > 1) {
        const areas = all.map(x => x.w * x.h);
        const mx = Math.max(...areas);
        const tot = areas.reduce((s2, x) => s2 + x, 0);
        const dom = mx / tot * 100;
        if (dom < 50) out.weakDom.push([i + 1, k, +dom.toFixed(1)]);
      }
      // sirti gecen gorsel: elle secilmis kadrajlar; rapor, yasak degil
      (info[i] || []).forEach(im => {
        if (im.l + im.w > 242 && im.w > 100) out.spans.push([i + 1, im.f]);
      });
    }
    // 32'lik bloklarda tasan sayfa sayisi
    const per = [];
    for (let s0 = 0; s0 < secs.length; s0 += 32) {
      per.push(out.bleedPer32.filter(x => x > s0 && x <= s0 + 32).length);
    }
    out.bleedPer32 = per;
    return out;
  });
  const bad = r.distorted.length + r.overflow.length + r.overlap.length +
              r.textout.length + r.blank.length + r.timid.length + r.weakDom.length;
  console.log(JSON.stringify(r, null, 1));
  console.log(bad ? 'AUDIT: %d finding(s)' : 'AUDIT: clean', bad);
  await b.close();
  process.exit(bad ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
