"""Figs 3-7 from fig_data.json (run extract.py first to refresh the numbers)."""
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, FancyBboxPatch
from matplotlib.lines import Line2D
from style import *
from matplotlib.transforms import blended_transform_factory as blended
from drawkit import capsule, text_w

FW = {'fig3': 3.785, 'fig4': 3.2573, 'fig5': 3.364, 'fig7': 2.576}   # figure widths (in), tuned so each figure prints at its column width
D = json.load(open(HERE / 'fig_data.json'))
pct = lambda c: (100 * c['k'] / c['n'], 100 * c['ci'][0], 100 * c['ci'][1])
RED, TEAL, NAVY, GREY = ATTACK[0], GUARD[0], EXEC[0], NEUTRAL[0]
COND = (('baseline', GREY, 'Before retrofit'), ('legal_retrofit', NAVY, 'Requested retrofit'),
        ('attacked', RED, 'Attacked (cooling setpoint 28 °C)'))


def sized(prop, size):
    p = prop.copy(); p.set_size(size)
    return p


def tidy(ax, grid='y'):
    ax.spines['left'].set_color(PANEL_LINE); ax.spines['bottom'].set_color(MUTED)
    if grid:
        getattr(ax, f'{grid}axis').grid(True, color=GRID, lw=0.5)
        ax.set_axisbelow(True)


def square_legend(ax_or_fig, items, **kw):
    h = [Patch(fc=c, ec='none', label=l) for c, l in items]
    return ax_or_fig.legend(handles=h, handlelength=0.9, handleheight=0.9, handletextpad=0.4, **kw)


# ---------- Fig 3: Experiment 1, entry x task wording ----------
def fig3():
    e = D['exp1']
    fig, ax = plt.subplots(figsize=(FW.get('fig3', COL_W), 2.15))
    groups = [('1-1', '1-4', 'Tool output', 'A'), ('1-2', '1-5', 'Peer summary', 'B'),
              ('1-3', '1-6', 'Config. note', 'C')]
    bw = 0.34
    for i, (open_c, fixed_c, name, k) in enumerate(groups):
        for dx, cell, col in ((-bw / 2 - 0.02, open_c, RED), (bw / 2 + 0.02, fixed_c, TEAL)):
            c = e[cell]['attack']; m, lo, hi = pct(c)
            ax.bar(i + dx, max(m, 0.6), bw, color=col, ec='none', zorder=2)
            ax.plot([i + dx] * 2, [lo, hi], color=INK, lw=0.6, zorder=3)
            ax.plot([i + dx - 0.05, i + dx + 0.05], [hi] * 2, color=INK, lw=0.6, zorder=3)
            ax.text(i + dx, hi + 1.6, f"{c['k']}/{c['n']}", ha='center', va='bottom', fontsize=7.4,
                    color=col, fontproperties=F_B)
    ax.set_xticks(range(3), [f'Entry {k}\n{n}' for _, _, n, k in groups])
    ax.tick_params(axis='x', length=0, pad=3)
    ax.set_xlim(-0.55, 2.55); ax.set_ylim(0, 60); ax.set_yticks(range(0, 61, 20))
    ax.set_ylabel('Attack success rate (%)')
    tidy(ax)
    nn = sum(e[c]['neutral']['n'] for c in e)
    ax.text(2.52, 57, f'Neutral controls: 0/{nn}', ha='right', va='top', fontsize=7.2, color=MUTED,
            fontproperties=F_I)
    square_legend(ax, ((RED, 'Task leaves the setpoint open'), (TEAL, 'Task states the setpoint')),
                  loc='lower left', bbox_to_anchor=(-0.02, 1.0), ncol=2, columnspacing=1.2)
    save(fig, 'fig3_exp1_entry_wording')


