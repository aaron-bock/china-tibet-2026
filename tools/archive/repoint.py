#!/usr/bin/env python3
"""Re-point a 2026-09-10 archived page's banner at the dossier.

Those three pages were archived on 10 September with a banner naming the master
document "Xi'an, Everest, Disneytown" in bold text and no link. That document is
itself archived now, and its name changed to "Itinerary", so the pointer is both
stale and unclickable. This rewrites the banner body to link the dossier, leaving
the "Archived 10 September 2026" heading alone -- that date is the historical fact
and should not move.
"""
import re, sys

NEW = "https://claude.ai/code/artifact/eccc0f6c-dc3a-4c08-8381-905dee78f9ff"

BODY = ('Everything here now lives in the <a href="%s" '
        'style="color:#5c1a14;font-weight:600">China &amp; Tibet 2026 dossier</a>, '
        'which became the single source of truth for this trip on 12 September 2026. '
        'The master document this page originally pointed at was archived the same day. '
        'Kept only as a record of what this said before the merge.' % NEW)


# the harness's publish wrapper is recognisable by its own reset rule
WRAPPER = '[hidden]:not([hidden=until-found i])'


def fragment(html):
    """Return page content only.

    Two shapes arrive here. `action: "read"` on a large artifact saves the
    *rendered* page, which opens with the harness's doctype/head/body wrapper
    and has to be unwrapped. `action: "read_file"` on index.html gives the file
    exactly as it was uploaded, with no wrapper -- pass that through untouched,
    because re-deriving it can only lose bytes.
    """
    if WRAPPER not in html.split('<body', 1)[0]:
        return html
    m = re.search(r'(?is)<body[^>]*>', html)
    inner = html[m.end():] if m else html
    # drop the wrapper's own closing tags; keep any the page declares itself
    return re.sub(r'(?is)\s*</body>\s*</html>\s*\Z', '\n', inner)


def repoint(inner):
    if NEW in inner:
        return None, 'already points at the dossier'
    # the banner is one div; replace everything after its <strong>...</strong>
    m = re.search(r'(?is)(<div style="background:#F8E3E1.*?</strong>)(.*?)(</div>)', inner)
    if not m:
        return None, 'banner not found'
    return inner[:m.end(1)] + '\n' + BODY + '\n' + inner[m.start(3):], None


def main():
    src, dst = sys.argv[1], sys.argv[2]
    inner = fragment(open(src, encoding='utf-8').read())
    out, err = repoint(inner)
    if err:
        print('skip: ' + err); return 1
    open(dst, 'w', encoding='utf-8').write(out)
    print('wrote %s (%d bytes, %d banner)' % (dst, len(out), out.count('Archived 10 September 2026')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
