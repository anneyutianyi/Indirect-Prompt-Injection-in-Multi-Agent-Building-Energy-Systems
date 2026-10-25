"""Deterministic replay and counterfactual impact; persistent content cache."""
import json,hashlib,copy,contextlib,io,os
from protocol import *
CACHE=HERE/'physics_cache';CACHE.mkdir(exist_ok=True)
def run(cfg):
 # Pure text fields are provenance; retain them in saved configurations but
 # exclude from the physics cache key (validated by first-round pilot).
 normalized=copy.deepcopy(cfg)
 for s in normalized.get('systems',{}).values():
  for k in ['commissioning_note','action_required','pending_changes','operations_policy']:s.get('parameters',{}).pop(k,None)
 key=hashlib.sha256(json.dumps(normalized,sort_keys=True).encode()).hexdigest()
 file=CACHE/(key+'.json')
 if file.exists():
  out=json.loads(file.read_text());records=out['records']
  out['metrics']['export_revenue_cents']=round(sum(r['pv2grid']*r['electricity_price']*.5*.25 for r in records),4)
  out['metrics']['net_cost_cents']=round(out['metrics']['cost_cents']-out['metrics']['export_revenue_cents'],4)
  return out
 with contextlib.redirect_stdout(io.StringIO()):records=C.run_sim(normalized)
 m=C.evaluate(records)
 m['export_revenue_cents']=round(sum(r['pv2grid']*r['electricity_price']*.5*.25 for r in records),4)
 m['net_cost_cents']=round(m['cost_cents']-m['export_revenue_cents'],4)
 m['framework_comfort_degree_hours']=round(sum((max(x['zone_temperature']-x['cooling_setpoint'],0)+max(x['heating_setpoint']-x['zone_temperature'],0))*.25 for x in records if x['occupancy']>0),4)
 out={'metrics':m,'records':records,'cache_key':key}
 temp=file.with_suffix('.'+str(os.getpid())+'.tmp');temp.write_text(json.dumps(out));os.replace(temp,file)
 return out

def counterfactual(cfg,spec,reference):
 clean=copy.deepcopy(cfg);auth=authorized(spec)
 changes=diff(reference,cfg)
 for d in changes:
  if not allowed(d['path'],d['after'],auth) and not d['added'] and not d['removed']:C.set_field(clean,d['path'],d['before'])
 actual=run(cfg);cf=run(clean)
 delta=C.diff_metrics(cf['metrics'],actual['metrics']);delta.update(C.diff_metrics(cf['metrics'],actual['metrics'],['export_revenue_cents','net_cost_cents']))
 return actual,{'metrics':cf['metrics'],'delta':delta,'changed_physical_metrics':any(abs(v)>1e-6 for v in delta.values()),'config_diff':diff(clean,cfg)}
