# -*- coding: utf-8 -*-
"""
booklet-layout.json -> InDesign paketi (IDML)

Kitabi InDesign'in kendi acik bicimi olan IDML olarak yazar. Cikan sey
duz bir resim degildir: her yazi kendi cercevesinde gercek yazidir, her
cizgi bir nesnedir, her gorsel bagli bir dosyadir ve hepsi paragraf ve
karakter stillerine baglidir. Bir altyazinin puntosunu degistirmek icin
stili degistirmek yeter, uc yuz altyaziyi tek tek acmak gerekmez.

    python3 to-indesign.py booklet-layout.json
    python3 to-indesign.py booklet-layout.json --web    # ekran seti

Ciktisi bir klasordur:

    Yigit-Ozen-Paintings-InDesign/
        Yigit-Ozen-Paintings.idml     <- InDesign bunu acar
        Links/                        <- bagli gorseller, baski cozunurlugunde
        Document fonts/               <- Inter ve Newsreader

"Document fonts" klasoru IDML'in yanindaysa InDesign yazi tiplerini
dosyayi acarken kendisi devreye alir; sisteme kurmak gerekmez.
"""
import os, sys, json, re, zipfile, shutil, math, html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir))
SITE = os.path.abspath(os.path.join(REPO, os.pardir, 'yigit'))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
WEB = '--web' in sys.argv
SRC = ARGS[0] if ARGS else os.path.join(REPO, 'editor', 'model.json')
OUTDIR = os.path.join(REPO, 'Yigit-Ozen-Paintings-InDesign')

from PIL import Image
Image.MAX_IMAGE_PIXELS = None

PT = 72.0 / 25.4                     # milimetre -> punto
PW, PH = 240.0 * PT, 320.0 * PT      # sayfa
BLEED = 3.0 * PT

CAND = [os.path.join(REPO, 'editor'), os.path.join(SITE, 'booklet-editor')]
ROOTS = [d for d in CAND if os.path.isdir(os.path.join(d, 'img'))]
SETS = [os.path.join(HERE, 'images-print'), os.path.join(HERE, 'images')]

MAN = {}
for d in SETS:
    p = os.path.join(d, 'manifest.json')
    if os.path.isfile(p):
        for k, v in json.load(open(p, encoding='utf-8')).items():
            if k not in MAN or v.get('srcpx', 0) > MAN[k].get('srcpx', 0): MAN[k] = v


# ── stiller: book.css'teki dort kademe, InDesign stillerine ────────
# Her yazi sinifi bir paragraf stili olur. Boylece kitabin tipografisi
# InDesign'da da tek yerden yonetilir.
INTER, NEWS = 'Inter', 'Newsreader'
PSTYLES = {
    # ad            : (aile, kesim, punto, satir, buyukharf, renk, hiza, harf araligi)
    'm':      (INTER, 'SemiBold', 7.6,  11.1, 1, 'ink',   'Left',   70),
    'm g':    (INTER, 'Medium',   7.6,  11.1, 1, 'grey',  'Left',   70),
    'm rt':   (INTER, 'SemiBold', 7.6,  11.1, 1, 'ink',   'Right',  70),
    'm rt g': (INTER, 'Medium',   7.6,  11.1, 1, 'grey',  'Right',  70),
    'm g rt': (INTER, 'Medium',   7.6,  11.1, 1, 'grey',  'Right',  70),
    'm ct':   (INTER, 'SemiBold', 7.6,  11.1, 1, 'ink',   'Center', 70),
    'm wn':   (INTER, 'SemiBold', 10.4, 15.2, 1, 'ink',   'Left',   50),
    'm wh':   (INTER, 'SemiBold', 7.6,  11.1, 1, 'paper', 'Left',   70),
    'm rt wh':(INTER, 'SemiBold', 7.6,  11.1, 1, 'paper', 'Right',  70),
    'f':      (INTER, 'SemiBold', 8.2,  8.2,  0, 'ink',   'Left',   40),
    'f rt':   (INTER, 'SemiBold', 8.2,  8.2,  0, 'ink',   'Right',  40),
    't':      (NEWS,  'Regular',  10.8, 15.1, 0, 'ink',   'Left',    4),
    'sans':   (INTER, 'Regular',  9.6,  13.8, 0, 'ink',   'Left',    2),
    'q':      (NEWS,  'Italic',   13.4, 18.5, 0, 'ink',   'Left',    0),
    'pq':     (NEWS,  'Italic',   27.0, 35.1, 0, 'ink',   'Left',   -5),
    'pq mid': (NEWS,  'Italic',   20.0, 26.8, 0, 'ink',   'Left',   -5),
    'pq big': (NEWS,  'Italic',   44.0, 48.4, 0, 'ink',   'Left',   -5),
    'd':      (INTER, 'Bold',     26.0, 27.0, 0, 'ink',   'Left',  -22),
    'd s':    (INTER, 'Bold',     19.0, 19.8, 0, 'ink',   'Left',  -16),
    'd l':    (INTER, 'Bold',     44.0, 43.1, 0, 'ink',   'Left',  -30),
    'd xl':   (INTER, 'Bold',     64.0, 60.2, 0, 'ink',   'Left',  -35),
    'd yr':   (INTER, 'Bold',    108.0, 92.9, 0, 'ink',   'Left',  -45),
    'd l wh': (INTER, 'Bold',     44.0, 43.1, 0, 'paper', 'Left',  -30),
}
# Yazi icindeki isaretler. book.css'te .m i egik degil, gri demektir:
# bu ayrim korunur, yoksa kunyeler InDesign'da egik cikar.
CSTYLES = {
    'grey':   (None, 'Medium',   'grey'),      # .m i
    'bold':   (None, 'Bold',     None),        # b
    'italic': (None, 'Italic',   None),        # em, i (govde yazisinda)
    'place':  (None, 'Medium',   'grey'),      # .f span
    'greywh': (None, 'Medium',   'paperdim'),  # koyu sayfada .m i
}
COLORS = {'ink': (0x11, 0x11, 0x11), 'grey': (0x6e, 0x6e, 0x6e),
          'hair': (0xd8, 0xd8, 0xd8), 'paper': (0xff, 0xff, 0xff),
          'paperdim': (0xbd, 0xbd, 0xbd), 'dark': (0x0c, 0x0c, 0x0c)}

