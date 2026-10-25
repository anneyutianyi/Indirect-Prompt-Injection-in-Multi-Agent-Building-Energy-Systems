"""Building blocks for the schematic figures, in the style of the survey figures.

Every schematic is drawn on a canvas whose units are printed points (y up), so a 7 pt label is 7 pt
in the paper.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
from matplotlib.textpath import TextPath
from style import *

ICONS = {
    'alert': '', 'shield': '', 'robot': '', 'user': '', 'sitemap': '',
    'database': '', 'settings': '', 'tool': '', 'file': '', 'home': '',
    'thermo': '\ueb38', 'server': '', 'shuffle': '', 'box': '', 'terminal': '',
    'report': '', 'clipboard': '', 'chart': '', 'message': '', 'filecog': '',
    'eye': '', 'plug': '', 'lock': '', 'bolt': '', 'stack': '',
    'folder': '', 'bars': '', 'doc': '', 'aircon': '', 'homebolt': '', 'listcheck': '',
}


def canvas(w, h):
    fig = plt.figure(figsize=(w / 72, h / 72))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis('off')
    return fig, ax


def text_w(s, size, prop=F_R):
    """Width of a single-line string in points."""
    if not s:
        return 0
    return TextPath((0, 0), s, size=size, prop=prop).get_extents().width


def rbox(ax, x, y, w, h, fc, ec='none', lw=0.6, r=4, ls='-', z=1, **kw):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}', fc=fc, ec=ec, lw=lw,
                       ls=ls, zorder=z, **kw)
    ax.add_patch(p)
    return p


def panel(ax, x, y, w, h, title=None, r=6, size=7.4):
    """Light grey group panel with a dark capsule title in its top-left corner."""
    rbox(ax, x, y, w, h, PANEL_BG, PANEL_LINE, lw=0.6, r=r, z=0)
    if title:
        capsule(ax, x + 6, y + h - 6, title, size=size, anchor='tl')


def capsule(ax, x, y, s, size=7.4, fc=DARK, tc=WHITE, anchor='tl', padx=6, h=None, prop=F_B, z=5):
    """Pill-shaped label. anchor: 'tl' top-left, 'c' centre, 'l' left-middle, 'r' right-middle."""
    h = h or size * 1.75
    w = text_w(s, size, prop) + 2 * padx
    if anchor == 'tl':
        x0, y0 = x, y - h
    elif anchor == 'c':
        x0, y0 = x - w / 2, y - h / 2
    elif anchor == 'l':
        x0, y0 = x, y - h / 2
    else:
        x0, y0 = x - w, y - h / 2
    rbox(ax, x0, y0, w, h, fc, r=h / 2, z=z)
    ax.text(x0 + w / 2, y0 + h / 2 - size * 0.04, s, ha='center', va='center', fontsize=size, color=tc,
            fontproperties=prop, zorder=z + 1)
    return x0, y0, w, h


def tag(ax, x, y, s, color, size=6.2, anchor='c', z=8):
    """Small coloured tag (e.g. the R2 / P1 constraint markers)."""
    return capsule(ax, x, y, s, size=size, fc=color, tc=WHITE, anchor=anchor, padx=3.2, h=size * 1.6, z=z)


def icon(ax, x, y, name, size, color, z=6):
    ax.text(x, y, ICONS[name], fontproperties=F_ICON, fontsize=size, color=color, ha='center', va='center',
            zorder=z)


def card(ax, x, y, w, h, title, body='', scheme=EXEC, icon_name=None, head=None, size=7.4, bsize=6.6,
         ls='-', title_color=None, body_style='normal', z=2):
    """Stage card: tinted header with icon and bold coloured title, white body with grey text."""
    line, tint = scheme
    head = head or size * 2.3
    outline = rbox(ax, x, y, w, h, 'none', line, lw=0.75, r=3, ls=ls, z=z + 2)
    for (yy, hh, fc) in ((y + h - head, head, tint), (y, h - head, WHITE)):
        r = Rectangle((x, yy), w, hh, fc=fc, ec='none', zorder=z)
        ax.add_patch(r); r.set_clip_path(outline)
    if body:
        ax.plot([x, x + w], [y + h - head] * 2, color=line, lw=0.5, zorder=z + 1)
    tx = x + 6
    if icon_name:
        icon(ax, x + 6 + size * 0.75, y + h - head / 2, icon_name, size * 1.35, line, z=z + 3)
        tx = x + 9 + size * 1.6
    ax.text(tx, y + h - head / 2, title, fontproperties=F_B, fontsize=size, color=title_color or line,
            va='center', ha='left', zorder=z + 3)
    if body:
        prop = F_I if body_style == 'italic' else F_R
        ax.text(x + 6, y + (h - head) / 2, body, fontproperties=prop, fontsize=bsize, color=SUB, va='center',
                ha='left', linespacing=1.25, zorder=z + 3)
    return dict(x=x, y=y, w=w, h=h, cx=x + w / 2, cy=y + h / 2, top=y + h, right=x + w)


def note_card(ax, x, y, w, h, title, body, scheme, icon_name, size=7.2, bsize=6.4, z=2, ls='-'):
    """Risk/control card: tinted throughout, icon on the left, bold title, italic note underneath."""
    line, tint = scheme
    rbox(ax, x, y, w, h, tint, line, lw=0.75, r=3, ls=ls, z=z)
    icon(ax, x + 6 + size * 0.8, y + h / 2, icon_name, size * 1.55, line, z=z + 1)
    tx = x + 11 + size * 1.6
    ax.text(tx, y + h / 2 + bsize * 0.62, title, fontproperties=F_B, fontsize=size, color=line, va='center',
            zorder=z + 1)
    ax.text(tx, y + h / 2 - size * 0.66, body, fontproperties=F_I, fontsize=bsize, color=SUB, va='center',
            zorder=z + 1)
    return dict(x=x, y=y, w=w, h=h, cx=x + w / 2, cy=y + h / 2, top=y + h, right=x + w)


def arrow(ax, pts, color=INK, lw=0.9, dashed=False, head=4.2, z=3):
    """Polyline arrow through pts with a filled triangular head at the end."""
    xs, ys = zip(*pts)
    ls = (0, (2.6, 1.8)) if dashed else '-'
    if len(pts) > 2:
        ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, ls=ls, zorder=z, solid_capstyle='butt')
    a = FancyArrowPatch(pts[-2], pts[-1], arrowstyle=f'-|>,head_length={head * 0.11},head_width={head * 0.07}',
                        mutation_scale=10, color=color, lw=lw, linestyle=ls, shrinkA=0, shrinkB=0, zorder=z)
    ax.add_patch(a)


def label(ax, x, y, s, size=6.4, color=SUB, prop=F_R, ha='left', va='center', z=7, **kw):
    return ax.text(x, y, s, fontproperties=prop, fontsize=size, color=color, ha=ha, va=va, zorder=z, **kw)
