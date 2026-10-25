# Figure sources

Style matches the figures of the CSUR skill survey: Linux Biolinum, dark capsule titles, light grey
group panels, cards with outline icons, muted palette (red = injected text / boundary crossed,
green = a stated constraint, purple = LLM agents, navy = deterministic execution / requested retrofit,
grey = before retrofit).

    python3 extract.py      # re-read the experiment results into fig_data.json
    python3 schematics.py   # Fig 1, Fig 2
    python3 data_figs.py    # Fig 3-7

Needs only matplotlib and numpy. Fonts are bundled in fonts/ (Linux Biolinum, SIL OFL; Tabler
icons, MIT), so no TeX install is required. Output: figs/*.pdf (for the paper), figs/*.svg,
figs/png/*.png (300 dpi previews). Text in the PDFs stays selectable; the SVGs store text as outlines
so they look identical on any machine.

Shared look: style.py (sizes, colours, fonts); drawing blocks for the schematics: drawkit.py.
Figures are drawn at their printed size (column 83.7 mm, text width 173.8 mm), so font sizes are real.
