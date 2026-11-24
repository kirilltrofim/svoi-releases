"""Собирает картинки README: шапку (светлую и тёмную), кнопку и значки разделов.

Текст переводится в контуры (шрифт Inter), чтобы GitHub показывал его одинаково
на любом устройстве. Запуск из корня этого репозитория:

    pip install fonttools uharfbuzz pillow
    python .github/assets/build.py --fonts <svoi>/app/assets/fonts --brand <svoi>/design
"""
import argparse, base64, io
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from PIL import Image

OUT = Path(__file__).parent

THEMES = {
    'light': dict(bg='#edf3fd', ink='#0f1b33', sub='#4b5a78'),
    'dark':  dict(bg='#111d33', ink='#f2f6ff', sub='#9db0d0'),
}
BLUE = '#2670e9'


class Face:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.upm = self.tt['head'].unitsPerEm
        blob = hb.Blob.from_file_path(str(path))
        self.hb = hb.Font(hb.Face(blob))

    def path(self, text, size, x, y):
        """Контур строки с кернингом; возвращает (d, ширина)."""
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hb, buf, {'kern': True, 'liga': True})
        order = self.tt.getGlyphOrder()
        s = size / self.upm
        pen = SVGPathPen(self.glyphs)
        cx = 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            tp = TransformPen(pen, (s, 0, 0, -s, x + (cx + pos.x_offset) * s, y))
            self.glyphs[order[info.codepoint]].draw(tp)
            cx += pos.x_advance
        return pen.getCommands(), cx * s


def png_data(path, width):
    im = Image.open(path).convert('RGBA')
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, 'WEBP', quality=90, method=6)  # WebP: шапка в разы легче PNG
    return base64.b64encode(buf.getvalue()).decode(), im.width, im.height


# 3D-предметы на «полке» справа: (файл, x, y, ширина, поворот) в координатах 1280×440
SHELF = (
    ('qa-shopping', 790, 72, 246, -6),
    ('qa-event', 1000, 14, 220, 8),
    ('qa-task', 905, 262, 168, 0),
    ('reward-star', 1090, 218, 180, 12),
)


def hero(theme, bold, medium, logo, art):
    t = THEMES[theme]
    W, H, P = 1280, 440, 76
    b64, lw0, lh0 = logo
    lw = 420
    lh = round(lh0 * lw / lw0)
    line1, _ = bold.path('Семейный планировщик', 48, P, 268)
    line2, _ = bold.path('для Android', 48, P, 324)
    sub, _ = medium.path('Расписание, задачи, покупки и звёзды за заботу', 25, P, 378)
    shadow = '0.22' if theme == 'light' else '0.45'
    items = []
    for name, x, y, w, rot in SHELF:
        data, iw, ih = art[name]
        h = round(ih * w / iw)
        cx, cy = x + w / 2, y + h / 2
        items.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" transform="rotate({rot} {cx} {cy})" '
                     f'filter="url(#s)" xlink:href="data:image/webp;base64,{data}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="SVOI — семейный планировщик для Android">
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="28"/></clipPath>
<filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#14327a" flood-opacity="{shadow}"/></filter></defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{t['bg']}"/>
{''.join(items)}
<image x="{P - 12}" y="44" width="{lw}" height="{lh}" xlink:href="data:image/webp;base64,{b64}"/>
<path d="{line1}" fill="{t['ink']}"/>
<path d="{line2}" fill="{t['ink']}"/>
<path d="{sub}" fill="{t['sub']}"/>
</g>
</svg>
'''


def button(bold, label='Скачать APK'):
    H, PX, ICON = 64, 30, 26
    _, tw = bold.path(label, 24, 0, 0)
    W = PX + ICON + 14 + round(tw) + PX + 4
    d, _ = bold.path(label, 24, PX + ICON + 14, 41)
    ix, iy = PX, (H - ICON) / 2
    icon = (f'<g fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" '
            f'transform="translate({ix} {iy})"><path d="M13 3v14M7 11l6 6 6-6M4 22h18"/></g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
<rect width="{W}" height="{H}" rx="{H/2}" fill="{BLUE}"/>
{icon}
<path d="{d}" fill="#fff"/>
</svg>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', type=Path, required=True)
    ap.add_argument('--brand', type=Path, required=True, help='<svoi>/design')
    a = ap.parse_args()
    bold = Face(a.fonts / 'Inter-Bold.ttf')
    medium = Face(a.fonts / 'Inter-Medium.ttf')
    logo = png_data(a.brand / 'brand' / 'landing-logo.png', 840)
    ill = a.brand / 'illustrations'
    src = {
        'qa-shopping': ill / 'app/home/qa-shopping.png',
        'qa-event': ill / 'app/home/qa-event.png',
        'qa-task': ill / 'app/home/qa-task.png',
        'reward-star': ill / 'rewards/reward-star.png',
    }
    art = {k: png_data(p, 360) for k, p in src.items()}
    for theme in THEMES:
        (OUT / f'hero-{theme}.svg').write_text(hero(theme, bold, medium, logo, art), encoding='utf-8')
    # Значки разделов для таблицы под кнопкой (показываются 72×72)
    for k, p in src.items():
        im = Image.open(p).convert('RGBA'); im.thumbnail((144, 144), Image.LANCZOS)
        im.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(OUT / f'{k}.png', optimize=True)
    (OUT / 'download.svg').write_text(button(bold), encoding='utf-8')


if __name__ == '__main__':
    main()
