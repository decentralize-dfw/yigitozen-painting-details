const { chromium } = require('playwright');
const path = require('path');

// catalogue-mini.html -> PDF. Kullanim: node print-pdf.js
(async () => {
  const dir = __dirname;
  const src = 'file://' + path.join(dir, 'catalogue-mini.html');
  const out = path.join(dir, 'Yigit-Ozen-Paintings-Mini-Catalogue.pdf');

  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto(src, { waitUntil: 'load', timeout: 120000 });
  await p.waitForFunction(
    () => Array.from(document.images).every(i => i.complete && i.naturalWidth > 0),
    { timeout: 120000 }
  );
  await p.pdf({
    path: out,
    width: '210mm',
    height: '297mm',
    printBackground: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' },
    preferCSSPageSize: true,
  });
  console.log('PDF:', out);
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
