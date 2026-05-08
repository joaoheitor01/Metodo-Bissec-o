"""
Interactive bisection visualization (wave-style) with UI controls.

Generates interactive_bisseccao.html using Plotly (CDN). Features:
- Wave-like stacked bands representing f(x) inside each iteration interval
- Markers for xm with hover tooltips displaying iteration, xm, f(xm), erro
- Slider + Play/Pause, Zoom to Interval, Reset View
- Checkboxes to toggle showing all intervals, baseline f(x) and labels

Open the generated interactive_bisseccao.html in a browser (internet required
to load Plotly CDN). The HTML is standalone.
"""

import importlib
import json
import os
import webbrowser
import time
import threading
import http.server
import socketserver
import contextlib
import io
import sys


def safe_div(a, b):
    return a / b if b else 0.0


def make_wave_data(mod, historico, xs, ys, separation=1.0, amplitude_fraction=0.75):
    """
    Build polygon coordinates and centerlines for a "wave" representation
    for each iteration.
    """
    n = len(historico)
    polys_x = []
    polys_y = []
    center_x = []
    center_y = []
    xm_y = []
    a_list = []
    b_list = []
    fxm_list = []
    err_list = []

    # global metrics
    global_min = min(ys)
    global_max = max(ys)
    global_mid = 0.5 * (global_max + global_min)
    global_hrange = 0.5 * (global_max - global_min)
    if global_hrange == 0:
        global_hrange = 1.0

    offsets = [(n - i) * separation for i in range(1, n + 1)]
    amplitude = separation * amplitude_fraction

    for idx, it in enumerate(historico):
        a = it['a']
        b = it['b']
        xm = it['xm']
        fx = it['fxm']
        err = it['erro']
        a_list.append(a)
        b_list.append(b)
        fxm_list.append(fx)
        err_list.append(err)

        # select xs inside [a,b]
        mask_x = [x for x in xs if x >= a and x <= b]
        if len(mask_x) < 2:
            # fallback: small window around xm
            dx = max(1e-8, 1e-3 * (abs(xm) + 1.0))
            mask_x = [xm - dx, xm + dx]

        mask_y = [mod.f(x) for x in mask_x]

        y_min = min(mask_y)
        y_max = max(mask_y)
        mid = 0.5 * (y_max + y_min)
        hrange = 0.5 * (y_max - y_min)
        if hrange == 0:
            hrange = 1.0

        normalized = [safe_div((yv - mid), hrange) for yv in mask_y]
        off = offsets[idx]

        y_top = [off + (nv + 1.0) * 0.5 * amplitude for nv in normalized]
        y_base = [off] * len(mask_x)

        x_poly = list(mask_x) + list(reversed(mask_x))
        y_poly = list(y_top) + list(reversed(y_base))

        polys_x.append(x_poly)
        polys_y.append(y_poly)

        center = [off + nv * 0.5 * amplitude for nv in normalized]
        center_x.append(mask_x)
        center_y.append(center)

        norm_xm = safe_div((fx - mid), hrange)
        xm_y_val = off + (norm_xm + 1.0) * 0.5 * amplitude
        xm_y.append(xm_y_val)

    return {
        'polys_x': polys_x,
        'polys_y': polys_y,
        'center_x': center_x,
        'center_y': center_y,
        'xm_y': xm_y,
        'offsets': offsets,
        'a_list': a_list,
        'b_list': b_list,
        'fxm_list': fxm_list,
        'err_list': err_list,
    }


def compute_payload(mod, a0, b0, tol, max_iter, n_points=700):
    """Run the bisseccao function (silencing its stdout) and build the plot payload."""
    # suppress output from mod.bisseccao which prints iteration tables
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            raiz, historico = mod.bisseccao(a0, b0, tol, max_iter)
    except Exception:
        # re-raise so caller can observe the failure
        raise

    if not historico:
        return None, raiz, historico

    xs = [a0 + i * (b0 - a0) / n_points for i in range(n_points + 1)]
    ys = [mod.f(x) for x in xs]

    wave = make_wave_data(mod, historico, xs, ys, separation=1.0, amplitude_fraction=0.8)

    payload = {
        'polys_x': wave['polys_x'],
        'polys_y': wave['polys_y'],
        'center_x': wave['center_x'],
        'center_y': wave['center_y'],
        'xm_x': [it['xm'] for it in historico],
        'xm_y': wave['xm_y'],
        'a_list': wave['a_list'],
        'b_list': wave['b_list'],
        'fxm_list': wave['fxm_list'],
        'err_list': wave['err_list'],
        'offsets': wave['offsets'],
        'xs': xs,
        'ys': ys,
        'raiz': raiz,
        'ts': time.time(),
    }

    return payload, raiz, historico


