
(function(){
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const store = {
  get(k, d){ try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch(e){ return d; } },
  set(k, v){ try { localStorage.setItem(k, JSON.stringify(v)); } catch(e){} }
};
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const ri = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const fmtN = x => Number(x).toLocaleString('ko-KR');
const sup = n => String(n).split('').map(c => c === '-' ? '⁻' : '⁰¹²³⁴⁵⁶⁷⁸⁹'[+c]).join('');

/* ---------- tabs ---------- */
const VIEWS = ['tree', 'compare', 'calc', 'quiz'];
function show(v){
  if (!VIEWS.includes(v)) v = 'tree';
  VIEWS.forEach(x => { $('#view-' + x).hidden = x !== v; });
  $$('.tab').forEach(t => t.setAttribute('aria-selected', String(t.dataset.view === v)));
}
$$('.tab').forEach(t => t.addEventListener('click', () => {
  const v = t.dataset.view;
  show(v);
  try { if (location.hash.slice(1) !== v) location.hash = v; } catch(e){}
  const head = $('.masthead');
  if (window.scrollY > head.offsetHeight) window.scrollTo({ top: head.offsetHeight });
}));
window.addEventListener('hashchange', () => show(location.hash.slice(1)));
show(location.hash.slice(1));

/* ---------- tree buttons ---------- */
$('#t-open').addEventListener('click', () => $$('#tree details').forEach(d => d.open = true));
$('#t-close').addEventListener('click', () => $$('#tree details.topic').forEach(d => d.open = false));
$('#t-star').addEventListener('click', () => $$('#tree details.topic').forEach(d => { d.open = !!d.querySelector(':scope > summary .bd.star'); }));

/* ---------- SVG helpers ---------- */
const T = (x, y, s, c, a) => '<text class="' + (c || 'fx-t') + '" x="' + x + '" y="' + y + '"' + (a ? ' text-anchor="' + a + '"' : '') + '>' + esc(s) + '</text>';
const R = (x, y, w, h, c, rx) => '<rect class="' + c + '" x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + (rx == null ? 6 : rx) + '"/>';
const L = (x1, y1, x2, y2, c, m) => '<line class="' + c + '" x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '"' + (m ? ' marker-end="url(#' + m + ')"' : '') + '/>';
const Ci = (cx, cy, r, c) => '<circle class="' + c + '" cx="' + cx + '" cy="' + cy + '" r="' + r + '"/>';
const P = (d, c, m) => '<path class="' + c + '" d="' + d + '"' + (m ? ' marker-end="url(#' + m + ')"' : '') + '/>';
const f1 = v => (+v).toFixed(1);
function svg(w, h, inner, label){
  return '<svg class="fig" viewBox="0 0 ' + w + ' ' + h + '" style="max-width:' + w + 'px;min-width:' + Math.min(w, 480) + 'px" role="img" aria-label="' + esc(label || '그림') + '">' + inner + '</svg>';
}
const FIG = {};
/* 보기 만들기: 정답 + 오답 후보에서 중복 없이 n개 뽑아 섞는다 */
function opts(correct, distract, n){
  const out = [correct];
  for (const d of distract) { if (out.length >= (n || 4)) break; if (!out.includes(d)) out.push(d); }
  return shuffle(out);
}
