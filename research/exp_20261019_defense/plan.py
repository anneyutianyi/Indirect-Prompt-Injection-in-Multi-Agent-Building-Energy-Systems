"""Defence experiment: D1 (parameter guard in the tool server) and D2 (content-source wrapping) x channels A/B; task R1 (E1c);
30 attack + 30 neutral per cell, K1-K4 / M1-M4 rotation, seed 20261019."""
import json,random,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import protocol_v3 as V3
CELLS={'D1-A':('A','D1'),'D1-B':('B','D1'),'D2-A':('A','D2'),'D2-B':('B','D2')}
def spec(phase,cell,cond,r):
 entry,guard=CELLS[cell]
 pid=(V3.attack_payload_id if cond=='attack' else V3.neutral_payload_id)(r)
 rid=f'{phase}_{cell}_{cond}_r{r:02d}'
 return {'run_id':rid,'phase':phase,'cell':cell,'entry':entry,'guard':guard,'task':'E1c','condition':cond,'repeat':r,'payload_id':pid,
  'target':'T1','model':'deepseek-flash','legacy_request':True,'mode':'decentralized','outdir':str(HERE/'runs'/phase/rid)}
if __name__=='__main__':
 rows=[spec('main',c,cond,r) for c in CELLS for cond in ('attack','neutral') for r in range(30)]
 random.Random(20261019).shuffle(rows)
 for i,x in enumerate(rows):x['order']=i
 (HERE/'manifest_main.json').write_text(json.dumps(rows,indent=1))
 sc=[]
 for c in CELLS:
  x=spec('selfcheck',c,'neutral',0);x['run_id']=f'selfcheck_{c}_neutral';x['outdir']=str(HERE/'runs'/'selfcheck'/x['run_id']);sc.append(x)
 (HERE/'manifest_selfcheck.json').write_text(json.dumps(sc,indent=1))
 print(len(rows),len(sc))
