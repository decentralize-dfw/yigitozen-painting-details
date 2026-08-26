const { chromium } = require('playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args:['--no-sandbox'] });
  const p = await b.newPage({ viewport: { width: 1400, height: 1867 } });
  await p.goto('file:///home/user/yigitozen-painting-details/book/book.html', { waitUntil: 'load', timeout: 300000 });
  await p.waitForFunction(() => Array.from(document.images).every(i => i.complete && i.naturalWidth > 0), { timeout: 300000 });
  const r = await p.evaluate(() => {
    const MM = 96 / 25.4;
    const out = { distorted: [], overflow: [], overlap: [], textout: [], blank: [],
                  bleedPages: [], pages: 0, spreads: [], diagonal: [] };
    const secs = [...document.querySelectorAll('section.pg')];
    out.pages = secs.length;
    const arch = secs.map(s => s.dataset.arch || 'text');
    const info = secs.map((s, i) => {
      const sb = s.getBoundingClientRect();
      const imgs = [...s.querySelectorAll('img')].map(im => {
        const r0 = im.getBoundingClientRect();
        return { f: im.src.split('/').pop(), cut: im.classList.contains('cut') || im.classList.contains('bleed'),
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
          if (im.cut || im.w > 240) bleed = true;
          else out.overflow.push([i + 1, im.f]);
        }
      });
      // tam tasmali sayfa: en az bir gorsel dort kenardan da sayfayi asiyor ya da
      // genisligi sayfayi geciyor
      if (imgs.some(im => im.w >= 240 && im.h >= 200)) bleed = true;
      if (bleed) out.bleedPages.push(i + 1);
      for (let a = 0; a < imgs.length; a++) for (let c = a + 1; c < imgs.length; c++) {
        const A = imgs[a], B = imgs[c];
        const ox = Math.min(A.l + A.w, B.l + B.w) - Math.max(A.l, B.l);
        const oy = Math.min(A.t + A.h, B.t + B.h) - Math.max(A.t, B.t);
        if (ox > 0.5 && oy > 0.5) out.overlap.push([i + 1, A.f, B.f]);
      }
      [...s.querySelectorAll('.b')].forEach(el => {
        const r1 = el.getBoundingClientRect();
        if (r1.bottom > sb.bottom - 1 || r1.right > sb.right + 1 || r1.left < sb.left - 1)
          out.textout.push([i + 1, el.className]);
      });
      // kosegen: iki gorsel, biri sol-ust digeri sag-alt
      if (imgs.length === 2) {
        const [A, B] = imgs;
        if (A.l < 60 && A.t < 100 && B.l > 100 && B.t > 140) out.diagonal.push(i + 1);
      }
      return imgs;
    });
    // serimler: (2,3), (4,5), ...
    const EXEMPT = new Set(['P', 'S', 'R', 'text', 'plate', 'dark', 'D']);
        for (let i = 1; i < secs.length; i += 2) {
      const a = info[i] || [], c = info[i + 1] || [];
      const all = a.concat(c);
      if (all.length < 2) continue;
      const ka = arch[i], kb = arch[i + 1] || 'text';
      if (EXEMPT.has(ka) || EXEMPT.has(kb)) continue;
      const areas = all.map(x => x.w * x.h);
      const mx = Math.max(...areas), mn = Math.min(...areas);
      const tot = areas.reduce((s, x) => s + x, 0);
      out.spreads.push({ p: i + 1, n: all.length, k: ka + '|' + kb,
                         ratio: +(mx / mn).toFixed(2),
                         dom: +(mx / tot * 100).toFixed(1) });
    }
    return out;
  });
  console.log(JSON.stringify(r));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
