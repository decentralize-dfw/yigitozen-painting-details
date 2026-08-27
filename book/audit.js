// Ikinci basimin denetimi. book.py sicili, serim denkligini ve aile
// ritmini derlerken tutar; burada cizilmis sayfa olculur.
//
//   node audit.js           ekran basimi: yerlesim ve olcek
//   node audit.js --print   baski ustasi: ustune etkin cozunurluk
//
// Sifir donmeyen her sey bir sayfa hatasidir.
const path = require('path');
function load() {
  for (const m of ['playwright', 'playwright-core']) {
    try { return require(m); } catch (e) { /* sonrakine bak */ }
  }
  throw new Error('playwright bulunamadi: npm i -D playwright-core');
}
const { chromium } = load();
const EXE = process.env.PLAYWRIGHT_CHROMIUM || '';
const PRINT = process.argv.includes('--print');

(async () => {
  const b = await chromium.launch(EXE ? { executablePath: EXE, args: ['--no-sandbox'] } : {});
  const p = await b.newPage({ viewport: { width: 1400, height: 1867 } });
  await p.goto('file://' + path.join(__dirname, PRINT ? 'book-print.html' : 'book.html'),
               { waitUntil: 'load', timeout: 300000 });
  await p.waitForFunction(
    () => Array.from(document.images).every(i => i.complete && i.naturalWidth > 0),
    { timeout: 300000 });
  const r = await p.evaluate((PRINT) => {
    const MM = 96 / 25.4, PA = 240 * 320;
    const out = { pages: 0, mode: PRINT ? 'print' : 'screen',
                  distorted: [], overflow: [], overlap: [], textOnImage: [], textOnText: [],
                  textout: [], blank: [], timid: [], weakDom: [],
                  lowRes: [], bleedPer32: [], clueFormula: [] };
    const secs = [...document.querySelectorAll('section.pg')];
    out.pages = secs.length;
    const fam = secs.map(s => s.dataset.fam || 'E');
    const info = secs.map((s, i) => {
      const frame = s.querySelector('.tp') || s;
      const sb = frame.getBoundingClientRect();
      const dark = s.classList.contains('dark');
      const imgs = [...s.querySelectorAll('img')].map(im => {
        const r0 = im.getBoundingClientRect();
        const w = r0.width / MM, h = r0.height / MM;
        return { f: im.src.split('/').pop(), cls: im.className || '',
                 cut: im.classList.contains('cut'),
                 butt: im.classList.contains('butt'),
                 bl:  im.classList.contains('bl'),
                 pl:  im.classList.contains('pl'),
                 ix:  im.classList.contains('ix') || im.src.endsWith('.svg'),
                 l: (r0.left - sb.left) / MM, t: (r0.top - sb.top) / MM,
                 w: w, h: h, pct: w * h / PA * 100,
                 npx: im.naturalWidth,
                 ppi: im.naturalWidth / (w / 25.4),
                 nat: im.naturalWidth / im.naturalHeight,
                 drawn: r0.width / r0.height };
      });
      if (!imgs.length && s.textContent.trim().length < 14) out.blank.push(i + 1);
      let bleed = false;
      imgs.forEach(im => {
        if (!im.cut && Math.abs(im.drawn - im.nat) / im.nat > 0.02)
          out.distorted.push([i + 1, im.f, +im.drawn.toFixed(3), +im.nat.toFixed(3)]);
        if (im.l < -0.5 || im.t < -0.5 || im.l + im.w > 240.5 || im.t + im.h > 320.5) {
          if (im.cut || im.bl || im.w > 200 || im.l < -4 || im.t < -4 ||
              im.l + im.w > 244 || im.t + im.h > 324) bleed = true;
          else out.overflow.push([i + 1, im.f]);
        }
        // Kagitta etkin cozunurluk: 240 ppi altina dusen gorsel raporlanir.
        if (PRINT && !im.f.endsWith('.svg') && im.ppi < 240)
          out.lowRes.push([i + 1, im.f, Math.round(im.ppi), +im.w.toFixed(0)]);
      });
      if (imgs.some(im => im.w >= 240 && im.h >= 200)) bleed = true;
      if (bleed) out.bleedPer32.push(i + 1);
      // Kararsiz orta boy: sayfa alaninin %4-19'u, tikiz bir en-boy orani,
      // sayfanin en buyugu ve yaninda bir esi yok. Levha, dizin, yapisik
      // kutle ve kasitli tasan kare bunun disinda.
      // Sikayetin kendisi: koca bir sayfada tek basina yuzen orta boy bir
      // gorsel. Iki ya da daha cok parca bir kompozisyondur, kural degil goz
      // yargilar; levha, dizin, yapisik kutle ve tasan kare zaten disarida.
      // Tekrar edenler bolumu disarida: orada olcek hiyerarsi degil,
      // figurun o tabloda ne kadar yer tuttugunu soyler.
      const free = imgs.filter(x => !x.ix && !x.pl && !x.butt && !x.bl && !x.cut);
      if (free.length === 1 && (s.dataset.fam || '') !== 'R') {
        const im = free[0];
        if (im.drawn > 0.5 && im.drawn < 2.0 && im.pct > 4 && im.pct < 19)
          out.timid.push([i + 1, im.f, +im.pct.toFixed(1)]);
      }
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
          out.textout.push([i + 1, el.className, el.textContent.trim().slice(0, 40)]);
        // Yazi resmin uzerine binmez; koyu sayfa ve beyaz yazi bunun disinda.
        if (dark || el.className.indexOf('wh') >= 0) return;
        const tl = (r1.left - sb.left) / MM, tt = (r1.top - sb.top) / MM;
        const tw = r1.width / MM, th = r1.height / MM;
        imgs.forEach(im => {
          const ox = Math.min(tl + tw, im.l + im.w) - Math.max(tl, im.l);
          const oy = Math.min(tt + th, im.t + im.h) - Math.max(tt, im.t);
          if (ox > 3 && oy > 3)
            out.textOnImage.push([i + 1, el.textContent.trim().slice(0, 30), im.f]);
        });
      });
      // Yazi yaziya binmez: iki kunye ust uste dusunce ikisi de okunmaz.
      const tb = [...s.querySelectorAll('.b')].map(el => {
        const r1 = el.getBoundingClientRect();
        return { t: el.textContent.trim(), l: (r1.left - sb.left) / MM,
                 y: (r1.top - sb.top) / MM, w: r1.width / MM, h: r1.height / MM };
      }).filter(x => x.t.length);
      for (let a2 = 0; a2 < tb.length; a2++) for (let c2 = a2 + 1; c2 < tb.length; c2++) {
        const A = tb[a2], B = tb[c2];
        const ox = Math.min(A.l + A.w, B.l + B.w) - Math.max(A.l, B.l);
        const oy = Math.min(A.y + A.h, B.y + B.h) - Math.max(A.y, B.y);
        if (ox > 2 && oy > 1.5)
          out.textOnText.push([i + 1, A.t.slice(0, 24), B.t.slice(0, 24)]);
      }
      return imgs;
    });
    for (let i = 1; i < secs.length - 1; i += 2) {
      let all = (info[i] || []).concat(info[i + 1] || []);
      const seen = new Set();          // sirti gecen bant bir kez sayilir
      all = all.filter(im => {
        const k2 = im.f + '|' + im.w.toFixed(1) + '|' + im.h.toFixed(1);
        if (seen.has(k2)) return false;
        seen.add(k2); return true;
      });
      const k = fam[i];
      if (all.length > 1) {
        const areas = all.map(x => x.w * x.h).sort((x, y) => y - x);
        const tot = areas.reduce((s2, x) => s2 + x, 0);
        // B: tartisma serimi tek bir ozne uzerine kurulur, ozne serimin
        // yarisini tutar. C: dizi serimi bir siradir, aranan hakimiyet
        // degil gorunur bir kademe: en buyuk, ikinciyi bir buçuk katlar.
        if (k === 'B' && Math.max(...areas) / tot * 100 < 50)
          out.weakDom.push([i + 1, k, +(Math.max(...areas) / tot * 100).toFixed(1)]);
        if (k === 'C' && areas.length > 1 && areas[0] / areas[1] < 1.5)
          out.weakDom.push([i + 1, k, 'step ' + (areas[0] / areas[1]).toFixed(2)]);
      }
      // "Kucuk ipucu, karsisinda tam tasan gorsel" jesti: kitapta en cok uc kez.
      const L = info[i] || [], R = info[i + 1] || [];
      const pair = [[L, R], [R, L]];
      pair.forEach(([a, c]) => {
        if (a.length === 1 && a[0].cut && a[0].pct > 90 &&
            c.length >= 1 && c.length <= 2 &&
            Math.max(...c.map(x => x.pct)) < 6)
          out.clueFormula.push(i + 1);
      });
    }
    const per = [];
    for (let s0 = 0; s0 < secs.length; s0 += 32)
      per.push(out.bleedPer32.filter(x => x > s0 && x <= s0 + 32).length);
    out.bleedPer32 = per;
    return out;
  }, PRINT);
  const hard = r.distorted.length + r.overflow.length + r.overlap.length +
               r.textout.length + r.blank.length + r.timid.length +
               r.weakDom.length + r.textOnImage.length + r.textOnText.length +
               (r.clueFormula.length > 3 ? 1 : 0);
  console.log(JSON.stringify(r, null, 1));
  console.log('clue-formula spreads: %d (limit 3)', r.clueFormula.length);
  if (PRINT) console.log('images under 240 ppi: %d', r.lowRes.length);
  console.log(hard ? 'AUDIT: %d finding(s)' : 'AUDIT: clean', hard);
  await b.close();
  process.exit(hard ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
