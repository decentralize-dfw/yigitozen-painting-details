const path = require('path');

// book.html -> PDF.  playwright ya da playwright-core, hangisi varsa;
// tarayici yolu PLAYWRIGHT_CHROMIUM ile verilebilir.
function load() {
  for (const m of ['playwright', 'playwright-core']) {
    try { return require(m); } catch (e) { /* sonrakine bak */ }
  }
  throw new Error('playwright bulunamadi: npm i -D playwright-core');
}
const { chromium } = load();
const EXE = process.env.PLAYWRIGHT_CHROMIUM || '';

(async () => {
  const dir = __dirname;
  const short = process.argv.includes('--short');
  // Baski ustasi 246 x 326 mm basilir: kesim 240 x 320, her kenarda 3 mm
  // tasma payi. Ekran basimi kesim olcusunde kalir.
  const bleed = process.argv.includes('--print');
  const file  = bleed ? 'book-print.html' : (short ? 'book-short.html' : 'book.html');
  const src = 'file://' + path.join(dir, file);
  const out = path.join(dir, bleed ? 'Yigit-Ozen-Paintings-Print-Master.pdf'
                        : short ? 'Yigit-Ozen-Paintings-Short.pdf'
                                : 'Yigit-Ozen-Paintings-since-2019.pdf');
  const b = await chromium.launch(EXE ? { executablePath: EXE, args: ['--no-sandbox'] } : {});
  const p = await b.newPage();
  await p.goto(src, { waitUntil: 'load', timeout: 300000 });
  await p.waitForFunction(
    () => Array.from(document.images).every(i => i.complete && i.naturalWidth > 0),
    { timeout: 300000 });
  await p.pdf({ path: out,
                width:  bleed ? '246mm' : '240mm',
                height: bleed ? '326mm' : '320mm',
                printBackground: true,
                margin: { top: '0', right: '0', bottom: '0', left: '0' },
                preferCSSPageSize: !bleed });
  console.log('PDF:', out);
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