def write_payload(payload, path='interactive_payload.json'):
    """Write payload JSON atomically to avoid partial reads from the browser."""
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    os.replace(tmp, path)
    print('Wrote payload:', path)


def write_html(out='interactive_bisseccao.html', payload_file='interactive_payload.json'):
    """Write an HTML file that fetches the payload JSON and updates the Plotly plot."""
    html_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <title>Bisseccao Interativa - Waves</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 10px; }
    .controls { display:flex; gap:12px; align-items:center; margin-bottom:8px; flex-wrap:wrap; }
    .info { font-size:13px; padding:8px; border:1px solid #ddd; background:#fafafa; }
  </style>
</head>
<body>
  <h3>Metodo da Bisseccao - Visualizacao em Ondas</h3>
  <div class="controls">
    <label>Iteracao: <input id="iter_slider" type="range" min="1" max="1" value="1" step="1" style="width:320px"></label>
    <button id="edit_eq_btn">Editar equacao</button>
    <button id="play_btn">Play</button>
    <button id="zoom_btn">Zoom to Interval</button>
    <button id="reset_btn">Reset View</button>
    <label><input id="show_all" type="checkbox" checked> Mostrar todas</label>
    <label><input id="show_baseline" type="checkbox" checked> Mostrar f(x)</label>
    <label><input id="show_labels" type="checkbox"> Mostrar rotulos</label>
  </div>
  <div class="info" id="info">Pronto</div>
  <div id="plot" style="width:100%; height:720px;"></div>
  <script>
    const DATA_URL = '__PAYLOAD_FILE__';
    let payload = null;
    let plotReady = false;
    let pollInterval = 2000;
    // globals for controls (assigned in attachControls)
    let slider, showAll, showBaseline, showLabels, playBtn, zoomBtn, resetBtn;

    async function fetchPayload() {
      const resp = await fetch(DATA_URL + '?ts=' + Date.now(), {cache: 'no-store'});
      if (!resp.ok) throw new Error('Fetch failed: ' + resp.status);
      return await resp.json();
    }

    function hslToRgb(h, s, l) { s=Math.max(0,Math.min(1,s)); l=Math.max(0,Math.min(1,l)); const a=s*Math.min(l,1-l); const f=(n)=>{const k=(n+h/30)%12; const color = l - a*Math.max(-1,Math.min(k-3,Math.min(9-k,1))); return Math.round(255*color);}; return [f(0), f(8), f(4)]; }
    function rgbaFromHsl(h, s, l, a){const rgb=hslToRgb(h,s,l); return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`; }

    function buildTraces(p) {
      const n = p.polys_x.length;
      const traces = [];
      for (let i=0;i<n;i++){
        const hue = 220 - (i * 140 / Math.max(1, n-1));
        const fillColor = rgbaFromHsl(hue/1, 0.7, 0.6, 0.28);
        const lineColor = rgbaFromHsl(hue/1, 0.7, 0.45, 1.0);
        traces.push({ x: p.polys_x[i], y: p.polys_y[i], mode: "none", fill: "toself", fillcolor: fillColor, hoverinfo: "text", text: Array(p.polys_x[i].length).fill(`Iter ${i+1} [a=${p.a_list[i].toFixed(8)}, b=${p.b_list[i].toFixed(8)}]`), opacity: 0.18, name: `interval ${i+1}` });
        traces.push({ x: p.center_x[i], y: p.center_y[i], mode: "lines", line: {color: lineColor, width: 1.0}, hoverinfo: "none", opacity: 0.9, showlegend: false });
      }
      const iters = Array.from({length:n}, (_,i)=>i+1);
      traces.push({ x: p.xm_x, y: p.xm_y, mode: "markers", marker: {size: Array(n).fill(8), color: "#d81b60"}, text: iters.map(i=>`Iter ${i}`), hovertemplate: "Iter %{text}<br>xm: %{x:.8f}<br>f(xm): %{y:.2e}<extra></extra>", name: "xm" });

      const xs = p.xs; const ys = p.ys; const gmin = Math.min(...ys); const gmax = Math.max(...ys); const gmid = (gmax+gmin)/2; const gr = (gmax-gmin)/2 || 1.0; const baselineOff=-0.9; const baselineAmp=0.8; const baselineY = ys.map(v => baselineOff + ((v - gmid)/gr) * 0.5 * baselineAmp);
      traces.push({x: xs, y: baselineY, mode: "lines", line: {color: "#111", width:1.2}, name: "f(x)", visible: true});

      return traces;
    }

    function makeLayout() {
      return { title: "Bisseccao - Ondas por Iteracao", xaxis: {title: "x"}, yaxis: {title: "Iteracao (empilhada)", autorange: "reversed", showgrid: false, zeroline:false}, hovermode: "closest", margin: {l:80, r:40, t:60, b:60}, showlegend: false, height: 720 };
    }

    function updateInfo(i){ const idx=i-1; const info = document.getElementById("info"); info.innerHTML = `<b>Iter ${i}</b> &nbsp; a=${payload.a_list[idx].toFixed(10)} &nbsp; b=${payload.b_list[idx].toFixed(10)} &nbsp; xm=${payload.xm_x[idx].toFixed(12)} &nbsp; f(xm)=${payload.fxm_list[idx].toExponential(2)} &nbsp; erro=${payload.err_list[idx].toExponential(2)}`; }

    function setIteration(i, zoom){
      const idx = i-1;
      const n = payload.polys_x.length;
      for(let j=0;j<n;j++){
        const polyIdx = 2*j;
        const centerIdx = 2*j+1;
        const isSel = (j===idx);
        const polyOpacity = showAll.checked ? (isSel?0.92:0.12) : (isSel?0.92:0);
        Plotly.restyle("plot", {"opacity":[polyOpacity]}, [polyIdx]);
        Plotly.restyle("plot", {"line.width":[isSel?2.2:1.0]}, [centerIdx]);
      }
      const sizes = Array(n).fill(8); sizes[idx]=14;
      const xmTraceIndex = 2*n;
      Plotly.restyle("plot", {"marker.size":[sizes]}, [xmTraceIndex]);
      const baselineIndex = xmTraceIndex + 1;
      Plotly.restyle("plot", {"visible": showBaseline.checked? true: 'legendonly'}, [baselineIndex]);
      const mode = showLabels.checked? 'markers+text' : 'markers';
      Plotly.restyle("plot", {"mode":[mode]}, [xmTraceIndex]);
      if(zoom){
        const a = payload.a_list[idx];
        const b = payload.b_list[idx];
        const margin = Math.max(1e-6, (b-a) * 0.25);
        Plotly.relayout("plot", {"xaxis.range":[a - margin, b + margin]});
        const off = payload.offsets[idx];
        const amp = 0.9;
        Plotly.relayout("plot", {"yaxis.range":[off - amp, off + amp * 1.6]});
      }
      updateInfo(i);
    }

    let playInterval = null;

    function attachControls(){
      slider = document.getElementById("iter_slider");
      const infoDiv = document.getElementById("info");
      showAll = document.getElementById("show_all");
      showBaseline = document.getElementById("show_baseline");
      showLabels = document.getElementById("show_labels");
      playBtn = document.getElementById("play_btn");
      zoomBtn = document.getElementById("zoom_btn");
      resetBtn = document.getElementById("reset_btn");

      slider.max = payload.polys_x.length;
      slider.value = Math.min(slider.value || 1, slider.max);
      slider.addEventListener("input", function(){ setIteration(parseInt(this.value), false); });
      showAll.addEventListener("change", function(){ setIteration(parseInt(slider.value), false); });
      showBaseline.addEventListener("change", function(){ setIteration(parseInt(slider.value), false); });
      showLabels.addEventListener("change", function(){ setIteration(parseInt(slider.value), false); });
      playBtn.addEventListener("click", function(){
        if(playInterval){ clearInterval(playInterval); playInterval=null; playBtn.textContent="Play"; return; }
        playBtn.textContent="Pause";
        let v = parseInt(slider.value);
        playInterval = setInterval(()=>{ v++; if(v>payload.polys_x.length){ clearInterval(playInterval); playInterval=null; playBtn.textContent="Play"; return;} slider.value=v; setIteration(v,true); }, 700);
      });
      zoomBtn.addEventListener("click", function(){ setIteration(parseInt(slider.value), true); });
      resetBtn.addEventListener("click", function(){ Plotly.relayout("plot", {"xaxis.autorange": true, "yaxis.autorange": true}); });
    }

    function initPlot(p){
      payload = p;
      const traces = buildTraces(p);
      const layout = makeLayout();
      Plotly.newPlot("plot", traces, layout, {responsive: true});
      attachControls();
      setIteration(1, false);
      plotReady = true;
    }

    async function updatePlot(newPayload){
      try{
        const gd = document.getElementById('plot');
        const xRange = gd.layout && gd.layout.xaxis && gd.layout.xaxis.range ? gd.layout.xaxis.range.slice() : null;
        const yRange = gd.layout && gd.layout.yaxis && gd.layout.yaxis.range ? gd.layout.yaxis.range.slice() : null;
        payload = newPayload;
        const traces = buildTraces(newPayload);
        const layout = makeLayout();
        await Plotly.react('plot', traces, layout);
        if(xRange) Plotly.relayout('plot', {'xaxis.range': xRange});
        if(yRange) Plotly.relayout('plot', {'yaxis.range': yRange});
        // update controls
        const slider = document.getElementById("iter_slider");
        const val = Math.min(parseInt(slider.value || 1), payload.polys_x.length);
        slider.max = payload.polys_x.length;
        slider.value = val;
        setIteration(val, false);
      }catch(e){
        console.error('updatePlot error', e);
      }
    }

    async function loadAndWatch(){
      try{
        const p = await fetchPayload();
        await initPlot(p);
      }catch(e){
        document.getElementById('info').textContent = 'Erro ao carregar payload: ' + e;
        console.error(e);
        return;
      }
      // poll for updates
      setInterval(async ()=>{
        try{
          const newP = await fetchPayload();
          if(!payload || newP.ts !== payload.ts){
            await updatePlot(newP);
          }
        }catch(e){
          console.error('poll error', e);
        }
      }, pollInterval);
    }

    document.getElementById('edit_eq_btn').addEventListener('click', function(){ document.getElementById('eq_modal').style.display='block'; });
    window.addEventListener('load', function(){ loadAndWatch(); });
  </script>
  <div id="eq_modal" style="display:none; position:fixed; left:50%; top:10%; transform:translate(-50%,0); background:#fff; border:1px solid #ccc; padding:12px; z-index:9999; box-shadow:0 2px 10px rgba(0,0,0,0.2); width:520px;">
    <h4>Editar equacao f(x)</h4>
    <div style="font-size:12px; color:#444; margin-bottom:6px">Digite uma expressão Python em x, por exemplo: <code>x**3 - x - 2</code> ou <code>sin(x) - 0.5</code></div>
    <textarea id="eq_input" style="width:100%; height:120px; font-family:monospace;"></textarea>
    <div style="margin-top:8px; display:flex; gap:8px; justify-content:flex-end;">
      <button id="eq_send_btn">Enviar</button>
      <button id="eq_close_btn">Fechar</button>
    </div>
  </div>
  <script>
    document.getElementById('eq_close_btn').addEventListener('click', function(){ document.getElementById('eq_modal').style.display='none'; });
    document.getElementById('eq_send_btn').addEventListener('click', async function(){
      const expr = document.getElementById('eq_input').value.trim();
      if(!expr){ alert('Equacao vazia'); return; }
      try{
        const resp = await fetch('/set_equation', {method:'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({expr})});
        const j = await resp.json();
        if(j.status === 'ok'){
          alert('Equacao enviada com sucesso. Aguarde o recálculo.');
          document.getElementById('eq_modal').style.display='none';
        } else {
          alert('Erro: ' + (j.error || 'unknown'));
        }
      }catch(e){ alert('Falha ao enviar: ' + e); }
    });
  </script>
  </body>
  </html>
  """

    html = html_template.replace('__PAYLOAD_FILE__', payload_file)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Wrote html:', out)


def start_http_server(host='127.0.0.1', port=8000):
    # Custom handler to accept POST /set_equation
    base_dir = os.getcwd()

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_POST(self):
            if self.path != '/set_equation':
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode('utf-8'))
                expr = data.get('expr', '').strip()
                if not expr:
                    raise ValueError('Empty expression')
                # Write user_func.py atomically
                user_path = os.path.join(base_dir, 'user_func.py')
                tmp = user_path + '.tmp'
                content = 'import math\nfrom math import *\n\ndef f(x):\n    return ' + expr + '\n'
                with open(tmp, 'w', encoding='utf-8') as f:
                    f.write(content)
                os.replace(tmp, user_path)
                # reply
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'error': str(e)}).encode('utf-8'))

    class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    try:
        server = ThreadingServer((host, port), CustomHandler)
    except OSError:
        server = ThreadingServer((host, 0), CustomHandler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_port = server.server_address[1]
    print(f"Serving HTTP at http://{host}:{actual_port}/")
    return server, actual_port


def watch_and_serve(mod, a0, b0, tol, max_iter, host='127.0.0.1', port=8000):
    # generate initial payload + html
    try:
        payload, raiz, historico = compute_payload(mod, a0, b0, tol, max_iter)
    except Exception as e:
        print('Error running bisseccao:', e)
        return

    if not payload:
        print('Historico vazio - nothing to plot')
        return

    write_payload(payload)
    write_html(out='interactive_bisseccao.html', payload_file='interactive_payload.json')

    server, actual_port = start_http_server(host, port)
    try:
        webbrowser.open(f'http://{host}:{actual_port}/interactive_bisseccao.html')
    except Exception:
        pass

    mod_path = getattr(mod, '__file__', 'bisseccao.py')
    user_func_path = os.path.join(os.path.dirname(mod_path), 'user_func.py')
    try:
        last_mtime_mod = os.path.getmtime(mod_path)
    except Exception:
        last_mtime_mod = None
    try:
        last_mtime_user = os.path.getmtime(user_func_path)
    except Exception:
        last_mtime_user = None

    print('Watching', mod_path, 'and', user_func_path, 'for changes. Press Ctrl-C to stop.')
    try:
        while True:
            time.sleep(1.0)
            changed = False
            try:
                mtime_mod = os.path.getmtime(mod_path)
            except Exception:
                mtime_mod = None
            try:
                mtime_user = os.path.getmtime(user_func_path)
            except Exception:
                mtime_user = None

            if last_mtime_mod is None or (mtime_mod is not None and mtime_mod != last_mtime_mod):
                last_mtime_mod = mtime_mod
                changed = True
                print('Change detected in', mod_path)

            if last_mtime_user is None or (mtime_user is not None and mtime_user != last_mtime_user):
                last_mtime_user = mtime_user
                changed = True
                print('Change detected in', user_func_path)

            if not changed:
                continue

            print('Reloading modules and regenerating payload')
            # If user_func is present in sys.modules, reload it first so bisseccao
            # will pick up the new function when reloaded.
            try:
                if 'user_func' in sys.modules:
                    try:
                        importlib.reload(sys.modules['user_func'])
                    except Exception as e:
                        print('Failed to reload user_func:', e)
                mod = importlib.reload(mod)
            except Exception as e:
                print('Failed to reload module:', e)
                continue

            try:
                payload, raiz, historico = compute_payload(mod, a0, b0, tol, max_iter)
                if payload:
                    write_payload(payload)
                else:
                    print('Historico empty after reload - not updating payload')
            except Exception as e:
                print('Error generating payload after reload:', e)
    except KeyboardInterrupt:
        print('\nShutting down server...')
        try:
            server.shutdown()
        except Exception:
            pass


def main():
    # Start the HTTP server, write initial payload and html, and watch bisseccao for changes.
    mod = importlib.import_module('bisseccao')
    a0 = 1.0
    b0 = 2.0
    tol = 1e-6
    max_iter = 50
    watch_and_serve(mod, a0, b0, tol, max_iter)


if __name__ == '__main__':
    main()
