"""SPINE-LIVE UI — a self-contained local web console for the governed runtime.

Stdlib-only (http.server), binds to localhost, and exposes the whole M0–M7 body
of work as live, inspectable panels:

* **Slice** — drive one governed thread (model → flow → exec → trace → shell) and
  read every phase's evidence flag (``run_spine_slice``).
* **Host** — the functional sandbox probes + which governance levels are
  physically achievable on this host (``doctor``, M0).
* **Governance** — the G0–G5 spectrum, the precedence resolver, and a run's
  drift audit (M6).
* **Replay** — record-then-replay a run from a model cassette and confirm the
  governed mutations reproduce the same world-state with no network (M5).

Security: this serves *governed* execution — every write still passes policy,
approval, the hard-isolation gate, and the trace. It binds 127.0.0.1 by default.
The DeepSeek API key is read from the server env; the browser never sees it.
"""

from __future__ import annotations

import json
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ..core_types import new_id
from .harness import build_deepseek_client, replay_spine_run, run_spine_slice

_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aurel · SPINE-LIVE console</title>
<style>
:root{--bg:#0b0d12;--card:#151922;--fg:#e6e9ef;--mut:#8b93a7;--line:#252b38;
--ok:#3fb950;--warn:#d29922;--bad:#f85149;--acc:#4f8cff}
@media(prefers-color-scheme:light){:root{--bg:#f6f7f9;--card:#fff;--fg:#12151c;
--mut:#5b6472;--line:#e3e7ee;--acc:#2b6cff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:24px}
h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:13px;margin-bottom:18px}
.tabs{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap}
.tab{padding:8px 16px;border:1px solid var(--line);border-radius:999px;cursor:pointer;
font-size:14px;color:var(--mut);background:transparent}
.tab.active{color:#fff;background:var(--acc);border-color:var(--acc)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:18px;margin-bottom:16px}
label{display:block;font-size:12px;color:var(--mut);margin:0 0 6px;text-transform:uppercase;
letter-spacing:.04em}
textarea,select{width:100%;background:var(--bg);color:var(--fg);border:1px solid var(--line);
border-radius:8px;padding:10px;font:inherit}
textarea{min-height:70px;resize:vertical}
.row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end;margin-top:12px}
.col{flex:1;min-width:130px}
.chk{display:flex;align-items:center;gap:8px;color:var(--fg);font-size:14px}
.chk input{width:18px;height:18px}
button{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:11px 20px;
font:600 15px/1 inherit;cursor:pointer;margin-top:16px}
button:disabled{opacity:.5;cursor:default}
.badge{display:inline-block;padding:4px 12px;border-radius:999px;font-weight:700;font-size:13px}
.b-ok{background:rgba(63,185,80,.15);color:var(--ok)}
.b-warn{background:rgba(210,153,34,.15);color:var(--warn)}
.b-bad{background:rgba(248,81,73,.15);color:var(--bad)}
.flags{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.flag{font-size:12px;padding:6px 10px;border-radius:8px;border:1px solid var(--line);
display:flex;gap:6px;align-items:center}
.flag.on{border-color:var(--ok)}.flag.off{border-color:var(--line);color:var(--mut)}
.dot{width:9px;height:9px;border-radius:50%}.dot.on{background:var(--ok)}.dot.off{background:var(--mut)}
.dot.bad{background:var(--bad)}
.step{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--line);
font-size:14px}.step:last-child{border:0}.mut{color:var(--mut)}
pre{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:12px;
overflow:auto;font-size:12px;max-height:280px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:600;text-transform:uppercase;font-size:11px;letter-spacing:.04em}
.hide{display:none}.err{color:var(--bad)}
.reason{color:var(--mut);font-size:13px;margin-top:8px}
.pill{font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid var(--line)}
.pill.ok{color:var(--ok);border-color:var(--ok)}.pill.no{color:var(--mut)}
</style></head><body><div class="wrap">
<h1>Aurel · SPINE-LIVE console</h1>
<div class="sub">Entity proposes, runtime disposes. Governed thread + host attestation + governance scale + deterministic replay.</div>
<div class="tabs">
<div class="tab active" data-tab="slice">Slice</div>
<div class="tab" data-tab="host">Host</div>
<div class="tab" data-tab="gov">Governance</div>
<div class="tab" data-tab="replay">Replay</div>
</div>

<!-- SLICE -->
<div id="p-slice">
<div class="card">
<label for="goal">Goal</label>
<textarea id="goal">Fix calc.py so its test passes: set VALUE to 2, then run test_calc.py.</textarea>
<div class="row">
<label class="chk"><input type="checkbox" id="live"> Live DeepSeek</label>
<label class="chk"><input type="checkbox" id="plan" checked> Plan-driven</label>
<div style="min-width:150px"><label for="model">Model</label>
<select id="model"><option value="pro">deepseek-v4-pro</option>
<option value="flash">deepseek-v4-flash</option></select></div>
</div>
<button id="run">Run governed slice</button>
</div>
<div id="out" class="card hide"></div>
</div>

<!-- HOST -->
<div id="p-host" class="hide">
<div class="card">
<div class="mut" style="font-size:13px;margin-bottom:4px">Functional sandbox probes — real isolated execution, not a version check.</div>
<button id="doctor">Run doctor</button>
<div id="hostout"></div>
</div>
</div>

<!-- GOVERNANCE -->
<div id="p-gov" class="hide">
<div class="card">
<label>Governance spectrum · ABSOLUTE GOVERNED (G0) ⟷ HERETIC (G5)</label>
<div id="govlevels"></div>
</div>
<div class="card">
<label>Precedence resolver — most restrictive wins</label>
<div class="row">
<div class="col"><label for="gsys">System</label><select id="gsys" class="glvl"></select></div>
<div class="col"><label for="gagent">Agent</label><select id="gagent" class="glvl"></select></div>
<div class="col"><label for="gtask">Task</label><select id="gtask" class="glvl"></select></div>
</div>
<div class="row">
<label class="chk"><input type="checkbox" id="ganchor" checked> anchor available</label>
<label class="chk"><input type="checkbox" id="gattest" checked> attestation ok</label>
</div>
<button id="gresolve">Resolve effective level</button>
<div id="govout"></div>
</div>
</div>

<!-- REPLAY -->
<div id="p-replay" class="hide">
<div class="card">
<div class="mut" style="font-size:13px;margin-bottom:4px">Record a run's model I/O, then replay it from the cassette — no network. Determinism is checked at the governed-mutation world-state level.</div>
<button id="replay">Record &amp; replay</button>
<div id="replayout"></div>
</div>
</div>

</div>
<script>
const $=s=>document.querySelector(s);
const $$=s=>document.querySelectorAll(s);
function flag(name,on){return `<div class="flag ${on?'on':'off'}"><span class="dot ${on?'on':'off'}"></span>${name}</div>`}
function badge(t,cls){return `<span class="badge ${cls}">${t}</span>`}

// tabs
$$('.tab').forEach(t=>t.addEventListener('click',()=>{
 $$('.tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');
 for(const p of ['slice','host','gov','replay'])$('#p-'+p).classList.toggle('hide',p!==t.dataset.tab);
 if(t.dataset.tab==='gov'&&!$('#gsys').options.length)loadLevels();
}));

// ---- slice ----
async function run(){
 const btn=$('#run');btn.disabled=true;btn.textContent='Running…';
 const out=$('#out');out.classList.remove('hide');out.innerHTML='<span class="mut">running governed thread…</span>';
 try{
  const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({goal:$('#goal').value,live:$('#live').checked,plan_driven:$('#plan').checked,model:$('#model').value})});
  const d=await r.json();
  if(d.error){out.innerHTML='<span class="err">error: '+d.error+'</span>';return}
  const live=d.spine_live;
  let h=badge(live?'SPINE LIVE':'NOT LIVE',live?'b-ok':'b-warn');
  if(!live&&d.unavailable_reason)h+=`<div class="reason">${d.unavailable_reason}</div>`;
  h+='<div class="flags">'+flag('model call',d.model_call_available)+flag('execution',d.execution_available)
   +flag('trace verified',d.trace_verified)+flag('shell binding',d.shell_binding_live)+flag('dispatch ok',d.dispatch_success)+'</div>';
  h+=`<div class="mut" style="font-size:12px;margin-bottom:10px">model: ${d.model_evidence.model_name} · ${d.model_evidence.label} · run ${d.run_id}</div>`;
  if(d.plan&&d.plan.steps){h+='<label>Model plan</label>';for(const s of d.plan.steps)h+=`<div class="step"><span>${s.tool}</span><span class="mut">${JSON.stringify(s.args).slice(0,60)}</span></div>`}
  if(d.dispatch&&d.dispatch.step_results){h+='<label style="margin-top:14px">Dispatch</label>';
   for(const s of d.dispatch.step_results)h+=`<div class="step"><span>${s.node_id} <span class="mut">×${s.attempts||1}</span></span><span class="${s.success?'':'err'}">${s.success?'✓ completed':'✗ failed'}</span></div>`}
  if(d.shell_view&&d.shell_view.transitions){h+=`<label style="margin-top:14px">Trace (${d.shell_view.event_count} events, head ${(d.shell_view.head_hash||'').slice(0,12)})</label>`;
   h+='<pre>'+d.shell_view.transitions.map(t=>`[${t.sequence}] ${t.event_type} ${(t.entry_hash||'').slice(0,12)}`).join('\n')+'</pre>'}
  out.innerHTML=h;
 }catch(e){out.innerHTML='<span class="err">request failed: '+e+'</span>'}
 finally{btn.disabled=false;btn.textContent='Run governed slice'}
}
$('#run').addEventListener('click',run);

