#!/usr/bin/env python3
"""조립한 페이지 자동 점검: 스크립트 문법, 문제은행 전 문항(그림·정답 1개), 드릴 유형별 200회(보기 중복·정답 1개), 트리 그림, JS 오류.
사용: python3 test.py page.html   (문제가 있으면 PROBLEM 줄이 나오고 종료 코드 1)"""
import sys, os, re, glob, html, shutil, subprocess, tempfile
src = open(sys.argv[1], encoding='utf-8').read()
bad = 0
node = shutil.which('node')
scripts = re.findall(r'<script>(.*?)</script>', src, re.S)
if node and scripts:
    fd, js = tempfile.mkstemp(suffix='.js'); os.write(fd, scripts[-1].encode()); os.close(fd)
    r = subprocess.run([node, '--check', js], capture_output=True, text=True)
    if r.returncode: print('PROBLEM 문법 오류:', r.stderr.strip()[:800]); sys.exit(1)
    print('문법 OK')
cands = glob.glob(os.path.expanduser('~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome')) + [shutil.which(x) for x in ('chromium', 'chromium-browser', 'google-chrome') if shutil.which(x)]
if not cands: print('브라우저가 없어 문법 검사만 했다'); sys.exit(0)
PRE = "<script>window.__errs=[];window.addEventListener('error',e=>{window.__errs.push(e.message+' @'+e.lineno)});</script>"
POST = r"""<script>
setTimeout(() => { const out = [];
  try {
    document.querySelector('[data-view="quiz"]').click();
    const n = +document.getElementById('qcount').textContent; let figs = 0;
    for (let i = 0; i < n; i++) {
      document.querySelectorAll('#qdots .dot')[i].click();
      const card = document.getElementById('qcard');
      if (card.querySelector('.chip.fig')) { if (card.querySelector('svg')) figs++; else out.push('PROBLEM 문제 '+(i+1)+' 그림 없음'); }
      card.querySelectorAll('.opt')[0].click();
      if (card.querySelectorAll('.opt.correct').length !== 1) out.push('PROBLEM 문제 '+(i+1)+' 정답 표시 이상');
    }
    out.push('문제은행 '+n+'문항 · 그림 '+figs+' · 유형 '+[...document.querySelectorAll('#qtypes .btn')].map(b=>b.textContent).join(' / '));
    if (document.getElementById('drill')) {
      document.querySelector('[data-view="calc"]').click();
      for (const k of [...document.querySelectorAll('#drill-kinds [data-k]')].map(b=>b.dataset.k)) {
        document.querySelector('#drill-kinds [data-k="'+k+'"]').click();
        for (let j = 0; j < 200; j++) {
          const opts = [...document.querySelectorAll('#dopts .opt')], t = opts.map(o=>o.textContent.slice(1));
          if (opts.length < 2) out.push('PROBLEM 드릴 '+k+' 보기 부족: '+document.getElementById('dq').textContent);
          if (new Set(t).size !== t.length) out.push('PROBLEM 드릴 '+k+' 보기 중복: '+t.join(' | '));
          opts[0].click();
          if (document.querySelectorAll('#dopts .opt.correct').length !== 1) out.push('PROBLEM 드릴 '+k+' 정답 없음: '+document.getElementById('dq').textContent);
          if (j === 0) out.push('예시 '+k+': '+document.getElementById('dq').textContent.slice(0,120));
          document.getElementById('dnext').click();
        }
      }
    }
    const miss = [...document.querySelectorAll('[data-fig]')].filter(e => !e.querySelector('svg')).map(e => e.dataset.fig);
    if (miss.length) out.push('PROBLEM 트리 그림 안 그려짐: '+miss.join(', '));
    out.push('트리 그림 '+document.querySelectorAll('[data-fig] svg').length+'개 · 트리 항목 '+document.querySelectorAll('#tree details.topic').length+'개');
  } catch(e) { out.push('PROBLEM 실행 오류 '+e.message); }
  if (window.__errs.length) out.push('PROBLEM JS 오류 '+JSON.stringify(window.__errs));
  const pre = document.createElement('pre'); pre.id='__out'; pre.textContent = out.join('\n'); document.body.appendChild(pre);
}, 300);
</script>"""
d = tempfile.mkdtemp(); p = os.path.join(d, 'test.html')
open(p, 'w', encoding='utf-8').write(PRE + src + POST)
r = subprocess.run([cands[0], '--headless=new', '--no-sandbox', '--disable-gpu', '--virtual-time-budget=8000', '--dump-dom', 'file://' + p], capture_output=True, text=True, timeout=180)
m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
txt = html.unescape(m.group(1)) if m else 'PROBLEM 결과를 못 읽음'
print(txt)
sys.exit(1 if 'PROBLEM' in txt else 0)