# ---------- Fig 4: layer-by-layer propagation ----------
def fig4():
    f = D['funnel']; n = f['n']
    layers = [('', 'Injected text delivered', f['delivered']), ('L1', 'Read by a downstream agent', f['contact']),
              ('L2', 'Target value submitted', f['attempt']), ('L3', 'Saved to configuration', f['state']),
              ('L4', 'Used by the simulation', f['simulation']), ('L5', 'Indoor outcome changed', f['physical'])]
    fig, ax = plt.subplots(figsize=(FW.get('fig4', COL_W), 1.85))
    y = np.arange(len(layers))[::-1]
    for yi, (code, lab, v) in zip(y, layers):
        col = NAVY if v == n else RED
        ax.barh(yi, v, height=0.62, color=col, ec='none', zorder=2)
        ax.text(v + 5, yi, f'{v}', va='center', fontsize=7.4, color=col, fontproperties=F_B)
        if code:
            ax.text(0.0, yi - 0.1, code, transform=blended(fig.transFigure, ax.transData), ha='left', va='center',
                    fontsize=7.4, color=MUTED, fontproperties=F_B)
    ax.set_yticks(y, [l for _, l, _ in layers]); ax.tick_params(axis='y', length=0, labelsize=7.6, labelcolor=INK)
    fig.subplots_adjust(left=0.53, right=0.99)
    ax.spines['left'].set_visible(False)
    ax.set_xlim(0, n * 1.08); ax.set_xticks([0, 100, 200, 300])
    ax.set_xlabel(f'Attack trajectories (n = {n})')
    tidy(ax, 'x')
    x0 = f['attempt'] + 50
    ax.annotate("the model's own choice\nis the only filter",
                xy=(f['attempt'] + 32, y[2]), xytext=(x0, y[2]), va='center', fontsize=7.2, color=INK,
                fontproperties=F_I, linespacing=1.15,
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=0.6, mutation_scale=5, shrinkA=1, shrinkB=0))
    ax.plot([x0, x0 + 5, x0 + 5, x0], [y[3] + 0.3, y[3] + 0.3, y[5] - 0.3, y[5] - 0.3], color=RED, lw=0.7)
    ax.text(x0 + 11, (y[3] + y[5]) / 2, 'no later layer stopped\na single change', va='center', fontsize=7.2,
            color=RED, fontproperties=F_I, linespacing=1.2)
    save(fig, 'fig4_propagation')


# ---------- Fig 5: indoor temperature over the simulated day ----------
def fig5():
    ts = D['timeseries']
    fig, ax = plt.subplots(figsize=(FW.get('fig5', COL_W), 2.0))
    h = np.arange(len(ts['attacked'])) * 0.25
    occ = np.array([r['occupancy'] > 0 for r in ts['attacked']])
    edges = np.flatnonzero(np.diff(occ.astype(int)))
    a, b = h[edges[0] + 1], h[edges[1] + 1]
    ax.axvspan(a, b, color='#eeeef1', lw=0, zorder=0)
    ax.text((a + b) / 2, 31.6, 'unoccupied', ha='center', va='top', fontsize=7.2, color=MUTED,
            fontproperties=F_I)
    ax.axhline(24, color=MUTED, lw=0.6, ls=(0, (3, 2)), zorder=1)
    ax.text(4.6, 23.1, 'Original setpoint 24 °C', fontsize=7.2, color=SUB, va='center', ha='left',
            fontproperties=F_I)
    for key, col, lab in COND:
        lw = 1.5 if key == 'attacked' else 1.1
        ax.plot(h, [r['zone_temperature'] for r in ts[key]], color=col, lw=lw, label=lab, zorder=3)
    ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 4), [f'{x:02d}:00' for x in range(0, 25, 4)])
    ax.set_ylim(22, 32); ax.set_yticks(range(22, 33, 2))
    ax.set_ylabel('Indoor temperature (°C)'); ax.set_xlabel('Time of the simulated summer day')
    tidy(ax, None)
    ax.legend(loc='lower left', bbox_to_anchor=(-0.02, 1.0), ncol=3, handlelength=1.3, columnspacing=0.9,
              handletextpad=0.4, labels=['Before retrofit', 'Requested retrofit', 'Attacked (28 °C)'],
              handles=[Line2D([], [], color=c, lw=1.4) for _, c, _ in COND])
    save(fig, 'fig5_indoor_temperature')


