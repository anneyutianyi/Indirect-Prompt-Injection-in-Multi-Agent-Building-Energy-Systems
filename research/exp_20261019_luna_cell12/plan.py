"""GPT-6 Luna via OpenRouter: cell 1-2 (entry B, task R1), 30 attack + 30 neutral, seed 20261019; selfcheck = 2 neutral."""
import json,random,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import protocol_v3 as V3
CELLS={'1-2':('B','E1c'),'1-1':('A','E1c'),'1-3':('C','E1c')}
def spec(phase,cond,r,cell='1-2'):
 pid=(V3.attack_payload_id if cond=='attack' else V3.neutral_payload_id)(r)
 rid=f'{phase}_{cell}_{cond}_r{r:02d}'
 return {'run_id':rid,'phase':phase,'cell':cell,'entry':CELLS[cell][0],'task':CELLS[cell][1],'condition':cond,'repeat':r,'payload_id':pid,
  'target':'T1','model':'gpt-6-luna','legacy_request':True,'mode':'decentralized','outdir':str(HERE/'runs'/phase/rid)}
if __name__=='__main__':
 rows=[spec('main',c,r) for c in ('attack','neutral') for r in range(30)];random.Random(20261019).shuffle(rows)
 for i,x in enumerate(rows):x['order']=i
 (HERE/'manifest_main.json').write_text(json.dumps(rows,indent=1))
 (HERE/'manifest_selfcheck.json').write_text(json.dumps([spec('selfcheck','neutral',r) for r in range(2)],indent=1))

 (HERE/'manifest_main13.json').write_text(json.dumps([dict(x,order=i) for i,x in enumerate((lambda L:(random.Random(20261020).shuffle(L),L)[1])([spec('main13',c,r,cell) for cell in ('1-1','1-3') for c in ('attack','neutral') for r in range(30)]))],indent=1))
