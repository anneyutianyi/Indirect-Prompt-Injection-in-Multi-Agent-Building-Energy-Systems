"""T2 (deadband 0.5->2.0): indoor-temperature metrics of the hit runs vs the matched neutral (legal) runs, same definitions as the paper's T1 analysis.
Uses the saved time series / summaries of today's batch only; no new simulations."""
import csv,json,collections,statistics as st
from pathlib import Path
HERE=Path(__file__).resolve().parent
rows=list(csv.DictReader(open(HERE/'results_main2.csv')))
def metrics(rid,sim='sim_maintenance'):
    d=HERE/'runs'/'main2'/rid
    ts=json.load(open(d/f'timeseries_{sim}.json'))
    occ=[r for r in ts if r['occupancy']>0]
    s=json.load(open(d/'summary.json'))['physical'][sim]
    return {'occ_mean':sum(r['zone_temperature'] for r in occ)/len(occ),'max':max(r['zone_temperature'] for r in ts),
            'occ_h':0.25*len(occ),'occ_h_above_26':0.25*sum(r['zone_temperature']>26 for r in occ),'occ_h_above_28':0.25*sum(r['zone_temperature']>28 for r in occ),
            'occ_h_above_24':0.25*sum(r['zone_temperature']>24 for r in occ),
            'hvac_kwh':s['hvac_kwh'],'cost_cents':s['cost_cents'],'comfort_degree_hours':s['comfort_degree_hours'],'framework_comfort':s['framework_comfort_degree_hours'],'grid_import_kwh':s['grid_import_kwh']}
hits=[r['run_id'] for r in rows if r['condition']=='attack' and r['violation']=='True']
neut=[r['run_id'] for r in rows if r['condition']=='neutral' and r['violation']=='False' and r['legal_done']=='True']
H=[metrics(i) for i in hits];N=[metrics(i) for i in neut]
B=[metrics(i,'sim_baseline') for i in neut]
key=lambda m:tuple(round(m[k],4) for k in m)
print('hits',len(hits),hits);print('neutral legal runs',len(neut))
print('distinct hit patterns',len({key(m) for m in H}),'distinct neutral patterns',len({key(m) for m in N}),'distinct baseline',len({key(m) for m in B}))
hm={k:st.mean(m[k] for m in H) for k in H[0]};nm={k:st.mean(m[k] for m in N) for k in N[0]};bm={k:st.mean(m[k] for m in B) for k in B[0]}
for k in hm:print(f"{k:22s} baseline {bm[k]:8.3f}  requested(neutral) {nm[k]:8.3f}  attacked {hm[k]:8.3f}  delta {hm[k]-nm[k]:+.3f}")
json.dump({'hits':hits,'n_neutral':len(neut),'attacked':hm,'requested_neutral':nm,'baseline':bm},open(HERE/'t2_indoor_metrics.json','w'),indent=1)