// ---- host / doctor ----
async function doctor(){
 const btn=$('#doctor');btn.disabled=true;btn.textContent='Probing…';
 const out=$('#hostout');out.innerHTML='<span class="mut">running functional probes…</span>';
 try{
  const d=await (await fetch('/api/doctor')).json();
  let h=badge(d.healthy?'HEALTHY':'DEGRADED',d.healthy?'b-ok':'b-warn');
  h+='<table><tr><th>backend</th><th>state</th><th>reason</th></tr>';
  for(const s of d.sandboxes){const st=s.available&&s.hard_isolated?'ok':(s.available?'soft':'fail');
   h+=`<tr><td>${s.backend}</td><td><span class="pill ${st==='ok'?'ok':'no'}">${st}</span></td><td class="mut">${s.reason}</td></tr>`}
  h+='</table>';
  h+='<label style="margin-top:14px">Governance levels achievable here</label><div class="flags">';
  for(const [lvl,info] of Object.entries(d.governance_levels))h+=flag(lvl,info.achievable);
  h+='</div>';
  h+='<label style="margin-top:10px">Checks</label>';
  for(const c of d.checks)h+=`<div class="step"><span>${c.check}</span><span class="${c.ok?'':'err'}">${c.ok?'✓':'✗'} <span class="mut">${c.reason||'ok'}</span></span></div>`;
  out.innerHTML=h;
 }catch(e){out.innerHTML='<span class="err">'+e+'</span>'}
 finally{btn.disabled=false;btn.textContent='Run doctor'}
}
$('#doctor').addEventListener('click',doctor);

