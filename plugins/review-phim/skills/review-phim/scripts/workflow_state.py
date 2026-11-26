#!/usr/bin/env python3
"""Local job checkpoint helper; does not run media tasks."""
import argparse, datetime, hashlib, json, os, tempfile
from pathlib import Path
from contextlib import contextmanager

GOOD = {'pass','skipped'}
STATUS = ['pending','running','pass','partial','blocked','stale','skipped']
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
@contextmanager
def locked(path):
    lock=path.with_name(path.name+'.lock')
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,str(os.getpid()).encode()); os.close(fd); fd=None
        yield
    finally:
        if fd is not None: os.close(fd)
        lock.unlink()
def save(path,obj):
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+'.',suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def load(p):
    d=json.loads(p.read_text(encoding='utf-8'))
    if [x['step'] for x in d['steps']]!=list(range(1,41)):raise ValueError('invalid steps')
    return d
def step(v):
    n=int(v)
    if not 1<=n<=40:raise argparse.ArgumentTypeError('step must be 1..40')
    return n
def main():
    a=argparse.ArgumentParser(description=__doc__);s=a.add_subparsers(dest='cmd',required=True)
    for cmd in ['init','mark','resume','invalidate']:
        q=s.add_parser(cmd);q.add_argument('--state',required=True,type=Path)
        if cmd=='init':q.add_argument('--job-id',required=True);q.add_argument('--source-fingerprint',required=True)
        if cmd=='mark':
            q.add_argument('--step',type=step,required=True);q.add_argument('--status',choices=STATUS,required=True);q.add_argument('--evidence',action='append',type=Path,default=[]);q.add_argument('--note',required=True)
        if cmd=='invalidate':q.add_argument('--from-step',type=step,required=True);q.add_argument('--note',required=True)
    x=a.parse_args();p=x.state.resolve()
    if x.cmd=='resume':
        d=load(p);issues=[]
        for z in d['steps']:
            if z['status']=='pass':
                for e in z.get('evidence',[]):
                    f=Path(e['path'])
                    if not f.is_file() or sha(f)!=e['sha256']:issues.append({'step':z['step'],'path':str(f)})
        todo=next((z['step'] for z in d['steps'] if z['status'] not in GOOD),None)
        if issues:todo=min([z['step'] for z in issues]+([todo] if todo else []))
        print(json.dumps({'job_id':d['job_id'],'next_step':todo,'evidence_changes':issues,'note':'Recheck source/config fingerprints before continuing.'},ensure_ascii=False));return
    p.parent.mkdir(parents=True,exist_ok=True)
    with locked(p):
        if x.cmd=='init':
            if p.exists():raise FileExistsError(p)
            d={'schema_version':1,'job_id':x.job_id,'source_fingerprint':x.source_fingerprint,'steps':[{'step':i,'status':'pending'} for i in range(1,41)],'history':[]}
        else:
            d=load(p)
            if x.cmd=='mark':
                if x.status=='pass' and not x.evidence:raise ValueError('pass requires evidence file')
                ev=[{'path':str(f.resolve()),'sha256':sha(f.resolve())} for f in x.evidence]
                z=d['steps'][x.step-1];d['history'].append({'at':now(),'previous':dict(z)})
                z.update(status=x.status,note=x.note,evidence=ev,updated_at=now())
            else:
                for z in d['steps'][x.from_step-1:]:
                    if z['status']!='pending':
                        d['history'].append({'at':now(),'previous':dict(z)});z.update(status='stale',note=x.note,updated_at=now())
        d['updated_at']=now();save(p,d)
    print(json.dumps({'job_id':d['job_id'],'state':str(p),'status':'saved'},ensure_ascii=False))
if __name__=='__main__':main()