FONTFILE = {(INTER, 'Regular'): 'Inter-400.ttf', (INTER, 'Medium'): 'Inter-500.ttf',
            (INTER, 'SemiBold'): 'Inter-600.ttf', (INTER, 'Bold'): 'Inter-700.ttf',
            (INTER, 'Italic'): 'Inter-Italic-400.ttf',
            (NEWS, 'Regular'): 'Newsreader-400.ttf',
            (NEWS, 'Medium'): 'Newsreader-500.ttf',
            (NEWS, 'Italic'): 'Newsreader-Italic-400.ttf'}


def x(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


# ── yazi: HTML parcasi -> InDesign kosulari ─────────────────────────
def runs(frag, base_cls, dark):
    """<b>, <i>, <em>, <span>, <br>, <p> -> (karakter stili, metin) dizisi.

    Donen her oge bir kosudur; None stil, paragrafin kendi stilidir.
    Paragraf sinirlari '\n' ile verilir.
    """
    micro = base_cls.split()[0] == 'm'
    folio = base_cls.split()[0] == 'f'
    out, stack = [], []
    pos = 0
    frag = frag.replace('\n', ' ')
    for mt in re.finditer(r'<(/?)(\w+)[^>]*>', frag):
        t = frag[pos:mt.start()]
        if t: out.append((stack[-1] if stack else None, t))
        pos = mt.end()
        close, tag = mt.group(1), mt.group(2).lower()
        if tag == 'br':
            # InDesign'da zorlanmis satir sonu U+2028'dir; <br> tam olarak
            # budur. Paragraf sonu degildir, o asagida <Br/> ile verilir.
            out.append((None, u'\u2028'))
        elif tag == 'p':
            if close: out.append((None, '\n'))
        elif tag in ('b', 'strong'):
            (stack.pop() if close and stack else stack.append('bold'))
        elif tag in ('i', 'em'):
            if close:
                if stack: stack.pop()
            else:
                # .m icinde <i> gri demektir, egik degil
                stack.append(('greywh' if dark else 'grey') if (micro and tag == 'i')
                             else 'italic')
        elif tag == 'span':
            if close:
                if stack: stack.pop()
            else:
                stack.append('place' if folio else (
                    'greywh' if dark else 'grey'))
    t = frag[pos:]
    if t: out.append((stack[-1] if stack else None, t))
    # varlik cozumlemesi ve bos kosularin atilmasi
    res = []
    for c, t in out:
        t = _html.unescape(t)
        if t: res.append((c, t))
    return res


def plain(frag):
    return _html.unescape(re.sub(r'<[^>]+>', '', frag))


# ── gorsel ─────────────────────────────────────────────────────────
def picture(base):
    """Bagli dosyanin yolu ve piksel olcusu."""
    folders = (['img'] if WEB else ['img-print', 'img'])
    for d in ROOTS:
        for f in folders:
            p = os.path.join(d, f, base)
            if os.path.isfile(p): return p
    for d in (SETS[::-1] if WEB else SETS):
        p = os.path.join(d, base)
        if os.path.isfile(p): return p
    return None


UID = [0]
def uid(pre='u'):
    UID[0] += 1
    return '%s%x' % (pre, 1000 + UID[0])


AID = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
       '<?aid style="50" type="%s" readerVersion="6.0" featureSet="257" '
       'product="18.0(100)"?>\n')
