"""Run a manifest in its frozen order, 4 concurrent worker processes, no replacement reruns."""
import sys,json,subprocess,time,os,signal,argparse,shutil,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
STOP=threading.Event();LOCK=threading.Lock();CONSEC=[0]

def events_of(d):
 p=d/'events.jsonl'
 return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
def interrupted(events):
 return any(e.get('kind')=='llm_error' and (e.get('status') is not None or e.get('error_type') in ('APIConnectionError','APITimeoutError')) for e in events)
def zero_response(events):
 return not any(e.get('kind')=='llm_invocation_success' for e in events)

def run_spec(spec):
 d=Path(spec['outdir']);d.mkdir(parents=True,exist_ok=True)
 if (d/'finished.json').exists():return json.loads((d/'finished.json').read_text())|{'run_id':spec['run_id'],'skipped':True}
 if STOP.is_set():return {'run_id':spec['run_id'],'not_started':True}
 sf=d/'spec.json';sf.write_text(json.dumps(spec,indent=2))
 t0=time.time()
 with (d/'worker.log').open('w') as log:
  p=subprocess.Popen([sys.executable,str(HERE/'worker.py'),str(sf)],cwd=REPO,stdout=log,stderr=log,start_new_session=True,
   env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'})
  try:rc=p.wait(timeout=1500)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=15)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   rc=124
 ev=events_of(d);intr=interrupted(ev)
 summ=json.loads((d/'summary.json').read_text()) if (d/'summary.json').exists() else {}
 rec={'run_id':spec['run_id'],'cell':spec.get('cell'),'condition':spec['condition'],'returncode':rc,'wall_s':round(time.time()-t0,1),
  'summary':bool(summ),'service_interrupted':intr,'zero_response':zero_response(ev),'status':summ.get('status'),
  'state_violation':summ.get('state_violation'),'legal_done':summ.get('legal_done')}
 # zero-response interruption: archive and (once) rerun is allowed by protocol
 (d/'finished.json').write_text(json.dumps(rec))
 return rec

def main():
 ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('--jobs',type=int,default=4);ap.add_argument('--limit',type=int)
 a=ap.parse_args()
 rows=json.loads(Path(a.manifest).read_text())
 if a.limit:rows=rows[:a.limit]
 name=Path(a.manifest).stem;log=HERE/f'driver_{name}.log'
 done=0;start=time.time()
 with ThreadPoolExecutor(a.jobs) as ex:
  futs=[ex.submit(run_spec,r) for r in rows]
  for f in as_completed(futs):
   rec=f.result();done+=1
   with LOCK:
    if rec.get('not_started') or rec.get('skipped'):pass
    elif rec['service_interrupted'] or (not rec['summary'] and rec['returncode']!=0 and rec['zero_response']):
     CONSEC[0]+=1
     if CONSEC[0]>=5 and not STOP.is_set():
      STOP.set();(HERE/f'paused_{name}.json').write_text(json.dumps({'reason':'5 consecutive service-interrupted trajectories','at':time.time(),'last':rec['run_id']}))
    else:CONSEC[0]=0
   line=f"{name} {done}/{len(rows)} t={int(time.time()-start)}s {rec.get('run_id')} cell={rec.get('cell')} status={rec.get('status')} viol={rec.get('state_violation')} legal={rec.get('legal_done')} intr={rec.get('service_interrupted')} consec={CONSEC[0]}"
   print(line,flush=True)
   with log.open('a') as fh:fh.write(line+'\n')
if __name__=='__main__':main()
