"""
Clawidth - SoftAP + tiny HTTP config server.

Your phone joins the "Clawidth" wifi network, opens http://192.168.4.1, and gets
a one-page control panel: set the hourly rate, clock in/out, switch the display
mode. No internet, no app, no cloud.

Routes (all GET, kept dead-simple for the on-page fetch() calls):
  /                  -> the control panel (HTML)
  /state             -> current state as JSON (the page polls this every second)
  /set?rate=NN       -> set hourly rate
  /in                -> clock in
  /out               -> clock out
  /reset             -> zero the running total
  /mode?to=earnings  -> switch the watch display to the earnings ticker
  /mode?to=usage     -> switch the watch display to the Claude-usage readout
"""

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

import json
import network

import config


def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    try:
        ap.config(
            essid=config.AP_SSID,
            password=config.AP_PASSWORD,
            authmode=network.AUTH_WPA_WPA2_PSK,
        )
    except Exception:
        # some ports don't expose AUTH_WPA_WPA2_PSK by that name
        ap.config(essid=config.AP_SSID, password=config.AP_PASSWORD)
    return ap


PAGE = """<!DOCTYPE html><html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Clawidth</title>
<style>
:root{color-scheme:dark}
*{box-sizing:border-box;font-family:ui-monospace,Menlo,Consolas,monospace}
body{margin:0;background:#0a0c10;color:#e8eaed;display:flex;min-height:100vh;
 align-items:center;justify-content:center}
.card{width:100%;max-width:360px;padding:28px}
h1{font-size:13px;letter-spacing:.4em;color:#8b8f96;font-weight:600;margin:0 0 16px}
.amt{font-size:54px;font-weight:700;letter-spacing:.01em;margin:4px 0}
.sub{color:#8b8f96;font-size:13px;margin-bottom:22px}
label{display:block;font-size:11px;color:#8b8f96;margin:18px 0 6px;letter-spacing:.18em}
input{width:100%;padding:14px;background:#13161c;border:1px solid #262b34;
 border-radius:10px;color:#fff;font-size:20px}
.row{display:flex;gap:10px;margin-top:14px}
button{flex:1;padding:15px;border:1px solid #262b34;border-radius:10px;
 background:#13161c;color:#e8eaed;font-size:13px;letter-spacing:.12em;cursor:pointer}
button:active{transform:translateY(1px)}
.go{background:#e8eaed;color:#0a0c10;border-color:#e8eaed;font-weight:700}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;
 background:#3a3f47;margin-right:8px;vertical-align:middle}
.on .dot{background:#37d67a}
.muted{color:#5a5f67;font-size:11px;margin-top:26px;text-align:center;letter-spacing:.15em}
</style></head><body><div class="card">
<h1>CLAWIDTH</h1>
<div class="amt" id="amt">$0.00</div>
<div class="sub" id="sub"><span class="dot"></span><span id="st">--</span></div>
<label>HOURLY RATE</label>
<input id="rate" type="number" inputmode="decimal" step="0.01" min="0">
<div class="row"><button class="go" onclick="setRate()">SAVE RATE</button></div>
<div class="row">
 <button onclick="api('/in')">CLOCK IN</button>
 <button onclick="api('/out')">CLOCK OUT</button>
</div>
<div class="row">
 <button onclick="if(confirm('Reset total to $0?'))api('/reset')">RESET</button>
</div>
<label>DISPLAY MODE</label>
<div class="row">
 <button id="mEarn" onclick="setMode('earnings')">EARNINGS</button>
 <button id="mClaude" onclick="setMode('usage')">CLAUDE</button>
</div>
<div class="muted">CONNECTED TO CLAWIDTH</div>
</div><script>
let editing=false;
const r=document.getElementById('rate');
r.addEventListener('focus',()=>editing=true);
r.addEventListener('blur',()=>editing=false);
const fmt=n=>'$'+n.toFixed(2);
async function refresh(){
 try{const s=await(await fetch('/state')).json();
  document.getElementById('amt').textContent=fmt(s.earnings);
  document.getElementById('st').textContent=
   (s.running?'ON':'OFF')+'  ·  '+s.hms+'  ·  $'+s.rate.toFixed(2)+'/hr';
  document.getElementById('sub').className='sub'+(s.running?' on':'');
  document.getElementById('mEarn').classList.toggle('go',s.mode==='earnings');
  document.getElementById('mClaude').classList.toggle('go',s.mode==='usage');
  if(!editing&&document.activeElement!==r)r.value=s.rate.toFixed(2);
 }catch(e){}
}
async function api(p){await fetch(p);refresh()}
async function setRate(){await fetch('/set?rate='+encodeURIComponent(r.value));refresh()}
async function setMode(m){await fetch('/mode?to='+m);refresh()}
refresh();setInterval(refresh,1000);
</script></body></html>"""


def _hms(total_s):
    total_s = int(total_s)
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    return "%dh %02dm" % (h, m) if h else "%dm %02ds" % (m, s)


def _parse(path):
    q = {}
    if "?" in path:
        path, qs = path.split("?", 1)
        for pair in qs.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                q[k] = v
    return path, q


def _make_handler(state):
    async def handle(reader, writer):
        try:
            line = await reader.readline()
            if not line:
                return
            try:
                _method, raw_path, _ver = line.split(b" ", 2)
            except ValueError:
                return
            # drain the rest of the request headers
            while True:
                h = await reader.readline()
                if not h or h == b"\r\n":
                    break

            path, q = _parse(raw_path.decode())

            if path == "/":
                body, ctype = PAGE, "text/html"
            else:
                if path == "/set" and "rate" in q:
                    state.set_rate(q["rate"])
                elif path == "/in":
                    state.clock_in()
                elif path == "/out":
                    state.clock_out()
                elif path == "/reset":
                    state.reset()
                elif path == "/mode" and "to" in q:
                    state.set_mode(q["to"])
                body = json.dumps(
                    {
                        "rate": state.rate,
                        "running": state.running,
                        "earnings": state.earnings(),
                        "seconds": state.worked_s(),
                        "hms": _hms(state.worked_s()),
                        "mode": state.mode,
                    }
                )
                ctype = "application/json"

            headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: %s\r\n"
                "Cache-Control: no-store\r\n"
                "Connection: close\r\n\r\n" % ctype
            )
            writer.write(headers.encode())
            writer.write(body.encode())
            await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    return handle


async def serve(state):
    start_ap()
    await asyncio.start_server(_make_handler(state), "0.0.0.0", 80)