NS = 'xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"'
DOM = 'DOMVersion="18.0"'


def geom(x1, y1, x2, y2):
    """Dikdortgen yolu. Kose noktalari saat yonunde, egri yok."""
    p = []
    for ax, ay in ((x1, y1), (x1, y2), (x2, y2), (x2, y1)):
        p.append('<PathPointType Anchor="%.4f %.4f" LeftDirection="%.4f %.4f" '
                 'RightDirection="%.4f %.4f"/>' % (ax, ay, ax, ay, ax, ay))
    return ('<Properties><PathGeometry><GeometryPathType PathOpen="false">'
            '<PathPointArray>%s</PathPointArray></GeometryPathType>'
            '</PathGeometry></Properties>' % ''.join(p))


def fonts_xml():
    fams = {}
    for (fam, sty) in FONTFILE: fams.setdefault(fam, []).append(sty)
    out = []
    for fam, stys in fams.items():
        f = ['<FontFamily Self="%s" Name="%s">' % (uid('fam'), x(fam))]
        for s in sorted(set(stys)):
            f.append('<Font Self="%s" FontFamily="%s" Name="%s&#9;%s" '
                     'PostScriptName="%s-%s" Status="Installed" FontStyleName="%s" '
                     'FontType="TrueType" WritingScript="0" FullName="%s %s" '
                     'FullNameNative="%s %s" FontStyleNameNative="%s" '
                     'PlatformName="%s-%s" Version="1.000"/>'
                     % (uid('fnt'), x(fam), x(fam), x(s), x(fam), x(s), x(s),
                        x(fam), x(s), x(fam), x(s), x(s), x(fam), x(s)))
        f.append('</FontFamily>')
        out.append(''.join(f))
    return (AID % 'fonts' + '<idPkg:Fonts %s %s>%s</idPkg:Fonts>'
            % (NS, DOM, ''.join(out)))


def graphic_xml():
    sw = ['<Swatch Self="Swatch/$ID/[None]" Name="$ID/[None]" '
          'ColorEditable="false" ColorRemovable="false" Visible="true" '
          'SwatchCreatorID="7937"/>',
          '<Color Self="Color/$ID/[Paper]" Model="Process" Space="CMYK" '
          'ColorValue="0 0 0 0" ColorOverride="Specialpaper" '
          'Name="$ID/[Paper]" ColorEditable="false" ColorRemovable="false" '
          'Visible="true" SwatchCreatorID="7937"/>',
          '<Color Self="Color/$ID/[Black]" Model="Process" Space="CMYK" '
          'ColorValue="0 0 0 100" ColorOverride="Specialblack" '
          'Name="$ID/[Black]" ColorEditable="false" ColorRemovable="false" '
          'Visible="true" SwatchCreatorID="7937"/>']
    for n, (r, g, b) in COLORS.items():
        sw.append('<Color Self="Color/%s" Model="Process" Space="RGB" '
                  'ColorValue="%d %d %d" ColorOverride="Normal" Name="%s" '
                  'ColorEditable="true" ColorRemovable="true" Visible="true" '
                  'SwatchCreatorID="7937"/>' % (x(n), r, g, b, x(n)))
    # Kapaktaki koyultma icin gecis
    sw.append('<Gradient Self="Gradient/shade" Type="Linear" Name="shade">'
              '<GradientStop Self="gs1" StopColor="Color/dark" Location="0" Midpoint="50"/>'
              '<GradientStop Self="gs2" StopColor="Color/$ID/[Paper]" Location="100" Midpoint="50"/>'
              '</Gradient>')
    sw.append('<StrokeStyle Self="StrokeStyle/$ID/Solid" Name="$ID/Solid"/>')
    return (AID % 'graphic' + '<idPkg:Graphic %s %s>%s</idPkg:Graphic>'
            % (NS, DOM, ''.join(sw)))


def pstyle(name, spec):
    fam, sty, size, lead, upper, col, align, track = spec
    return ('<ParagraphStyle Self="ParagraphStyle/%s" Name="%s" '
            'Imported="false" NextStyle="ParagraphStyle/%s" '
            'KeyboardShortcut="0 0" PointSize="%.2f" Leading="%.2f" '
            'Capitalization="%s" FillColor="Color/%s" Tracking="%d" '
            'Justification="%sAlign" AppliedLanguage="$ID/English: USA" '
            'HyphenateCapitalizedWords="false" Hyphenation="false" '
            'SpaceAfter="0" SpaceBefore="0">'
            '<Properties>'
            '<AppliedFont type="string">%s</AppliedFont>'
            '<BasedOn type="object">$ID/[No paragraph style]</BasedOn>'
            '</Properties>'
            '<FontStyle type="string">%s</FontStyle>'
            '</ParagraphStyle>'
            % (x(name), x(name), x(name), size, lead,
               'AllCaps' if upper else 'Normal', x(col), track,
               align, x(fam), x(sty)))


