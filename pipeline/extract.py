import sys, re, json
sys.path.insert(0, sys.argv[1]); import mdom
from mdom import N
domdir = sys.argv[2]
LECS = [  # (강, artifact id, 제목)
 (3,'Bg5WhkJ4idvTrfQ2SsiqUg'),(4,'QwCM4qtdoXZbZmmNXHgoPs'),(5,'RA2YhCJaEDmRsLF8rYT7Ye'),
 (6,'Te72duyPPXPpH3JbBdzwqB'),(7,'Rkpkpn5PbgjzDQnD8PFqR4'),(8,'9oFpLeELxu7Tedc4DHDaPG'),
 (9,'QhYYvWwXV6FfRG8EjZPxjv'),(10,'UG5scDYMFGMJhPZvXsTN5G'),(11,'RDuCiM4CqVqMWcrDs27ZNM'),
 (12,'BJjr84mo2es6mijNkb7a1n'),(13,'7pYSaWXBnfCakdvqfhmrv3'),(14,'7GR1dCizEscQhtDEu2FMAQ'),
 (15,'98yMwHp9oryT324QExrxTz'),(16,'H5qm1FotEVkhLGBKVenH2X'),(17,'8jWAxMXJjfCsMfbHfK8B3h'),
 (18,'FE3gHyKujLcFr5QEb4o5Hs'),(19,'VdxtuaCtYnHR39YTQc8Cdt'),(20,'D4TqtNACat7ZFbx6TpQmST')]
ONLY={int(a) for a in sys.argv[4:]}  # 강 번호를 주면 그 강의만 뽑는다 (예: ... out.json 20)
BLOCK={'div','p','li','td','th','tr','h1','h2','h3','h4','br','ul','ol','summary','details','section','table','pre','dd','dt'}
def txt(n, keep_btn=False, drop=()):
    out=[]
    for k in n.kids:
        if isinstance(k,str): out.append(k)
        elif k.tag in ('script','style','svg') or (k.tag=='button' and not keep_btn) or set(k.cls)&set(drop): continue
        elif k.tag in BLOCK: out.append(' '+txt(k,keep_btn,drop)+' ')
        else: out.append(txt(k,keep_btn,drop))
    return re.sub(r'\s+',' ',''.join(out)).strip()
def body(n):
    return txt(n,drop=('chk','done','bcnt','mark','hint','caret','tw','bd','nt-tp','tt','term','node-label')) if n else ''
def up(n,c):
    while n is not None and c not in n.cls: n=n.parent
    return n
def h2chunks(r):
    out=[]; cur=None
    def walk(n):
        nonlocal cur
        for k in n.kids:
            if isinstance(k,str):
                if cur is not None: cur[1].append(k)
            elif k.tag in ('script','style','svg','button'): continue
            elif k.tag=='h2': cur=[txt(k),[]]; out.append(cur)
            elif k.tag in ('footer',): continue
            else:
                if cur is not None and k.tag in BLOCK: cur[1].append(' ')
                walk(k)
    walk(r)
    return [(t,re.sub(r'\s+',' ',''.join(b)).strip()) for t,b in out]
def has(r,c): return next(r.find(lambda n: c in n.cls),None) is not None
def first(n,pred): return next(n.find(pred),None)
def cl(c): return lambda n: c in n.cls
def extract(r):
    units=[]
    if has(r,'nt-br'):
        for b in r.find(cl('branch')):
            u=first(b,cl('nt-br')); 
            if u: units.append((txt(u),[(txt(t),body(t.parent.parent),txt(first(t.parent,cl('gist'))) if first(t.parent,cl('gist')) else '') for t in b.find(cl('nt-tp'))]))
    if not units and has(r,'bn'):
        for b in r.find(cl('branch')):
            u=first(b,cl('bn')); 
            if u: units.append((txt(u),[(txt(t),body(up(t,'topic'))) for t in b.find(cl('tt'))]))
    if not units and has(r,'br-row'):
        for b in r.find(lambda n: 'br' in n.cls and n.tag=='li'):
            row=first(b,cl('br-row')); tog=first(row,cl('tog')); sub=first(row,cl('bsub'))
            name=re.sub(r'^\d+\s*','',txt(tog,True))+' — '+txt(sub)
            units.append((name,[(txt(t),body(up(t,'tp'))) for t in b.find(cl('tt'))]))
    if not units and has(r,'b-title'):
        for b in r.find(cl('branch')):
            u=first(b,cl('b-title'))
            if u: units.append((txt(u),[(txt(t,drop=('hint',)).rstrip(' ·'),body(t.parent)) for t in b.find(cl('term'))]))
    if not units and has(r,'node-label'):
        for s in r.find(lambda n: 'node' in n.cls and 'section' in n.cls):
            units.append((txt(first(s,cl('node-label'))),[(txt(first(t,cl('node-label'))),body(t)) for t in s.find(lambda n:'node' in n.cls and 'sub' in n.cls)]))
    if not units and has(r,'term') and first(r,lambda n:n.a.get('id')=='tree'):
        tree=first(r,lambda n:n.a.get('id')=='tree')
        for k in [k for k in tree.find(lambda n: n.tag=='summary' or 'branch' in n.cls)]:
            if k.tag=='summary':
                h=first(k,lambda n:n.tag=='h2')
                if h: units.append((txt(h),[]))
            elif units: units[-1][1].extend(((txt(t,drop=('en',))+' ('+txt(first(t,cl('en')))+')') if first(t,cl('en')) else txt(t), body(up(t,'node'))) for t in k.find(cl('term')))
    if not units and has(r,'style-head'):
        units=[(t,[(t,b)]) for t,b in h2chunks(r)]
    if not units:
        units=[('',[(t,b) for t,b in h2chunks(r) if not re.search('퀴즈|연습',t)])]
    return units
res=[]
for lec,aid in LECS:
    if ONLY and lec not in ONLY: continue
    r=mdom.parse(f'{domdir}/{aid}.html')
    title=txt(first(r,lambda n:n.tag=='title'))
    h1=first(r,lambda n:n.tag=='h1')
    res.append({'lec':lec,'id':aid,'title':title,'h1':txt(h1) if h1 else title,'units':extract(r)})
json.dump(res,open(sys.argv[3],'w'),ensure_ascii=False,indent=1)
for x in res: print(x['lec'], '단원',len(x['units']), '주제',sum(len(t) for _,t in x['units']), '본문자수',sum(len(b) for _,ts in x['units'] for tp in ts for b in [tp[1]]), '빈본문',sum(1 for _,ts in x['units'] for tp in ts if len(tp[1])<40))
