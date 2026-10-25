"""Manifests for claude-haiku-5-5: 1-1 attack, 1-1 neutral, 1-3 attack (30 each), seed 20261019; selfcheck = 3 neutral."""
import json,random,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import protocol_v3 as V3
MODEL='claude-haiku-5-5'
CELLS={'1-2':('B','E1c',None),'1-1':('A','E1c',None),'1-3':('C','E1c',None),'2-P1':('A','E1c','P1')}
def spec(phase,cell,cond,r):
 entry,task,pol=CELLS[cell]
 pid=(V3.attack_payload_id if cond=='attack' else V3.neutral_payload_id)(r)
 rid=f'{phase}_{cell}_{cond}_r{r:02d}'
 x={'run_id':rid,'phase':phase,'cell':cell,'entry':entry,'task':task,'condition':cond,'repeat':r,'payload_id':pid,
  'target':'T1','model':MODEL,'legacy_request':True,'mode':'decentralized','outdir':str(HERE/'runs'/phase/rid)}
 if pol:x['policy']=pol
 return x
def shuffled(rows):
 random.Random(20261019).shuffle(rows)
 for i,x in enumerate(rows):x['order']=i
 return rows
if __name__=='__main__':
 main=shuffled([spec('main',c,cond,r) for c,cond in (('1-1','attack'),('1-1','neutral'),('1-3','attack')) for r in range(30)])
 (HERE/'manifest_main.json').write_text(json.dumps(main,indent=1))
 sc=[]
 for r in range(3):
  x=spec('selfcheck','1-1','neutral',r);x['run_id']=f'selfcheck_1-1_neutral_r{r}';x['outdir']=str(HERE/'runs'/'selfcheck'/x['run_id']);sc.append(x)
 (HERE/'manifest_selfcheck.json').write_text(json.dumps(sc,indent=1))
 (HERE/'manifest_p1.json').write_text(json.dumps(shuffled([spec('p1','2-P1','attack',r) for r in range(30)]),indent=1))
 (HERE/'manifest_main12.json').write_text(json.dumps(shuffled([spec('main12','1-2',cond,r) for cond in ('attack','neutral') for r in range(30)]),indent=1))
 print(len(main),len(sc))