def cstyle(name, spec):
    fam, sty, col = spec
    bits = ''
    if col: bits += 'FillColor="Color/%s" ' % x(col)
    return ('<CharacterStyle Self="CharacterStyle/%s" Name="%s" '
            'Imported="false" KeyboardShortcut="0 0" %s>'
            '<Properties><BasedOn type="object">$ID/[No character style]</BasedOn>'
            '</Properties>'
            '<FontStyle type="string">%s</FontStyle>'
            '</CharacterStyle>' % (x(name), x(name), bits, x(sty)))


def styles_xml():
    ps = ['<RootParagraphStyleGroup Self="psg">',
          '<ParagraphStyle Self="ParagraphStyle/$ID/[No paragraph style]" '
          'Name="$ID/[No paragraph style]" Imported="false"/>']
    for n, s in PSTYLES.items(): ps.append(pstyle(n, s))
    ps.append('</RootParagraphStyleGroup>')
    cs = ['<RootCharacterStyleGroup Self="csg">',
          '<CharacterStyle Self="CharacterStyle/$ID/[No character style]" '
          'Name="$ID/[No character style]" Imported="false"/>']
    for n, s in CSTYLES.items(): cs.append(cstyle(n, s))
    cs.append('</RootCharacterStyleGroup>')
    obj = ('<RootObjectStyleGroup Self="osg">'
           '<ObjectStyle Self="ObjectStyle/$ID/[None]" Name="$ID/[None]"/>'
           '<ObjectStyle Self="ObjectStyle/$ID/[Normal Graphics Frame]" '
           'Name="$ID/[Normal Graphics Frame]"/>'
           '<ObjectStyle Self="ObjectStyle/$ID/[Normal Text Frame]" '
           'Name="$ID/[Normal Text Frame]"/></RootObjectStyleGroup>')
    misc = ('<RootCellStyleGroup Self="celg"/><RootTableStyleGroup Self="tblg"/>'
            '<RootObjectStyleGroup Self="osg2"/>')
    return (AID % 'styles' + '<idPkg:Styles %s %s>%s%s%s</idPkg:Styles>'
            % (NS, DOM, ''.join(ps), ''.join(cs), obj))


def prefs_xml():
    return (AID % 'preferences' + '<idPkg:Preferences %s %s>'
            '<DocumentPreference Self="dprefs" PageHeight="%.4f" PageWidth="%.4f" '
            'PagesPerDocument="1" FacingPages="true" DocumentBleedTopOffset="%.4f" '
            'DocumentBleedBottomOffset="%.4f" DocumentBleedInsideOrLeftOffset="%.4f" '
            'DocumentBleedOutsideOrRightOffset="%.4f" '
            'DocumentBleedUniformSize="true" PageBinding="LeftToRight" '
            'ColumnDirection="Horizontal" PreserveLayoutWhenShuffling="true" '
            'AllowPageShuffle="true" OverprintBlack="true"/>'
            '<ViewPreference Self="vprefs" HorizontalMeasurementUnits="Millimeters" '
            'VerticalMeasurementUnits="Millimeters" RulerOrigin="PageOrigin"/>'
            '<MarginPreference Self="mprefs" Top="%.4f" Bottom="%.4f" '
            'Left="%.4f" Right="%.4f" ColumnCount="12" ColumnGutter="%.4f"/>'
            '<TransparencyDefaultContainerObject Self="tdco"/>'
            '</idPkg:Preferences>'
            % (NS, DOM, PH, PW, BLEED, BLEED, BLEED, BLEED,
               18 * PT, 22 * PT, 20 * PT, 16 * PT, 4 * PT))


