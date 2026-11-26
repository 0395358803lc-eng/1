import json
import importlib.util
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'workflow_state.py'
spec = importlib.util.spec_from_file_location('workflow_state', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state.json'
        self.ev = self.root / 'evidence.txt'
        self.ev.write_text('synthetic evidence', encoding='utf-8')
        self.identity = ['--job-id','test-job','--source-fingerprint','source-test','--config-fingerprint','config-test']
        self.run_cli('init','--mode','transcript-only')
    def run_cli(self, cmd, *args, ok=True, identity=None):
        args = [cmd,'--state',str(self.state),*([] if cmd=='resume' else self.identity if identity is None else identity),*map(str,args)]
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                result = module.execute(module.parser().parse_args(args))
        except (SystemExit, ValueError, OSError, KeyError, TypeError) as exc:
            if ok: raise
            return str(exc)
        self.assertTrue(ok, f"unexpected success: {args}")
        return result
    def prepare(self,n):
        return self.run_cli('prepare','--step',n,'--scope',f'Synthetic step {n}')['approval_request']
    def start(self,n,req):
        return self.run_cli('start','--step',n,'--approval-text',req['expected_text'])['attempt_id']
    def finish(self,n,aid,status='pass',evidence=True,ok=True):
        return self.run_cli('finish','--step',n,'--attempt-id',aid,'--status',status,'--note','test report',*(['--evidence',self.ev] if evidence else []),ok=ok)
    def complete(self,n):
        return self.finish(n,self.start(n,self.prepare(n)))
    def test_01_init(self):
        d=json.loads(self.state.read_text()); self.assertEqual(len(d['steps']),40); self.assertEqual(d['steps'][9]['status'],'out_of_scope')
    def test_02_no_overwrite(self): self.run_cli('init','--mode','transcript-only',ok=False)
    def test_03_evidence_required(self): self.finish(1,self.start(1,self.prepare(1)),evidence=False,ok=False)
    def test_04_one_step(self):
        self.complete(1); d=json.loads(self.state.read_text()); self.assertEqual([s['status'] for s in d['steps'][:3]],['pass','pending','pending'])
    def test_05_blocked_stays(self):
        self.finish(1,self.start(1,self.prepare(1)),'blocked',False); self.assertEqual(self.run_cli('resume')['next_step'],1)
    def test_06_partial_stays(self):
        self.finish(1,self.start(1,self.prepare(1)),'partial',False); self.assertEqual(self.run_cli('resume')['next_step'],1)
    def test_07_lock(self):
        self.state.with_name('state.json.lock').write_text('test'); self.run_cli('prepare','--step',1,'--scope','test',ok=False)
    def test_08_retry_new_approval(self):
        r=self.prepare(1); self.finish(1,self.start(1,r),'blocked',False); r2=self.prepare(1); self.assertNotEqual(r['id'],r2['id']); self.run_cli('start','--step',1,'--approval-text',r['expected_text'],ok=False); self.finish(1,self.start(1,r2))
    def test_09_changed_evidence(self):
        self.complete(1); self.ev.write_text('changed'); self.assertEqual(self.run_cli('resume')['status'],'stale'); self.run_cli('prepare','--step',2,'--scope','test',ok=False)
    def test_10_invalidation(self):
        self.complete(1); self.complete(2); self.run_cli('invalidate','--from-step',1,'--note','changed upstream'); d=json.loads(self.state.read_text()); self.assertEqual([s['status'] for s in d['steps'][:2]],['stale','stale'])
    def test_11_bad_step(self): self.run_cli('prepare','--step',41,'--scope','test',ok=False)
    def test_12_approval_required(self):
        self.run_cli('start','--step',1,'--approval-text','Tiếp tục',ok=False); self.prepare(1); self.run_cli('start','--step',1,'--approval-text','chạy toàn bộ',ok=False)
    def test_13_no_jump(self): self.run_cli('prepare','--step',2,'--scope','test',ok=False)
    def test_14_no_duplicate(self):
        r=self.prepare(1); a=self.start(1,r); self.run_cli('start','--step',1,'--approval-text',r['expected_text'],ok=False); self.finish(1,a); self.finish(1,a,ok=False); self.run_cli('prepare','--step',1,'--scope','test',ok=False)
    def test_15_transcript_limit(self):
        for n in range(1,10): self.complete(n)
        self.assertEqual(self.run_cli('resume')['status'],'complete'); self.assertIsNone(self.run_cli('resume')['next_step']); self.run_cli('prepare','--step',10,'--scope','test',ok=False)
    def test_16_log(self):
        log=self.root/'approval_log.json'; log.write_text(json.dumps([{'scope_type':'bootstrap','notes':'preserve'}])); self.complete(1); rows=json.loads(log.read_text()); self.assertEqual([r['status'] for r in rows[1:]],['started','pass']); self.assertEqual(rows[1]['approval_id'],rows[2]['approval_id']); self.assertEqual(rows[0]['notes'],'preserve'); self.run_cli('resume'); self.assertEqual(json.loads(log.read_text()),rows)
    def test_17_wrong_job_or_fingerprint(self):
        r=self.prepare(1)
        for j in (0,2,4):
            x=self.identity.copy(); x[j+1]='wrong'; self.run_cli('start','--step',1,'--approval-text',r['expected_text'],identity=x,ok=False)
    def test_18_wrong_attempt(self):
        self.start(1,self.prepare(1)); self.finish(1,'wrong',ok=False)
    def test_19_cancel_invalidates(self):
        r=self.prepare(1); self.run_cli('cancel','--step',1,'--request-id',r['id'],'--note','scope changed'); self.prepare(1); self.run_cli('start','--step',1,'--approval-text',r['expected_text'],ok=False)
    def test_20_replay_log_after_interrupt(self):
        self.complete(1); log=self.root/'approval_log.json'; rows=json.loads(log.read_text()); log.write_text(json.dumps(rows[:1])); self.run_cli('resume'); self.assertEqual(json.loads(log.read_text()),rows)
    def test_21_legacy_blocked(self):
        d=json.loads(self.state.read_text()); d['schema_version']=1; self.state.write_text(json.dumps(d)); self.run_cli('resume',ok=False)
    def test_22_full_mode(self):
        self.state=self.root/'full'/'state.json'; self.run_cli('init','--mode','full-review')
        for n in range(1,41):
            if n == 22: self.choose(self.offer()['options'][0])
            self.complete(n)
        self.assertIsNone(self.run_cli('resume')['next_step'])
    def test_23_running_blocks_invalidate(self):
        self.start(1,self.prepare(1)); self.run_cli('invalidate','--from-step',1,'--note','test',ok=False)
    def test_24_prepare_idempotent(self): self.assertEqual(self.prepare(1),self.prepare(1))

    def test_25_skip_requires_scope_and_evidence(self):
        a=self.start(1,self.prepare(1)); self.finish(1,a,'skipped',ok=False)
        self.finish(1,a,'blocked',False); r=self.run_cli('prepare','--step',1,'--scope','BỎ QUA: verified preparation already exists')['approval_request']; a=self.start(1,r); self.finish(1,a,'skipped',False,ok=False); self.finish(1,a,'skipped')
    def test_26_mandatory_transcript_not_skippable(self):
        for n in range(1,7): self.complete(n)
        r=self.run_cli('prepare','--step',7,'--scope','BỎ QUA: test')['approval_request']; self.finish(7,self.start(7,r),'skipped',ok=False)

    def full_to_voice(self):
        self.state=self.root/'full'/'state.json'
        self.run_cli('init','--mode','full-review')
        for n in range(1,22): self.complete(n)
    def offer(self, voices=None, ok=True):
        catalog=self.root/'voice-catalog.json'
        if voices is None:
            voices=[{'engine':'synthetic-engine-1','voice_id':'a','display_name':'Giọng A'}, {'engine':'synthetic-engine-1','voice_id':'b','display_name':'Giọng B'}]
        catalog.write_text(json.dumps(voices,ensure_ascii=False),encoding='utf-8')
        result=self.run_cli('offer-voices','--catalog',catalog,ok=ok)
        return result['voice_choice_request'] if ok else result
    def choose(self, option, ok=True):
        return self.run_cli('select-voice','--selection-text',option['expected_text'],ok=ok)
    def test_27_no_default_voice(self):
        self.full_to_voice()
        self.assertEqual(self.run_cli('resume')['status'],'waiting_voice_selection')
        self.run_cli('prepare','--step',22,'--scope','default voice',ok=False)
        self.run_cli('start','--step',22,'--approval-text','Tiếp tục',ok=False)
    def test_28_choice_not_execution_approval(self):
        self.full_to_voice(); option=self.offer()['options'][1]
        result=self.choose(option); self.assertEqual(result['voice_selection']['voice_id'],'b')
        self.assertIsNone(result['running_step']); self.assertIsNone(result['approval_request'])
        r=self.prepare(22); self.assertIn('Giọng B',r['expected_text'])
        self.run_cli('start','--step',22,'--approval-text',option['expected_text'],ok=False)
        self.finish(22,self.start(22,r))
        d=json.loads(self.state.read_text()); self.assertEqual(d['steps'][21]['attempt']['voice_selection']['voice_id'],'b')
        self.assertEqual(d['steps'][22]['status'],'pending')
        log=json.loads(self.state.with_name('approval_log.json').read_text())
        self.assertEqual([e['status'] for e in log if e['step_number']==22],['selected','started','pass'])
    def test_29_single_voice_requires_choice(self):
        self.full_to_voice(); offer=self.offer([{'engine':'e','voice_id':'one','display_name':'Only'}])
        self.assertIsNone(self.run_cli('resume')['voice_selection'])
        self.run_cli('prepare','--step',22,'--scope','one voice',ok=False)
        self.choose(offer['options'][0]); self.complete(22)
    def test_30_empty_invalid_catalog(self):
        self.full_to_voice(); self.offer([],ok=False); self.offer([{'engine':'e','voice_id':'','display_name':'bad'}],ok=False)
        self.assertIsNone(self.run_cli('resume')['voice_selection'])
    def test_31_stale_and_wrong_voice_choice(self):
        self.full_to_voice(); old=self.offer()['options'][0]; new=self.offer()['options'][1]
        self.choose(old,ok=False); self.run_cli('select-voice','--selection-text','Trúc Ly',ok=False)
        self.choose(new); self.choose(new,ok=False)
    def test_32_step24_bound_to_same_voice(self):
        self.full_to_voice(); self.choose(self.offer()['options'][1]); self.complete(22); self.complete(23)
        self.offer(ok=False); r=self.prepare(24); self.assertEqual(r['voice_selection']['voice_id'],'b')
        self.finish(24,self.start(24,r))
        self.assertEqual(json.loads(self.state.read_text())['steps'][23]['attempt']['voice_selection']['voice_id'],'b')
    def test_33_invalidation_clears_voice(self):
        self.full_to_voice(); self.choose(self.offer()['options'][0]); r=self.prepare(22)
        self.run_cli('invalidate','--from-step',22,'--note','approved voice change')
        self.assertIsNone(self.run_cli('resume')['voice_selection']); self.run_cli('start','--step',22,'--approval-text',r['expected_text'],ok=False)
        self.choose(self.offer()['options'][1]); self.complete(22)
    def test_34_transcript_no_voice(self):
        self.offer(ok=False); self.run_cli('select-voice','--selection-text','any',ok=False)
        self.assertIsNone(self.run_cli('resume')['voice_selection'])
    def test_35_voice_change_while_execution_pending_or_running(self):
        self.full_to_voice(); self.choose(self.offer()['options'][0]); r=self.prepare(22)
        self.offer(ok=False); a=self.start(22,r); self.offer(ok=False)
        self.finish(22,a,'blocked',False); self.choose(self.offer()['options'][1]); self.complete(22)
    def test_36_legacy_step22_request_blocked(self):
        self.full_to_voice(); d=json.loads(self.state.read_text()); d['request']={'id':'old','step':22,'scope':'old','expected_text':'old-approval','created_at':'old'}; d['steps'][21]['status']='waiting_approval'
        self.state.write_text(json.dumps(d)); self.run_cli('start','--step',22,'--approval-text','old-approval',ok=False)
        self.run_cli('cancel','--step',22,'--request-id','old','--note','upgrade'); self.choose(self.offer()['options'][0]); self.complete(22)
    def test_37_legacy_step24_requires_review(self):
        self.full_to_voice(); self.choose(self.offer()['options'][0]); self.complete(22); self.complete(23)
        d=json.loads(self.state.read_text()); d.pop('voice_selection'); d['steps'][21]['attempt'].pop('voice_selection'); self.state.write_text(json.dumps(d))
        self.run_cli('prepare','--step',24,'--scope','legacy',ok=False)
    def test_38_no_skip_tts(self):
        self.full_to_voice(); self.choose(self.offer()['options'][0]); r=self.run_cli('prepare','--step',22,'--scope','BỎ QUA: test')['approval_request']; self.finish(22,self.start(22,r),'skipped',ok=False)

if __name__=='__main__': unittest.main(verbosity=2)
