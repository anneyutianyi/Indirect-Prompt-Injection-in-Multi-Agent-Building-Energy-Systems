"""Rewrite each manifest's output folders to research/<experiment>/runs_new/<batch>/<run_id> in this checkout."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for m in sorted(ROOT.glob('research/exp_*/manifest_*.json')):
    specs = json.loads(m.read_text())
    for s in specs:
        old = Path(s['outdir'])
        s['outdir'] = str(m.parent / 'runs_new' / old.parent.name / old.name)
    m.with_name(m.stem + '_local.json').write_text(json.dumps(specs, indent=1))
    print(m.relative_to(ROOT), '->', m.stem + '_local.json')