def story_xml(sid, cls, frag, dark):
    """Bir yazi cercevesinin metni: paragraf stili + karakter kosulari."""
    st = cls if cls in PSTYLES else (cls.split()[0] if cls.split() else 't')
    if st not in PSTYLES: st = 't'
    if dark and st in ('m', 'm g', 'm rt', 'm rt g', 'm g rt'):
        st = 'm wh' if 'rt' not in st else 'm rt wh'
    paras = [[]]
    for c, t in runs(frag, cls, dark):
        for k, piece in enumerate(t.split('\n')):
            if k: paras.append([])
            if piece: paras[-1].append((c, piece))
    body = []
    for pr in paras:
        if not pr: continue
        cr = []
        for c, t in pr:
            cs = ('CharacterStyle/%s' % x(c)) if c else \
                 'CharacterStyle/$ID/[No character style]'
            cr.append('<CharacterStyleRange AppliedCharacterStyle="%s">'
                      '<Content>%s</Content></CharacterStyleRange>' % (cs, x(t)))
        body.append('<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/%s">'
                    '%s%%s</ParagraphStyleRange>' % (x(st), ''.join(cr)))
    # Paragraf sonu paragraflarin ARASINA girer; sonuncunun ardina konursa
    # hikayenin sonunda bos bir paragraf kalir ve cerceve bir satir buyur.
    body = [b % ('<Br/>' if k < len(body) - 1 else '')
            for k, b in enumerate(body)]
    if not body:
        body.append('<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/%s">'
                    '<CharacterStyleRange AppliedCharacterStyle='
                    '"CharacterStyle/$ID/[No character style]"><Content></Content>'
                    '</CharacterStyleRange></ParagraphStyleRange>' % x(st))
    return (AID % 'story' + '<idPkg:Story %s %s>'
            '<Story Self="%s" AppliedTOCStyle="n" TrackChanges="false" '
            'StoryTitle="$ID/" AppliedNamedGrid="n">'
            '<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" '
            'FrameType="TextFrameType" StoryOrientation="Horizontal" '
            'StoryDirection="LeftToRightDirection"/>%s</Story></idPkg:Story>'
            % (NS, DOM, x(sid), ''.join(body)), st)


def est_height(cls, frag, w_mm):
    """Cerceve icin ilk yukseklik. InDesign kendi kendine sigdirir; bu
    yalnizca acilista makul bir kutu olsun diyedir."""
    st = cls if cls in PSTYLES else (cls.split()[0] if cls.split() else 't')
    size, lead = (PSTYLES.get(st) or PSTYLES['t'])[2:4]
    txt = plain(frag)
    cpl = max(6, int((w_mm * PT) / (size * 0.48)))
    lines = 0
    for para in re.split(r'</p>|<br\s*/?>', frag):
        t = plain(para).strip()
        if not t: continue
        lines += max(1, math.ceil(len(t) / float(cpl)))
    return max(lead, (lines or 1) * lead) * 1.06


def spread_xml(sid, pageinfo, items):
    pg = []
    for pself, name, left, master in pageinfo:
        gb = ('0 %.4f %.4f %.4f' % (-PW, PH, 0.0)) if left else \
             ('0 0 %.4f %.4f' % (PH, PW))
        pg.append('<Page Self="%s" Name="%s" AppliedMaster="%s" '
                  'GeometricBounds="%s" ItemTransform="1 0 0 1 0 0" '
                  'OverrideList="" AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName" '
                  'TabOrder="" GridStartingPoint="TopOutside" UseMasterGrid="true">'
                  '<MarginPreference ColumnCount="12" ColumnGutter="%.4f" Top="%.4f" '
                  'Bottom="%.4f" Left="%.4f" Right="%.4f"/>'
                  '</Page>' % (x(pself), x(name), x(master), gb, 4 * PT,
                               18 * PT, 22 * PT, 20 * PT, 16 * PT))
    return (AID % 'spread' + '<idPkg:Spread %s %s>'
            '<Spread Self="%s" PageCount="%d" BindingLocation="%d" '
            'ShowMasterItems="true" PageTransitionType="None" '
            'PageTransitionDirection="NotApplicable" PageTransitionDuration="Medium" '
            'AllowPageShuffle="true" ItemTransform="1 0 0 1 0 0">'
            '<FlattenerPreference LineArtAndTextResolution="300" '
            'GradientAndMeshResolution="150" ClipComplexRegions="false" '
            'ConvertAllStrokesToOutlines="false" ConvertAllTextToOutlines="false"/>'
            '%s%s</Spread></idPkg:Spread>'
            % (NS, DOM, x(sid), len(pageinfo),
               1 if len(pageinfo) > 1 else 0, ''.join(pg), ''.join(items)))


def rect(x1, y1, x2, y2, fill=None, stroke=None, sw=0.0, gradient=False):
    f = ('FillColor="Color/%s" ' % x(fill)) if fill else 'FillColor="Swatch/$ID/[None]" '
    if gradient: f = 'FillColor="Gradient/shade" '
    s = ('StrokeColor="Color/%s" StrokeWeight="%.3f" ' % (x(stroke), sw)) if stroke \
        else 'StrokeColor="Swatch/$ID/[None]" StrokeWeight="0" '
    return ('<Rectangle Self="%s" ContentType="Unassigned" %s%s'
            'ItemTransform="1 0 0 1 0 0" '
            'AppliedObjectStyle="ObjectStyle/$ID/[Normal Graphics Frame]" '
            'OverprintFill="false" StrokeAlignment="CenterAlignment">%s</Rectangle>'
            % (uid('r'), f, s, geom(x1, y1, x2, y2)))


