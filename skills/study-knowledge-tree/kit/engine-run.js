
/* ---------- 공용 실행부 ---------- */
if (typeof TREE_FIGS !== 'undefined') $$('[data-fig]').forEach(el => { const f = TREE_FIGS[el.dataset.fig]; if (f) el.innerHTML = f(); });
$$('[data-reveal]').forEach(b => b.addEventListener('click', () => {
  const t = document.getElementById(b.dataset.reveal), on = b.getAttribute('aria-expanded') !== 'true';
  b.setAttribute('aria-expanded', String(on)); b.textContent = on ? '정답 숨기기' : '정답 보기'; if (t) t.hidden = !on;
}));
if (typeof DRILLS !== 'undefined' && document.getElementById('drill')) {
const KINDS = Object.keys(DRILLS).concat('mix');
let dkind = store.get(PAGE_KEY + '.dkind', 'mix'); if (!KINDS.includes(dkind)) dkind = 'mix';
let dcur = null, dlocked = false, dstat = { n: 0, ok: 0, streak: 0 };
function renderKinds(){
  $('#drill-kinds').innerHTML = KINDS.map(k => '<button class="btn' + (k === dkind ? ' on' : '') + '" data-k="' + k + '" aria-pressed="' + (k === dkind) + '">' + (k === 'mix' ? '섞어서' : DRILLS[k].label) + '</button>').join('');
}
function newDrill(){
  const ks = Object.keys(DRILLS), k = dkind === 'mix' ? ks[ri(0, ks.length - 1)] : dkind;
  dcur = DRILLS[k].gen(); dcur.kind = k; dlocked = false;
  $('#dq').innerHTML = (dkind === 'mix' ? '<span class="chip">' + DRILLS[k].label + '</span> ' : '') + esc(dcur.q);
  $('#dopts').innerHTML = dcur.opts.map((o, i) => '<button class="opt" data-o="' + i + '"><span class="k">' + (i + 1) + '</span><span>' + esc(o) + '</span></button>').join('');
  $('#dfb').hidden = true;
}
function renderDstat(){
  $('#dstat').innerHTML = dstat.n ? '이번 세션 <b>' + dstat.ok + ' / ' + dstat.n + '</b> · 연속 정답 <b>' + dstat.streak + '</b>' : '';
}
$('#drill-kinds').addEventListener('click', e => {
  const b = e.target.closest('[data-k]'); if (!b) return;
  dkind = b.dataset.k; store.set(PAGE_KEY + '.dkind', dkind); renderKinds(); newDrill();
});
$('#dopts').addEventListener('click', e => {
  const b = e.target.closest('.opt'); if (!b || dlocked) return;
  dlocked = true;
  const pick = dcur.opts[+b.dataset.o], ok = pick === dcur.correct;
  $$('#dopts .opt').forEach(x => {
    const v = dcur.opts[+x.dataset.o];
    x.disabled = true;
    if (v === dcur.correct) x.classList.add('correct'); else if (x === b) x.classList.add('wrong'); else x.classList.add('dim');
  });
  dstat.n++; if (ok) { dstat.ok++; dstat.streak++; } else dstat.streak = 0;
  const fb = $('#dfb');
  fb.innerHTML = '<p class="verdict ' + (ok ? 'ok">정답' : 'bad">오답 · 정답은 ' + esc(dcur.correct)) + '</p><ol class="steps">' + dcur.steps.map(s => '<li>' + esc(s) + '</li>').join('') + '</ol>';
  fb.hidden = false;
  renderDstat();
});
$('#dnext').addEventListener('click', newDrill);
renderKinds(); newDrill(); renderDstat();
}
const TYPES = (typeof QTYPES !== 'undefined') ? QTYPES : ['전체', '암기', '상황', '그림', '계산'];
const QS = Q.map((r, i) => ({ id: 'q' + (i + 1), n: i + 1, type: r[0], topic: r[1], q: r[2], opts: r[3], a: r[4], ex: r[5], fig: r[6] }));
$('#qcount').textContent = QS.length;

