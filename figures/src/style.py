"""Shared look for every figure.

Matches the figures of Tan's CSUR survey: Linux Biolinum, dark capsule titles, light grey group
panels, cards with outline icons, muted palette. Figures are drawn at their printed size in the
cas-dc template (column 83.7 mm, text width 173.8 mm), so the font sizes here are what readers see.
Fonts are bundled in src/fonts (Linux Biolinum, OFL; Tabler icons, MIT), so no TeX install is needed.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = Path(__file__).resolve().parent
FIGDIR = HERE.parent
FONTS = HERE / 'fonts'

COL_PT = 83.7 / 25.4 * 72      # 237.3 pt
FULL_PT = 173.8 / 25.4 * 72    # 492.7 pt
COL_W, FULL_W = COL_PT / 72, FULL_PT / 72

for f in FONTS.glob('*.ttf'):
    fm.fontManager.addfont(str(f))
FAMILY = 'TypoPRO Linux Biolinum'
F_R = fm.FontProperties(fname=str(FONTS / 'TypoPRO-LinuxBiolinum-Regular.ttf'))
F_B = fm.FontProperties(fname=str(FONTS / 'TypoPRO-LinuxBiolinum-RegularBold.ttf'))
F_I = fm.FontProperties(fname=str(FONTS / 'TypoPRO-LinuxBiolinum-RegularItalic.ttf'))
F_ICON = fm.FontProperties(fname=str(FONTS / 'tabler-icons-outline.ttf'))

# ink and surfaces
INK = '#2b2b2e'
SUB = '#56565c'
MUTED = '#808088'
DARK = '#3f3f46'          # capsule titles
PANEL_BG = '#f7f7f8'
PANEL_LINE = '#d4d4d8'
GRID = '#e6e6ea'
WHITE = '#ffffff'

# semantic colours (line, tint); the same meaning in every figure
ATTACK = ('#e0663a', '#fcf0eb')     # injected text, boundary crossed
GUARD = ('#3f9a7a', '#ecf5f2')      # a stated constraint
AGENT = ('#8a6bb8', '#f3f0f8')      # LLM agents
EXEC = ('#3f7cb5', '#ecf2f8')       # deterministic execution; requested retrofit
NEUTRAL = ('#b3b0aa', '#f7f7f6')    # before retrofit; neutral controls
NEUTRAL_TEXT = '#8f8b84'           # the neutral colour, dark enough for text on white
NAVY_LIGHT = '#a9c4de'

mpl.rcParams.update({
    'font.family': FAMILY, 'font.size': 8,
    'axes.titlesize': 8, 'axes.labelsize': 8, 'xtick.labelsize': 7.4, 'ytick.labelsize': 7.4,
    'legend.fontsize': 7.6, 'text.color': INK, 'axes.labelcolor': INK,
    'axes.edgecolor': MUTED, 'xtick.color': MUTED, 'ytick.color': MUTED,
    'xtick.labelcolor': SUB, 'ytick.labelcolor': SUB,
    'axes.linewidth': 0.5, 'xtick.major.width': 0.5, 'ytick.major.width': 0.5,
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'axes.spines.top': False, 'axes.spines.right': False,
    'legend.frameon': False, 'lines.solid_capstyle': 'round',
    'pdf.fonttype': 42, 'svg.fonttype': 'path',
    'savefig.facecolor': 'white', 'axes.unicode_minus': False,
})


def save(fig, name, tight=True):
    kw = dict(bbox_inches='tight', pad_inches=0.0) if tight else {}
    (FIGDIR / 'png').mkdir(exist_ok=True)
    for ext in ('pdf', 'svg'):
        fig.savefig(FIGDIR / f'{name}.{ext}', **kw)
    fig.savefig(FIGDIR / 'png' / f'{name}.png', dpi=300, **kw)
    plt.close(fig)