# ── kitabi kur ──────────────────────────────────────────────────────
m = json.load(open(SRC, encoding='utf-8'))
pages = m['pages'] if isinstance(m, dict) and 'pages' in m else m

if os.path.isdir(OUTDIR): shutil.rmtree(OUTDIR)
LINKS = os.path.join(OUTDIR, 'Links')
DFONTS = os.path.join(OUTDIR, 'Document fonts')
os.makedirs(LINKS); os.makedirs(DFONTS)

for (fam, sty), fn in FONTFILE.items():
    sp = os.path.join(HERE, 'fonts', fn)
    if os.path.isfile(sp): shutil.copyfile(sp, os.path.join(DFONTS, fn))

MASTER = 'uMaster'
spreads, stories = [], []
copied, missing, lowres = {}, set(), []

# Kapak tek yaprak, sonrasi ikili: kitabin gercek serim duzeni.
groups = [[0]] + [[i, i + 1] if i + 1 < len(pages) else [i]
                  for i in range(1, len(pages), 2)]

for gi, g in enumerate(groups):
    items, pageinfo = [], []
    for slot, pi in enumerate(g):
        p = pages[pi]
        # Tek sayfalik ilk yaprak sagdadir; sonraki yapraklarda ilki solda.
        left = (len(g) == 2 and slot == 0)
        ox = -PW if left else 0.0
        pageinfo.append((uid('pg'), str(pi + 1), left, MASTER))
        dark = 'dark' in (p.get('cls') or '')
        if dark:
            items.append(rect(ox, 0, ox + PW, PH, fill='dark'))
        for e in p['els']:
            t = e.get('t')
            if t == 'shade':
                # Bolum acilisinda yazinin altina giren koyultma: sayfanin
                # alt 130 mm'si, siyahtan seffafa.
                items.append(rect(ox, PH - 130 * PT, ox + PW, PH, gradient=True))
                continue
            X = ox + e.get('x', 0) * PT
            Y = e.get('y', 0) * PT
            if t == 'img':
                base = os.path.basename(e['src'])
                sp = picture(base)
                if not sp:
                    missing.add(base); continue
                if base not in copied:
                    shutil.copyfile(sp, os.path.join(LINKS, base))
                    if base.lower().endswith('.svg'):
                        # Cizim dosyasinin pikseli yoktur; olculeri viewBox
                        # verir, oradan en-boy orani cikar.
                        vb = re.search(r'viewBox="([-\d.]+) +([-\d.]+) +'
                                       r'([\d.]+) +([\d.]+)"',
                                       open(sp, encoding='utf-8').read()[:2000])
                        copied[base] = ((float(vb.group(3)), float(vb.group(4)))
                                        if vb else (100.0, 100.0))
                    else:
                        copied[base] = Image.open(sp).size
                pxw, pxh = copied[base]
                svg = base.lower().endswith('.svg')
                W = e['w'] * PT
                # Yuksekligi verilmemis oge, kaynagin oranini alir.
                H = (e['h'] * PT) if e.get('h') else W * pxh / float(pxw)
                ppi = 0 if svg else pxw / (e['w'] / 25.4)
                if ppi and ppi < 240: lowres.append((pi + 1, base, round(ppi)))
                cut = 'cut' in (e.get('cls') or '')
                if cut:
                    s = max(W / pxw, H / pxh)
                    pos = (e.get('pos') or '50% 45%').replace('%', '').split()
                    fx = float(pos[0]) / 100.0 if pos else .5
                    fy = float(pos[1]) / 100.0 if len(pos) > 1 else .45
                    tx = X + (W - pxw * s) * fx
                    ty = Y + (H - pxh * s) * fy
                    sx = sy = s
                else:
                    sx, sy = W / pxw, H / pxh
                    tx, ty = X, Y
                img = ('<Image Self="%s" ItemTransform="%.6f 0 0 %.6f %.4f %.4f" '
                       'ImageTypeName="%s" ActualPpi="72 72" '
                       'EffectivePpi="%d %d" ImageRenderingIntent="UseColorSettings">'
                       '<Properties><Profile type="string">$ID/Embedded</Profile>'
                       '<GraphicBounds Left="0" Top="0" Right="%d" Bottom="%d"/>'
                       '</Properties>'
                       '<Link Self="%s" LinkResourceURI="file:Links/%s" '
                       'LinkResourceFormat="%s" StoredState="Normal" '
                       'LinkClassID="35906" LinkClientID="257" '
                       'LinkResourceModified="false" LinkObjectModified="false" '
                       'ImportPolicy="NoAutoImport" ExportPolicy="NoAutoExport" '
                       'ShowInMenu="false"/></Image>'
                       % (uid('im'), sx, sy, tx, ty,
                          '$ID/SVG' if svg else '$ID/JPEG',
                          round(ppi) or 72, round(ppi) or 72,
                          pxw, pxh, uid('lk'), x(base),
                          '$ID/SVG' if svg else '$ID/JPEG'))
                items.append('<Rectangle Self="%s" ContentType="GraphicType" '
                             'FillColor="Swatch/$ID/[None]" '
                             'StrokeColor="Swatch/$ID/[None]" StrokeWeight="0" '
                             'ItemTransform="1 0 0 1 0 0" '
                             'AppliedObjectStyle="ObjectStyle/$ID/[Normal Graphics Frame]">'
                             '%s%s</Rectangle>'
                             % (uid('r'), geom(X, Y, X + W, Y + H), img))
            elif t == 'txt':
                sid = uid('st')
                xml, st = story_xml(sid, e.get('cls') or 't', e.get('html') or '', dark)
                stories.append((sid, xml))
                W = e['w'] * PT
                H = est_height(e.get('cls') or 't', e.get('html') or '', e['w'])
                items.append('<TextFrame Self="%s" ParentStory="%s" '
                             'ContentType="TextType" FillColor="Swatch/$ID/[None]" '
                             'StrokeColor="Swatch/$ID/[None]" StrokeWeight="0" '
                             'ItemTransform="1 0 0 1 0 0" '
                             'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]">'
                             '%s<TextFramePreference AutoSizingType="HeightOnly" '
                             'AutoSizingReferencePoint="TopLeftPoint" '
                             'UseNoLineBreaksForAutoSizing="false" '
                             'VerticalJustification="TopAlign" '
                             'TextColumnCount="1" TextColumnGutter="0">'
                             '<Properties><InsetSpacing type="list">'
                             '<ListItem type="unit">0</ListItem>'
                             '<ListItem type="unit">0</ListItem>'
                             '<ListItem type="unit">0</ListItem>'
                             '<ListItem type="unit">0</ListItem>'
                             '</InsetSpacing></Properties></TextFramePreference>'
                             '</TextFrame>'
                             % (uid('tf'), x(sid), geom(X, Y, X + W, Y + H)))
            elif t == 'rule':
                c = e.get('cls') or 'r'
                if e.get('h'):                       # dikme
                    items.append(rect(X, Y, X + .35, Y + e['h'] * PT,
                                      fill='ink' if ' t' in c else 'hair'))
                else:
                    th = .9 if ' t' in c else .35
                    items.append(rect(X, Y, X + e['w'] * PT, Y + th,
                                      fill='ink' if ' t' in c else 'hair'))
            elif t == 'frame':
                items.append(rect(X, Y, X + e['w'] * PT, Y + e['h'] * PT,
                                  stroke='ink', sw=.35))
    spreads.append((uid('sp'), pageinfo, items))