let results = store.get(PAGE_KEY + '.results', {});
const qf = { type: '전체', topic: '전체', wrong: false };
let qorder = [], qi = 0, perms = {}, answered = null;
function permFor(q){ if (!perms[q.id]) perms[q.id] = shuffle(q.opts.map((_, i) => i)); return perms[q.id]; }
function renderTypes(){
  $('#qtypes').innerHTML = TYPES.map(t => {
    const n = t === '전체' ? QS.length : QS.filter(q => q.type === t).length;
    return '<button class="btn' + (qf.type === t ? ' on' : '') + '" data-t="' + t + '" aria-pressed="' + (qf.type === t) + '">' + t + ' <span style="font-family:var(--font-mono);font-weight:400">' + n + '</span></button>';
  }).join('');
}
$('#qtopic').innerHTML = '<option value="전체">전체</option>' + Object.keys(TOPIC).map(k => '<option value="' + k + '">' + TOPIC[k] + '</option>').join('');
function buildOrder(shuf){
  qorder = QS.filter(q => (qf.type === '전체' || q.type === qf.type) && (qf.topic === '전체' || q.topic === qf.topic) && (!qf.wrong || results[q.id] === false));
  if (shuf) shuffle(qorder);
  qi = 0; renderQ(); renderDots();
}
function renderScore(){
  const ids = Object.keys(results).filter(k => QS.some(q => q.id === k)), ok = ids.filter(k => results[k]).length;
  $('#qscore').innerHTML = '푼 문제 <b>' + ids.length + '</b> / ' + QS.length + ' · 맞음 <b>' + ok + '</b> · 틀림 <b>' + (ids.length - ok) + '</b>' + (ids.length ? ' · 정답률 <b>' + Math.round(ok / ids.length * 100) + '%</b>' : '');
}
function renderDots(){
  $('#qdots').innerHTML = qorder.map((q, i) => {
    const r = results[q.id];
    return '<button class="dot' + (r === true ? ' ok' : r === false ? ' bad' : '') + (i === qi ? ' cur' : '') + '" data-i="' + i + '" title="#' + q.n + ' ' + q.type + ' · ' + TOPIC[q.topic] + '" aria-label="' + (i + 1) + '번 문제">' + (i + 1) + '</button>';
  }).join('');
}
function renderQ(){
  answered = null;
  const box = $('#qcard');
  if (!qorder.length) { box.innerHTML = '<p class="empty">' + (qf.wrong ? '틀린 문제가 없다. 다른 유형을 풀거나 \'틀린 문제만\'을 끈다.' : '조건에 맞는 문제가 없다.') + '</p>'; return; }
  const q = qorder[qi], p = permFor(q);
  let figHtml = '';
  if (q.fig) { try { figHtml = '<div class="fig-box">' + FIG[q.fig[0]](q.fig[1]) + '</div>'; } catch(e) { figHtml = ''; } }
  box.innerHTML =
    '<div class="qmeta"><span class="chip type">' + q.type + '</span><span class="chip">' + TOPIC[q.topic] + '</span>' + (q.fig ? '<span class="chip fig">그림</span>' : '') + '<span class="qn">' + (qi + 1) + ' / ' + qorder.length + ' · #' + q.n + '</span></div>' +
    '<p class="qtext">' + esc(q.q) + '</p>' + figHtml +
    '<div class="opts">' + p.map((oi, k) => '<button class="opt" data-oi="' + oi + '"><span class="k">' + (k + 1) + '</span><span>' + esc(q.opts[oi]) + '</span></button>').join('') + '</div>' +
    '<div class="fb" hidden></div>' +
    '<div class="qnav"><button class="btn" data-nav="-1"' + (qi === 0 ? ' disabled' : '') + '>← 이전</button><span class="kbd-hint">1–' + p.length + ' 선택 · ← → 이동</span><button class="btn primary" data-nav="1"' + (qi === qorder.length - 1 ? ' disabled' : '') + '>다음 →</button></div>';
}
function answer(oi){
  if (answered !== null || !qorder.length) return;
  const q = qorder[qi], ok = oi === q.a, p = permFor(q);
  answered = oi;
  $$('#qcard .opt').forEach(b => {
    const v = +b.dataset.oi; b.disabled = true;
    if (v === q.a) b.classList.add('correct'); else if (v === oi) b.classList.add('wrong'); else b.classList.add('dim');
  });
  results[q.id] = ok; store.set(PAGE_KEY + '.results', results);
  const fb = $('#qcard .fb');
  fb.innerHTML = '<p class="verdict ' + (ok ? 'ok">정답' : 'bad">오답 · 정답은 ' + (p.indexOf(q.a) + 1) + '번') + '</p><p>' + esc(q.ex) + '</p>';
  fb.hidden = false;
  renderDots(); renderScore();
}
function go(d){ const n = qi + d; if (n < 0 || n >= qorder.length) return; qi = n; renderQ(); renderDots(); }
$('#qtypes').addEventListener('click', e => { const b = e.target.closest('[data-t]'); if (!b) return; qf.type = b.dataset.t; renderTypes(); buildOrder(false); });
$('#qtopic').addEventListener('change', e => { qf.topic = e.target.value; buildOrder(false); });
$('#qwrong').addEventListener('click', e => { qf.wrong = !qf.wrong; e.currentTarget.classList.toggle('on', qf.wrong); e.currentTarget.setAttribute('aria-pressed', String(qf.wrong)); buildOrder(false); });
$('#qshuffle').addEventListener('click', () => { perms = {}; buildOrder(true); });
let resetArmed = null;
$('#qreset').addEventListener('click', e => {
  const b = e.currentTarget;
  if (!resetArmed) { b.textContent = '한 번 더 누르면 지운다'; resetArmed = setTimeout(() => { b.textContent = '기록 지우기'; resetArmed = null; }, 3000); return; }
  clearTimeout(resetArmed); resetArmed = null; b.textContent = '기록 지우기';
  results = {}; store.set(PAGE_KEY + '.results', results); buildOrder(false); renderScore();
});
$('#qdots').addEventListener('click', e => { const b = e.target.closest('[data-i]'); if (!b) return; qi = +b.dataset.i; renderQ(); renderDots(); });
$('#qcard').addEventListener('click', e => {
  const o = e.target.closest('.opt'); if (o) { answer(+o.dataset.oi); return; }
  const n = e.target.closest('[data-nav]'); if (n) go(+n.dataset.nav);
});
document.addEventListener('keydown', e => {
  if ($('#view-quiz').hidden || e.altKey || e.ctrlKey || e.metaKey) return;
  const tag = (e.target.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'select' || tag === 'textarea') return;
  if (/^[1-5]$/.test(e.key) && qorder.length) {
    const p = permFor(qorder[qi]), k = +e.key - 1;
    if (k < p.length) { answer(p[k]); e.preventDefault(); }
  } else if (e.key === 'ArrowRight') { go(1); e.preventDefault(); }
  else if (e.key === 'ArrowLeft') { go(-1); e.preventDefault(); }
});
renderTypes(); buildOrder(false); renderScore();
})();
