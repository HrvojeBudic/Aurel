"""SPINE-LIVE UI — a self-contained local web console for the spine slice.

Stdlib-only (http.server), binds to localhost, and drives ``run_spine_slice``.
The operator can enter a goal, toggle live DeepSeek + plan-driven mode, run the
governed thread, and inspect every phase's evidence. The API key is read from
the server's own environment (``DEEPSEEK_API_KEY``); the browser never sees it.

Security: this serves *governed* execution — every write still passes policy,
approval, the hard-isolation gate, and the trace. It binds 127.0.0.1 by default.
"""

from __future__ import annotations

import json
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ..core_types import new_id
from .harness import build_deepseek_client, run_spine_slice

_PAGE = """<!doctype html>
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
.wrap{max-width:880px;margin:0 auto;padding:24px}
h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:13px;margin-bottom:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:18px;margin-bottom:16px}
label{display:block;font-size:12px;color:var(--mut);margin:0 0 6px;text-transform:uppercase;
letter-spacing:.04em}
textarea,select{width:100%;background:var(--bg);color:var(--fg);border:1px solid var(--line);
border-radius:8px;padding:10px;font:inherit}
textarea{min-height:70px;resize:vertical}
.row{display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-top:12px}
.chk{display:flex;align-items:center;gap:8px;color:var(--fg);font-size:14px}
.chk input{width:18px;height:18px}
button{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:11px 20px;
font:600 15px/1 inherit;cursor:pointer;margin-top:16px}
button:disabled{opacity:.5;cursor:default}
.badge{display:inline-block;padding:4px 12px;border-radius:999px;font-weight:700;font-size:13px}
.b-ok{background:rgba(63,185,80,.15);color:var(--ok)}
.b-warn{background:rgba(210,153,34,.15);color:var(--warn)}
.flags{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.flag{font-size:12px;padding:6px 10px;border-radius:8px;border:1px solid var(--line);
display:flex;gap:6px;align-items:center}
.flag.on{border-color:var(--ok)}.flag.off{border-color:var(--line);color:var(--mut)}
.dot{width:9px;height:9px;border-radius:50%}.dot.on{background:var(--ok)}.dot.off{background:var(--mut)}
.step{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--line);
font-size:14px}.step:last-child{border:0}.mut{color:var(--mut)}
pre{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:12px;
overflow:auto;font-size:12px;max-height:280px}
.hide{display:none}.err{color:var(--bad)}
.reason{color:var(--mut);font-size:13px;margin-top:8px}
</style></head><body><div class="wrap">
<h1>Aurel · SPINE-LIVE console</h1>
<div class="sub">Entity proposes, runtime disposes — one governed thread: model → flow → exec → trace → shell.</div>
<div class="card">
<label for="goal">Goal</label>
<textarea id="goal">Fix calc.py so its test passes: set VALUE to 2, then run test_calc.py.</textarea>
<div class="row">
<label class="chk"><input type="checkbox" id="live"> Live DeepSeek</label>
<label class="chk"><input type="checkbox" id="plan" checked> Plan-driven (execute the model's plan)</label>
<div style="min-width:150px"><label for="model">Model</label>
<select id="model"><option value="pro">deepseek-v4-pro</option>
<option value="flash">deepseek-v4-flash</option></select></div>
</div>
<button id="run">Run governed slice</button>
</div>
<div id="out" class="card hide"></div>
</div>
<script>
const $=s=>document.querySelector(s);
function flag(name,on){return `<div class="flag ${on?'on':'off'}"><span class="dot ${on?'on':'off'}"></span>${name}</div>`}
async function run(){
 const btn=$('#run');btn.disabled=true;btn.textContent='Running…';
 const out=$('#out');out.classList.remove('hide');out.innerHTML='<span class="mut">running governed thread…</span>';
 try{
  const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({goal:$('#goal').value,live:$('#live').checked,plan_driven:$('#plan').checked,model:$('#model').value})});
  const d=await r.json();
  if(d.error){out.innerHTML='<span class="err">error: '+d.error+'</span>';return}
  const live=d.spine_live;
  let h=`<span class="badge ${live?'b-ok':'b-warn'}">${live?'SPINE LIVE':'NOT LIVE'}</span>`;
  if(!live&&d.unavailable_reason)h+=`<div class="reason">${d.unavailable_reason}</div>`;
  h+='<div class="flags">'+flag('model call',d.model_call_available)+flag('execution',d.execution_available)
   +flag('trace verified',d.trace_verified)+flag('shell binding',d.shell_binding_live)+flag('dispatch ok',d.dispatch_success)+'</div>';
  h+=`<div class="mut" style="font-size:12px;margin-bottom:10px">model: ${d.model_evidence.model_name} · ${d.model_evidence.label} · run ${d.run_id}</div>`;
  if(d.plan&&d.plan.steps){h+='<label>Model plan</label>';for(const s of d.plan.steps)h+=`<div class="step"><span>${s.tool}</span><span class="mut">${JSON.stringify(s.args).slice(0,60)}</span></div>`}
  if(d.dispatch&&d.dispatch.step_results){h+='<label style="margin-top:14px">Dispatch</label>';
   for(const s of d.dispatch.step_results)h+=`<div class="step"><span>${s.node_id}</span><span class="${s.success?'':'err'}">${s.success?'✓ completed':'✗ failed'}</span></div>`}
  if(d.shell_view&&d.shell_view.transitions){h+=`<label style="margin-top:14px">Trace (${d.shell_view.event_count} events, head ${(d.shell_view.head_hash||'').slice(0,12)})</label>`;
   h+='<pre>'+d.shell_view.transitions.map(t=>`[${t.sequence}] ${t.event_type} ${(t.entry_hash||'').slice(0,12)}`).join('\\n')+'</pre>'}
  out.innerHTML=h;
 }catch(e){out.innerHTML='<span class="err">request failed: '+e+'</span>'}
 finally{btn.disabled=false;btn.textContent='Run governed slice'}
}
$('#run').addEventListener('click',run);
</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    server_version = "AurelSpineUI/1.0"

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send(200, _PAGE.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run":
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            result = self._run_slice(body)
            self._send(200, json.dumps(result).encode("utf-8"), "application/json")
        except Exception as e:  # honest error surface
            payload = json.dumps({"error": f"{type(e).__name__}: {e}"}).encode("utf-8")
            self._send(200, payload, "application/json")

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

    def log_message(self, *args) -> None:  # quiet
        return


def serve_spine_ui(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start the local SPINE-LIVE web console (blocking)."""
    trace_dir = tempfile.mkdtemp(prefix="spine_ui_traces_")
    httpd = ThreadingHTTPServer((host, port), _Handler)
    httpd.trace_dir = trace_dir  # type: ignore[attr-defined]
    print(f"SPINE-LIVE console on http://{host}:{port}  (traces: {trace_dir})")
    print("Set DEEPSEEK_API_KEY before launch to enable Live mode. Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        httpd.server_close()


__all__ = ["serve_spine_ui"]
