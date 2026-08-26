const { chromium } = require('playwright');
const path = require('path');

// booklet.html -> PDF. Kullanim: node print-pdf.js
(async () => {
  const dir = __dirname;
  const short = process.argv.includes('--short');
  const src = 'file://' + path.join(dir, short ? 'booklet-short.html' : 'booklet.html');
  const out = path.join(dir, short ? 'Yigit-Ozen-Artbooklet-Short.pdf'
                                   : 'Yigit-Ozen-Artbooklet.pdf');

  const b = await chromium.launch();
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