# ── paketi yaz ──────────────────────────────────────────────────────
IDML = os.path.join(OUTDIR, 'Yigit-Ozen-Paintings.idml')
parts = []

master = (AID % 'masterspread' + '<idPkg:MasterSpread %s %s>'
          '<MasterSpread Self="%s" Name="A-Master" NamePrefix="A" BaseName="Master" '
          'ShowMasterItems="true" PageCount="2" ItemTransform="1 0 0 1 0 0">'
          '<Page Self="mpL" Name="A" AppliedMaster="n" GeometricBounds="0 %.4f %.4f 0" '
          'ItemTransform="1 0 0 1 0 0" OverrideList="" TabOrder="" '
          'GridStartingPoint="TopOutside" UseMasterGrid="true">'
          '<MarginPreference ColumnCount="12" ColumnGutter="%.4f" Top="%.4f" '
          'Bottom="%.4f" Left="%.4f" Right="%.4f"/></Page>'
          '<Page Self="mpR" Name="A" AppliedMaster="n" GeometricBounds="0 0 %.4f %.4f" '
          'ItemTransform="1 0 0 1 0 0" OverrideList="" TabOrder="" '
          'GridStartingPoint="TopOutside" UseMasterGrid="true">'
          '<MarginPreference ColumnCount="12" ColumnGutter="%.4f" Top="%.4f" '
          'Bottom="%.4f" Left="%.4f" Right="%.4f"/></Page>'
          '</MasterSpread></idPkg:MasterSpread>'
          % (NS, DOM, MASTER, -PW, PH, 4 * PT, 18 * PT, 22 * PT, 20 * PT, 16 * PT,
             PH, PW, 4 * PT, 18 * PT, 22 * PT, 16 * PT, 20 * PT))