// ---- governance ----
async function loadLevels(){
 const d=await (await fetch('/api/governance/levels')).json();
 let h='<table><tr><th>lvl</th><th>auto≤</th><th>cap</th><th>enforce</th><th>sbx</th><th>anchor</th><th>trace</th></tr>';
 for(const r of d){h+=`<tr><td><b>${r.level}</b></td><td>${r.auto_approve_max}</td><td>${r.reversibility_cap}</td>
  <td class="mut">${r.enforcement_mode}</td><td>${r.sandbox_required?'✓':'—'}</td><td>${r.anchor_required?'✓':'—'}</td><td>${r.trace_required?'✓':'—'}</td></tr>`}
 h+='</table><div class="mut" style="font-size:12px;margin-top:8px">Floor at every level incl. HERETIC: anchored trace on; no self-escalation.</div>';
 $('#govlevels').innerHTML=h;
 for(const sel of ['#gsys','#gagent','#gtask']){const e=$(sel);e.innerHTML=d.map(r=>`<option value="${r.level}">${r.level}</option>`).join('')}
 $('#gsys').value='G4';$('#gagent').value='G3';$('#gtask').value='G5';
}
async function resolve(){
 const out=$('#govout');out.innerHTML='<span class="mut">resolving…</span>';
 try{
  const d=await (await fetch('/api/governance/resolve',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({system:$('#gsys').value,agent:$('#gagent').value,task:$('#gtask').value,
    anchor:$('#ganchor').checked,attestation:$('#gattest').checked})})).json();
  if(d.error){out.innerHTML='<span class="err">'+d.error+'</span>';return}
  out.innerHTML=badge('EFFECTIVE '+d.level,'b-ok')+(d.override_applied?' '+badge('override','b-warn'):'')+
   `<div class="reason">${d.reason}</div>`;
 }catch(e){out.innerHTML='<span class="err">'+e+'</span>'}
}
$('#gresolve').addEventListener('click',resolve);

