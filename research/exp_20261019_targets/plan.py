"""Manifests for the new targets: T2 (fan power) and T3 (V2G off), channels A/B, 30 attack + 30 neutral each."""
import json,random,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import protocol_v3 as V3
COP='systems.hvac_system_1.parameters.system_config.chiller.rated_cop'
CELLS={ # cell: (entry, task, internal target key)
 'T2-A':('A','T2','T2'),'T2-B':('B','T2','T2'),'T3-A':('A','T3','T4'),'T3-B':('B','T3','T4'),
 'T2v2-A':('A','T2v2','T5'),'T2v2-B':('B','T2v2','T5'),
 'T3-C':('C','T3','T4'),'T2v2-C':('C','T2v2','T5')}
def spec(phase,cell,cond,r):
 entry,task,target=CELLS[cell]
 pid=(V3.attack_payload_id if cond=='attack' else V3.neutral_payload_id)(r)
 rid=f'{phase}_{cell}_{cond}_r{r:02d}'
 x={'run_id':rid,'phase':phase,'cell':cell,'entry':entry,'task':task,'condition':cond,'repeat':r,'payload_id':pid,
  'target':target,'model':'deepseek-flash','legacy_request':True,'mode':'decentralized','outdir':str(HERE/'runs'/phase/rid)}
 if task=='T2':x['authorized']={COP:4.0}
 if task=='T2v2':x['authorized']={COP:4.0,'controllers.hvac_controller_1.parameters.base_heating':17}
 return x
def shuffled(rows,seed=20261019):
 random.Random(seed).shuffle(rows)
 for i,x in enumerate(rows):x['order']=i
 return rows
def v2():
 sc=[]
 for c in ('T2v2-A','T2v2-B'):
  for cond in ('neutral','attack'):
   x=spec('selfcheck2',c,cond,0);x['run_id']=f'selfcheck2_{c}_{cond}';x['outdir']=str(HERE/'runs'/'selfcheck2'/x['run_id']);sc.append(x)
 main=shuffled([spec('main2',c,cond,r) for c in ('T2v2-A','T2v2-B') for cond in ('attack','neutral') for r in range(30)])
 (HERE/'manifest_selfcheck2.json').write_text(json.dumps(sc,indent=1));(HERE/'manifest_main2.json').write_text(json.dumps(main,indent=1))
def c3():
 sc=[]
 for c in ('T3-C','T2v2-C'):
  for cond in ('neutral','attack'):
   x=spec('selfcheck3',c,cond,0);x['run_id']=f'selfcheck3_{c}_{cond}';x['outdir']=str(HERE/'runs'/'selfcheck3'/x['run_id']);sc.append(x)
 main=shuffled([spec('main3',c,cond,r) for c in ('T3-C','T2v2-C') for cond in ('attack','neutral') for r in range(30)])
 (HERE/'manifest_selfcheck3.json').write_text(json.dumps(sc,indent=1));(HERE/'manifest_main3.json').write_text(json.dumps(main,indent=1))
if __name__=='__main__':
 c3()
 v2()
 main=shuffled([spec('main',c,cond,r) for c in ('T2-A','T2-B','T3-A','T3-B') for cond in ('attack','neutral') for r in range(30)])
 (HERE/'manifest_main.json').write_text(json.dumps(main,indent=1))
 sc=[]
 for c in ('T2-A','T2-B','T3-A','T3-B'):
  x=spec('selfcheck',c,'neutral',0);x['run_id']=f'selfcheck_{c}';x['outdir']=str(HERE/'runs'/'selfcheck'/x['run_id']);sc.append(x)
 (HERE/'manifest_selfcheck.json').write_text(json.dumps(sc,indent=1))
 print(len(main),len(sc))
