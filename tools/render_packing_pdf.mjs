/* print-packing.html -> China-Tibet-2026-packing-list.pdf, via headless Chromium.
 *
 *   node tools/render_packing_pdf.mjs <in.html> <out.pdf>
 *
 * The margins here must stay equal to the @page margins in tools/packing_pdf.py:
 * Chromium takes its own, and where they disagree the smaller one wins silently
 * and the footer creeps up into the last row of a bag.
 */
import { pathToFileURL } from 'node:url';

const [src, out] = process.argv.slice(2);
if (!src || !out) {
  console.error('usage: node tools/render_packing_pdf.mjs <in.html> <out.pdf>');
  process.exit(1);
}

/* The repo has no node_modules and should not grow one for a script that runs
 * twice a year. Node resolves a bare import against THIS file's directory, so
 * fall back to the working directory, which is where playwright is installed. */
async function playwright() {
  try {
    return await import('playwright');
  } catch (e) {
    if (e.code !== 'ERR_MODULE_NOT_FOUND') throw e;
    const local = pathToFileURL(process.cwd() + '/node_modules/playwright/index.mjs').href;
    return await import(local).catch(() => {
      console.error('playwright not found. Run this from a directory that has it installed,\n'
                  + 'or `npm i playwright` there first.');
      process.exit(1);
    });
  }
}
const { chromium } = await playwright();

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage();
const errs = [];
p.on('pageerror', e => errs.push(String(e)));
await p.goto('file://' + (src.startsWith('/') ? src : process.cwd() + '/' + src), { waitUntil: 'load' });
await p.emulateMedia({ media: 'print' });
await p.pdf({
  path: out,
  format: 'Letter',
  printBackground: true,
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: '<div style="width:100%;font:7pt \'Liberation Mono\',monospace;color:#8b95a2;padding:0 13mm;text-align:right;">'
    + 'Packing list &middot; <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
  margin: { top: '14mm', right: '13mm', bottom: '16mm', left: '13mm' }
});
await b.close();
console.log('wrote ' + out + (errs.length ? ' — page errors: ' + errs.join(' | ') : ''));