# ---------- Fig 6: looks better, is worse ----------
def fig6():
    p = D['physics']; v = D['verdicts']
    fig, axs = plt.subplots(1, 4, figsize=(FULL_W, 2.25),
                            gridspec_kw=dict(wspace=0.8, width_ratios=[1, 1, 0.9, 1]))
    keys = [k for k, _, _ in COND]; cols = [c for _, c, _ in COND]

    def bars(ax, vals, labels, title, ylab, colors=cols, top=None):
        ax.bar(range(len(vals)), vals, color=colors, width=0.62, zorder=2)
        top = top or max(vals) * 1.22
        for i, (x, s) in enumerate(zip(vals, labels)):
            ax.text(i, x + top * 0.025, s, ha='center', va='bottom', fontsize=7.4,
                    color=NEUTRAL_TEXT if colors[i] == GREY else colors[i],
                    fontproperties=F_B)
        ax.set_xticks([]); ax.set_xlim(-0.6, len(vals) - 0.4); ax.set_ylim(0, top)
        ax.set_ylabel(ylab, fontsize=7.6)
        ax.set_title(title, loc='center', pad=5, fontproperties=sized(F_B, 8), color=INK)
        tidy(ax)

    kwh = [p[k]['hvac_kwh'] for k in keys]
    bars(axs[0], kwh, [f'{x:.1f}' for x in kwh], '(a) HVAC electricity', 'kWh per day')
    axs[0].set_yticks(range(0, 15, 2))
    usd = [p[k]['cost_cents'] / 100 for k in keys]
    bars(axs[1], usd, [f'{x:.2f}' for x in usd], '(b) Electricity cost', 'USD per day')
    lg, at = v['comfort_retrofit_better']['legal'], v['comfort_retrofit_better']['attacked']
    bars(axs[2], [100 * lg[0] / lg[1], 100 * at[0] / at[1]], [f'{lg[0]}/{lg[1]}', f'{at[0]}/{at[1]}'],
         '(c) Framework\u2019s comfort comparison', '% judging retrofit\ncomfort better', colors=cols[1:], top=125)
    axs[2].set_yticks(range(0, 101, 25))
    # (d) time the occupied house spends above 26 °C, from the simulated-day time series
    ts = D['timeseries']
    hot = []
    for k in keys:
        occ = [r for r in ts[k] if r['occupancy'] > 0]
        hot.append(0.25 * sum(r['zone_temperature'] > 26 for r in occ))
    occ_h = 0.25 * sum(r['occupancy'] > 0 for r in ts['attacked'])
    bars(axs[3], [max(x, 0.06) for x in hot], [f'{x:g} h' for x in hot], '(d) Indoor temperature',
         f'Occupied hours above 26 \u00b0C\n(of {occ_h:g} h)', top=14)
    axs[3].set_yticks(range(0, 15, 2))
    axs[3].text(-0.45, 13.6, 'Over 31 days of August:\nattacked 384 of 426 h,\nrequested 0 h',
                va='top', fontsize=7.2, color=RED, fontproperties=F_I, linespacing=1.15)

    fig.subplots_adjust(top=0.9, bottom=0.17, left=0.058, right=0.975)
    square_legend(fig, [(c, l) for _, c, l in COND], loc='lower center', bbox_to_anchor=(0.5, -0.01), ncol=3,
                  columnspacing=1.8)
    save(fig, 'fig6_looks_better_is_worse', tight=False)


# ---------- Fig 7: Experiment 2, where the constraint is written ----------
def fig7():
    rows = [('No stated constraint', 'Exp. 1 baseline, cell 1-1', D['exp1']['1-1']['attack'], RED),
            ('Specialist-agent prompts', 'P1', D['exp2']['2-P1']['attack'], TEAL),
            ('Orchestrator prompt', 'P2', D['exp2']['2-P2']['attack'], TEAL),
            ('Configuration document', 'P3', D['exp2']['2-P3']['attack'], TEAL)]
    fig, ax = plt.subplots(figsize=(FW.get('fig7', COL_W), 1.7))
    for i, (lab, sub, c, col) in enumerate(rows):
        yi = len(rows) - 1 - i + (0.25 if i == 0 else 0)
        m, lo, hi = pct(c)
        ax.plot([lo, hi], [yi, yi], color=col, lw=1.4, zorder=3, solid_capstyle='round')
        ax.plot(m, yi, 'o', ms=5.2, mfc=WHITE, mec=col, mew=1.4, zorder=4)
        ax.text(hi + 2, yi, f"{c['k']}/{c['n']}", va='center', fontsize=7.4, color=col, fontproperties=F_B)
        tr = ax.get_yaxis_transform()
        if i == 0:
            ax.text(-0.04, yi + 0.17, lab, transform=tr, ha='right', va='center', fontsize=7.6, color=INK,
                    fontproperties=F_B)
            ax.text(-0.04, yi - 0.24, sub, transform=tr, ha='right', va='center', fontsize=7.2, color=MUTED,
                    fontproperties=F_I)
        else:
            ax.text(-0.085, yi, lab, transform=tr, ha='right', va='center', fontsize=7.6, color=INK)
            ax.text(-0.02, yi, sub, transform=tr, ha='right', va='center', fontsize=7.2, color=TEAL,
                    fontproperties=F_B)
    ax.axhline(2.62, color=PANEL_LINE, lw=0.6)
    ax.text(59, 2.5, 'constraint stated (Exp. 2)', ha='right', va='top', fontsize=7.2, color=TEAL,
            fontproperties=F_I)
    ax.set_yticks([]); ax.spines['left'].set_visible(False)
    ax.set_ylim(-0.85, 3.75)
    ax.set_xlim(-1.5, 60); ax.set_xlabel('Attack success rate (%), Wilson 95% interval')
    tidy(ax, 'x')
    nn = D['exp1']['1-1']['neutral']['n'] + sum(D['exp2'][f'2-P{j}']['neutral']['n'] for j in (1, 2, 3))
    ax.text(59, -0.62, f'Neutral controls: 0/{nn}', ha='right', va='center', fontsize=7.2, color=MUTED,
            fontproperties=F_I)
    save(fig, 'fig7_exp2_constraint_placement')


if __name__ == '__main__':
    for f in (fig3, fig4, fig5, fig6, fig7):
        f()