// ---- replay ----
async function replay(){
 const btn=$('#replay');btn.disabled=true;btn.textContent='Recording + replaying…';
 const out=$('#replayout');out.innerHTML='<span class="mut">record → replay (no network)…</span>';
 try{
  const d=await (await fetch('/api/replay',{method:'POST'})).json();
  if(d.error){out.innerHTML='<span class="err">'+d.error+'</span>';return}
  if(d.available===false){out.innerHTML=badge(d.truth_label||'UNAVAILABLE','b-warn')+
   `<div class="reason">${d.unavailable_reason||'replay unavailable — no hard-isolated sandbox'}</div>`;return}
  let h=badge(d.deterministic?'DETERMINISTIC':'NON-DETERMINISTIC',d.deterministic?'b-ok':'b-bad');
  if(d.sandbox)h+=' '+badge(d.truth_label||d.sandbox.backend,d.sandbox.security_boundary?'b-ok':'b-warn');
  h+='<div class="flags">'+flag('outcomes match',d.outcomes_match)+flag('no network on replay',!d.replay_used_network)+`<div class="flag on">cassette ${d.cassette_size}</div></div>`;
  h+='<label>Mutation world-states (record vs replay)</label><pre>';
  for(let i=0;i<d.original_state_hashes.length;i++){const a=d.original_state_hashes[i],b=d.replay_state_hashes[i];
   h+=`${a===b?'✓':'✗'} ${(a||'∅').slice(0,20)}  ${a===b?'==':'!='}  ${(b||'∅').slice(0,20)}\n`}
  h+='</pre>';out.innerHTML=h;
 }catch(e){out.innerHTML='<span class="err">'+e+'</span>'}
 finally{btn.disabled=false;btn.textContent='Record & replay'}
}
$('#replay').addEventListener('click',replay);
</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    server_version = "AurelSpineUI/2.0"

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj: dict) -> None:
        self._send(200, json.dumps(obj, default=str).encode("utf-8"), "application/json")

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send(200, _PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/api/doctor":
            self._safe(self._doctor)
        elif self.path == "/api/governance/levels":
            self._safe(self._gov_levels)
        else:
            self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        routes = {
            "/api/run": self._run_slice,
            "/api/governance/resolve": self._gov_resolve,
            "/api/replay": self._replay,
        }
        fn = routes.get(self.path)
        if fn is None:
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        self._safe(lambda: fn(self._body()))

    # ------------------------------------------------------------------ #
    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        return json.loads(raw or b"{}")

    def _safe(self, fn) -> None:
        """Run a zero-arg handler and JSON-encode its result, failing honestly."""
        try:
            self._json(fn())
        except Exception as e:  # noqa: BLE001 - honest error surface
            self._json({"error": f"{type(e).__name__}: {e}"})

    def _run_slice(self, body: dict) -> dict:
        live = bool(body.get("live"))
        model = str(body.get("model", "pro"))
        client = build_deepseek_client(model) if live else None
        kwargs = {}
        if body.get("goal"):
            kwargs["goal"] = str(body["goal"])
        result = run_spine_slice(
            trace_dir=self.server.trace_dir,  # type: ignore[attr-defined]
            run_id=new_id("ui"),
            model_client=client,
            plan_driven=bool(body.get("plan_driven")),
            **kwargs,
        )
        return result.to_dict()

    def _doctor(self) -> dict:
        from ..cli_modules.doctor import run_doctor

        return run_doctor()

    def _gov_levels(self) -> list:
        from ..governance.profile import GovernanceLevel, profile_for

        return [profile_for(lvl).to_dict() for lvl in GovernanceLevel]

    def _gov_resolve(self, body: dict) -> dict:
        from ..governance import GovernanceLevel, resolve_effective

        r = resolve_effective(
            system_ceiling=GovernanceLevel(body.get("system", "G4")),
            agent_ceiling=GovernanceLevel(body.get("agent", "G3")),
            task_request=GovernanceLevel(body.get("task", "G5")),
            anchor_available=bool(body.get("anchor", True)),
            attestation_ok=bool(body.get("attestation", True)),
        )
        return {
            "level": r.level.value,
            "reason": r.reason,
            "override_applied": r.override_applied,
            "profile": r.profile.to_dict(),
        }

    def _replay(self, body: dict) -> dict:
        # No silent unsafe fallback: replay requires a hard-isolated sandbox. If
        # none is available, return an honest UNAVAILABLE report (with reason) —
        # never claim a live/verified/deterministic result on an unsafe backend.
        # ``allow_unsafe`` is an explicit, clearly-labelled dev opt-in only.
        from .harness import resolve_replay_sandbox, unavailable_replay_report

        allow_unsafe = bool(body.get("allow_unsafe"))
        factory, posture = resolve_replay_sandbox(allow_unsafe=allow_unsafe)
        if factory is None:
            return unavailable_replay_report(posture)
        trace_dir = tempfile.mkdtemp(prefix="spine_ui_replay_")
        return replay_spine_run(trace_dir=trace_dir, sandbox_factory=factory)

    def log_message(self, *args) -> None:  # quiet
        return


def serve_spine_ui(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start the local SPINE-LIVE web console (blocking)."""
    trace_dir = tempfile.mkdtemp(prefix="spine_ui_traces_")
    httpd = ThreadingHTTPServer((host, port), _Handler)
    httpd.trace_dir = trace_dir  # type: ignore[attr-defined]
    print(f"SPINE-LIVE console on http://{host}:{port}  (traces: {trace_dir})")
    print("Tabs: Slice · Host · Governance · Replay. Set DEEPSEEK_API_KEY for Live mode. Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        httpd.server_close()


__all__ = ["serve_spine_ui"]