backing = (AID % 'backingStory' + '<idPkg:BackingStory %s %s>'
           '<XmlStory Self="bs" AppliedTOCStyle="n" TrackChanges="false" '
           'StoryTitle="$ID/" AppliedNamedGrid="n">'
           '<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" '
           'FrameType="TextFrameType" StoryOrientation="Horizontal" '
           'StoryDirection="LeftToRightDirection"/>'
           '<InCopyExportOption IncludeGraphicProxies="true" IncludeAllResources="false"/>'
           '</XmlStory></idPkg:BackingStory>' % (NS, DOM))

tags = (AID % 'tags' + '<idPkg:Tags %s %s>'
        '<XMLTag Self="XMLTag/Root" Name="Root">'
        '<Properties><TagColor type="enumeration">LightBlue</TagColor></Properties>'
        '</XMLTag></idPkg:Tags>' % (NS, DOM))

dm = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
      '<?aid style="50" type="document" readerVersion="6.0" featureSet="257" '
      'product="18.0(100)"?>\n'
      '<Document %s DOMVersion="18.0" Self="YigitOzenPaintings" '
      'StoryList="%s" Name="Yigit-Ozen-Paintings.idml">'
      % (NS, ' '.join(s for s, _ in stories))]
for r in ('Resources/Graphic.xml', 'Resources/Fonts.xml', 'Resources/Styles.xml',
          'Resources/Preferences.xml'):
    dm.append('<idPkg:%s src="%s"/>' % (r.split('/')[1][:-4], r))
dm.append('<idPkg:MasterSpread src="MasterSpreads/MasterSpread_%s.xml"/>' % MASTER)
for sid, _, _ in spreads:
    dm.append('<idPkg:Spread src="Spreads/Spread_%s.xml"/>' % sid)
for sid, _ in stories:
    dm.append('<idPkg:Story src="Stories/Story_%s.xml"/>' % sid)
dm.append('<idPkg:BackingStory src="XML/BackingStory.xml"/>')
dm.append('<idPkg:Tags src="XML/Tags.xml"/>')
dm.append('</Document>')

parts.append(('designmap.xml', ''.join(dm)))
parts.append(('META-INF/container.xml',
              '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
              '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" '
              'version="1.0"><rootfiles><rootfile full-path="designmap.xml" '
              'media-type="text/xml"/></rootfiles></container>'))
parts.append(('META-INF/metadata.xml',
              '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
              '<Properties xmlns="http://ns.adobe.com/adobeinDesign/idml/1.0/packaging">'
              '<Metadata/></Properties>'))
parts.append(('Resources/Graphic.xml', graphic_xml()))
parts.append(('Resources/Fonts.xml', fonts_xml()))
parts.append(('Resources/Styles.xml', styles_xml()))
parts.append(('Resources/Preferences.xml', prefs_xml()))
parts.append(('MasterSpreads/MasterSpread_%s.xml' % MASTER, master))
for sid, pinfo, items in spreads:
    parts.append(('Spreads/Spread_%s.xml' % sid, spread_xml(sid, pinfo, items)))
for sid, xml in stories:
    parts.append(('Stories/Story_%s.xml' % sid, xml))
parts.append(('XML/BackingStory.xml', backing))
parts.append(('XML/Tags.xml', tags))

with zipfile.ZipFile(IDML, 'w', zipfile.ZIP_DEFLATED) as z:
    # mimetype ilk giristir ve sikistirilmaz; InDesign paketi boyle tanir.
    zi = zipfile.ZipInfo('mimetype')
    zi.compress_type = zipfile.ZIP_STORED
    z.writestr(zi, 'application/vnd.adobe.indesign-idml-package')
    for name, data in parts:
        z.writestr(name, data.encode('utf-8'))

mb = lambda p: sum(os.path.getsize(os.path.join(p, f)) for f in os.listdir(p)) / 1048576.0
print('%s' % os.path.basename(IDML))
print('  %d yaprak · %d sayfa · %d yazi cercevesi · %d bagli gorsel'
      % (len(spreads), len(pages), len(stories), len(copied)))
print('  paragraf stili %d · karakter stili %d · renk %d'
      % (len(PSTYLES), len(CSTYLES), len(COLORS)))
print('  IDML %.1f MB · Links %.0f MB · Document fonts %d dosya'
      % (os.path.getsize(IDML) / 1048576.0, mb(LINKS), len(os.listdir(DFONTS))))
if lowres:
    print('  240 ppi altinda %d yerlestirme' % len(lowres))
if missing:
    print('  ! bulunamayan gorsel: %s' % ', '.join(sorted(missing)[:4]))
print('  klasor: %s' % OUTDIR)
