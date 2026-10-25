"""Build the experiment-1 manifest (7 cells x 30 attack + 30 neutral) and smoke manifest."""
import json,random,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import protocol_v3 as V3
CELLS={ # cell: (entry, task key in round-1 tasks.py)
 '1-0':('A','E1g'),'1-1':('A','E1c'),'1-2':('B','E1c'),'1-3':('C','E1c'),
 '1-4':('A','E1cc'),'1-5':('B','E1cc'),'1-6':('C','E1cc')}
def spec(phase,cell,cond,r):
 entry,task=CELLS[cell]
 if cell=='1-0':pid='REPRO_ATTACK' if cond=='attack' else 'REPRO_NEUTRAL'
 else:pid=(V3.attack_payload_id if cond=='attack' else V3.neutral_payload_id)(r)
 rid=f'{phase}_{cell}_{cond}_r{r:02d}'
 return {'run_id':rid,'phase':phase,'cell':cell,'entry':entry,'task':task,'condition':cond,'repeat':r,'payload_id':pid,
  'target':'T1','model':'deepseek-flash','legacy_request':True,'mode':'decentralized',
  'outdir':str(HERE/'runs'/phase/rid)}
def exp1():
 rows=[spec('exp1',c,cond,r) for c in CELLS for cond in ('attack','neutral') for r in range(30)]
 random.Random(20261009).shuffle(rows)
 for i,x in enumerate(rows):x['order']=i
 return rows
def smoke():
 rows=[spec('smoke',c,cond,0) for c in CELLS for cond in ('attack','neutral')]
 random.Random(20261009).shuffle(rows);return rows
def selfcheck():
 rows=[]
 for pol in ('P1','P2','P3'):
  for r in range(3):
   x=spec('selfcheck','1-1','neutral',r);x['policy']=pol;x['run_id']=f'selfcheck_{pol}_r{r}';x['outdir']=str(HERE/'runs'/'selfcheck'/x['run_id']);rows.append(x)
 return rows
def exp2():
 rows=[]
 for pol in ('P0','P1','P2','P3'):
  for cond in ('attack','neutral'):
   for r in range(30):
    x=spec('exp2','1-1',cond,r);x['cell']='2-'+pol;x['policy']=pol
    x['run_id']=f'exp2_2-{pol}_{cond}_r{r:02d}';x['outdir']=str(HERE/'runs'/'exp2'/x['run_id']);rows.append(x)
 random.Random(20261009).shuffle(rows)
 for i,x in enumerate(rows):x['order']=i
 return rows
def diag(window):
 rows=[]
 for r in range(30):
  x=spec('diag_'+window,'1-1','attack',r);x['run_id']=f'diag_{window}_1-1_attack_r{r:02d}';x['outdir']=str(HERE/'runs'/('diag_'+window)/x['run_id']);rows.append(x)
 random.Random(20261009).shuffle(rows);return rows
if __name__=='__main__':
 for w in ('day','night'):(HERE/f'manifest_diag_{w}.json').write_text(json.dumps(diag(w),indent=1))
 (HERE/'manifest_exp2.json').write_text(json.dumps(exp2(),indent=1))
 (HERE/'manifest_selfcheck.json').write_text(json.dumps(selfcheck(),indent=1))
 e=exp1();assert len(e)==420
 (HERE/'manifest_exp1.json').write_text(json.dumps(e,indent=1))
 (HERE/'manifest_smoke.json').write_text(json.dumps(smoke(),indent=1))
 from collections import Counter
 print(Counter((x['cell'],x['condition']) for x in e).most_common(3),len(e))
 print(Counter(x['payload_id'] for x in e if x['cell']=='1-1' and x['condition']=='attack'))
