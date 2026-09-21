/* An HTML print sheet -> PDF, via headless Chromium.
 *
 *   node tools/render_packing_pdf.mjs <in.html> <out.pdf> [options]
 *     --max-pages N          fail, and write nothing, if the result exceeds N pages
 *     --margins T,R,B,L      default 14mm,13mm,16mm,13mm (the packing list's)
 *     --footer "Text"        running footer; "" for none. Default "Packing list".
 *     --landscape            Letter on its side, for sheets imposed two-up.
 *
 * MARGINS MUST MATCH the @page margins in the generating script. Chromium takes
 * its own, and where they disagree the smaller wins silently and the footer
 * creeps up into the last row of content. They were hard-wired to the packing
 * list's until the leave-behind sheet arrived with different ones and a footer
 * of its own — which is why they are arguments now.
 */
import { pathToFileURL } from 'node:url';

const [src, out, ...rest] = process.argv.slice(2);
if (!src || !out) {
  console.error('usage: node tools/render_packing_pdf.mjs <in.html> <out.pdf> [--max-pages N] [--landscape]');
  process.exit(1);
}
/* The leave-behind sheet has to be ONE page, and "it was one page last time I
 * looked" is not a guarantee — Chromium paginates a little tighter than a
 * viewport measurement suggests, so the boundary is easy to cross by accident.
 * Passing --max-pages makes the build fail instead of quietly shipping two. */
const opt = (name, dflt) => {
  const i = rest.indexOf('--' + name);
  return i >= 0 ? rest[i + 1] : dflt;
};
const maxPages = Number(opt('max-pages', 0));
const [mt, mr, mb, ml] = opt('margins', '14mm,13mm,16mm,13mm').split(',').map(x => x.trim());
const footer = opt('footer', 'Packing list');
/* The field guide is half-letter pages printed two to a landscape Letter sheet
 * and cut down the middle, so the SHEET is landscape even though every page on
 * it is portrait. Chromium needs telling; the generating script's @page size
 * has to say the same thing. */
const landscape = rest.includes('--landscape');

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
  landscape,
  printBackground: true,
  displayHeaderFooter: !!footer,
  headerTemplate: '<div></div>',
  footerTemplate: footer
    ? '<div style="width:100%;font:7pt \'Liberation Mono\',monospace;color:#8b95a2;padding:0 ' + mr + ';text-align:right;">'
      + footer.replace(/[<>&]/g, '') + ' &middot; <span class="pageNumber"></span> / <span class="totalPages"></span></div>'
    : '<div></div>',
  margin: { top: mt, right: mr, bottom: mb, left: ml }
});
await b.close();

if (maxPages > 0) {
  const { readFileSync, unlinkSync } = await import('node:fs');
  const buf = readFileSync(out);
  const pages = (buf.toString('latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
  if (pages > maxPages) {
    unlinkSync(out);
    console.error(`render: ${pages} pages, limit ${maxPages}. Nothing written — shorten the source.`);
    process.exit(1);
  }
  console.log(`wrote ${out} — ${pages} page${pages === 1 ? '' : 's'}, within the limit of ${maxPages}`);
} else {
  console.log('wrote ' + out + (errs.length ? ' — page errors: ' + errs.join(' | ') : ''));
}
