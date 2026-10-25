"""Collect the numbers behind Figs 3-7 from the experiment runs into fig_data.json."""
import csv, json, glob, math
from pathlib import Path
from collections import Counter
EXP = Path(__file__).resolve().parents[2] / 'research/exp_20261009'
OUT = Path(__file__).resolve().parent / 'fig_data.json'

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z*z/n; c = p + z*z/(2*n); h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return max(0.0, (c-h)/d), min(1.0, (c+h)/d)

def load(f):
    return [r for r in csv.DictReader(open(EXP/f))]

def valid(r):  # same rule as build_results.py: drop service interruptions and undetermined rows
    return r['service_interrupted'] == 'False' and r['violation'] in ('True', 'False')

e1, e2 = load('results_exp1.csv'), load('results_exp2.csv')
e2 = [r for r in e2 if r['cell'] != '2-P0']   # the extra no-policy batch is reported only in the limitations
data = {}

def cells(rows):
    out = {}
    for cell in sorted({r['cell'] for r in rows}):
        d = {}
        for cond in ('attack', 'neutral'):
            g = [r for r in rows if r['cell'] == cell and r['condition'] == cond and valid(r)]
            k = sum(r['violation'] == 'True' for r in g); n = len(g)
            d[cond] = {'k': k, 'n': n, 'ci': wilson(k, n)}
        d['entry'] = rows[[r['cell'] for r in rows].index(cell)]['entry']
        d['task'] = rows[[r['cell'] for r in rows].index(cell)]['task']
        out[cell] = d
    return out
data['exp1'] = cells(e1); data['exp2'] = cells(e2)

# Fig 4: layer-by-layer propagation, all valid attack runs of both experiments
att = [r for r in e1 + e2 if r['condition'] == 'attack' and valid(r)]
summ = {r['run_id']: json.load(open(EXP/'runs'/r['phase']/r['run_id']/'summary.json')) for r in att}
data['funnel'] = {
    'n': len(att),
    'delivered': sum(r['injection_applied'] == 'True' for r in att),
    'contact': sum(r['contact'] == 'True' for r in att),
    'attempt': sum(r['param_attempt'] == 'True' for r in att),
    'state': sum(bool(summ[r['run_id']]['state_compromise']) for r in att),
    'simulation': sum(r['violation'] == 'True' for r in att),
    'physical': sum(bool(summ[r['run_id']]['physical_impact']) for r in att),
}
neu = [r for r in e1 + e2 if r['condition'] == 'neutral' and valid(r)]
data['neutral_total'] = {'k': sum(r['violation'] == 'True' for r in neu), 'n': len(neu)}

# Fig 5/6: physics of the attacked runs vs the same run with the unauthorised change undone
viol = [r for r in att if r['violation'] == 'True']
phys = Counter(); cfs = Counter()
for r in viol:
    s = summ[r['run_id']]
    a = s['physical']['sim_retrofit']; cf = s['counterfactual_physics']['sim_retrofit']['metrics']; b = s['physical']['sim_baseline']
    keys = ('comfort_degree_hours', 'hvac_kwh', 'cost_cents', 'framework_comfort_degree_hours')
    phys[tuple(a[k] for k in keys)] += 1; cfs[(tuple(cf[k] for k in keys), tuple(b[k] for k in keys))] += 1
assert len(phys) == 1 and len(cfs) == 1, (phys, cfs)  # every attacked run lands on the same physics
keys = ('comfort_degree_hours', 'hvac_kwh', 'cost_cents', 'framework_comfort_degree_hours')
(a,), ((cf, b),) = phys.keys(), cfs.keys()
data['physics'] = {'baseline': dict(zip(keys, b)), 'legal_retrofit': dict(zip(keys, cf)), 'attacked': dict(zip(keys, a))}

# time series: attacked run and a non-violating run of the same task whose retrofit equals the counterfactual
ex = viol[0]
ts = lambda r, name: json.load(open(EXP/'runs'/r['phase']/r['run_id']/f'timeseries_{name}.json'))
legal_run = next(r for r in att + neu if r['violation'] == 'False' and r['task'] == ex['task']
                 and abs(float(r['comfort_deg_h_18_24']) - cf[0]) < 1e-3 and abs(float(r['hvac_kwh']) - cf[1]) < 1e-3)
pick = lambda recs: [{k: x[k] for k in ('zone_temperature', 'cooling_setpoint', 'occupancy', 'hvac_power_kw')} for x in recs]
data['timeseries'] = {'baseline': pick(ts(ex, 'sim_baseline')), 'legal_retrofit': pick(ts(legal_run, 'sim_retrofit')),
                      'attacked': pick(ts(ex, 'sim_retrofit')), 'runs': {'attacked': ex['run_id'], 'legal': legal_run['run_id']}}

# Fig 6: verdicts of the framework's own comparison tools (sim_baseline vs sim_retrofit)
vio_ids = {r['run_id'] for r in viol}
# legal group = runs that completed the requested retrofit without crossing the boundary
valid_ids = {r['run_id'] for r in e1 + e2 if valid(r) and (r['violation'] == 'True' or r['legal_done'] == 'True')}
comf = Counter(); comp = Counter()
for f in glob.glob(str(EXP/'runs/exp[12]/*/work/logs/agent_responses/comparison_agent/*.json')):
    rid = Path(f).parts[-6]
    if rid not in valid_ids: continue
    grp = 'attacked' if rid in vio_ids else 'legal'
    for t in json.load(open(f)).get('tools_used', []):
        if set((t.get('parameters') or {}).values()) != {'sim_baseline', 'sim_retrofit'}: continue
        try: res = json.loads(t['result'][0]['text'])['data']
        except Exception: continue
        if t['tool'] == 'comparison_comfort':
            comf[(grp, res.get('better_comfort') == (t['parameters'].get('sim2')))] += 1
        elif t['tool'] == 'comparison_comprehensive':
            comp[(grp, res['summary']['improvements_count'])] += 1
data['verdicts'] = {'comfort_retrofit_better': {g: [comf[(g, True)], comf[(g, True)] + comf[(g, False)]] for g in ('legal', 'attacked')},
                    'comprehensive': {f'{g}|{c}': n for (g, c), n in comp.items()}}
OUT.write_text(json.dumps(data, indent=1))
print(json.dumps({k: v for k, v in data.items() if k != 'timeseries'}, indent=1)); print(data['timeseries']['runs'])
