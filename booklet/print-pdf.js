const path = require('path');

// playwright ya da playwright-core, hangisi bulunursa. Tarayici yolu
// PLAYWRIGHT_CHROMIUM ile verilebilir; verilmezse paketin kendi indirdigi
// tarayici kullanilir.
function load() {
  for (const m of ['playwright', 'playwright-core']) {
    try { return require(m); } catch (e) { /* sonrakine bak */ }
  }
  throw new Error('playwright bulunamadi: npm i -D playwright-core');
}
const { chromium } = load();
const EXE = process.env.PLAYWRIGHT_CHROMIUM || '';

// booklet.html -> PDF. Kullanim: node print-pdf.js
(async () => {
  const dir = __dirname;
  const short = process.argv.includes('--short');
  const src = 'file://' + path.join(dir, short ? 'booklet-short.html' : 'booklet.html');
  const out = path.join(dir, short ? 'Yigit-Ozen-Artbooklet-Short.pdf'
                                   : 'Yigit-Ozen-Artbooklet.pdf');

  const b = await chromium.launch(
    EXE ? { executablePath: EXE, args: ['--no-sandbox'] } : {});
  const p = await b.newPage();
  await p.goto(src, { waitUntil: 'load', timeout: 180000 });
  await p.waitForFunction(
    () => Array.from(document.images).every(i => i.complete && i.naturalWidth > 0),
    { timeout: 180000 }
  );
  await p.pdf({
    path: out,
    width: '240mm',
    height: '320mm',
    printBackground: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' },
    preferCSSPageSize: true,
  });
  console.log('PDF:', out);
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
