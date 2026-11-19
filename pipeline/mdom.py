import re
from html.parser import HTMLParser
VOID={'area','base','br','col','embed','hr','img','input','link','meta','source','track','wbr'}
class N:
    def __init__(s,tag,attrs,parent):
        s.tag=tag; s.a=dict(attrs); s.parent=parent; s.kids=[]
    @property
    def cls(s): return (s.a.get('class') or '').split()
    def text(s):
        out=[]
        for k in s.kids:
            if isinstance(k,str): out.append(k)
            elif k.tag not in ('script','style','button'): out.append(k.text())
        return re.sub(r'\s+',' ',''.join(out)).strip()
    def find(s,pred):
        for k in s.kids:
            if isinstance(k,N):
                if pred(k): yield k
                yield from k.find(pred)
class B(HTMLParser):
    def __init__(s):
        super().__init__(); s.root=N('root',[],None); s.cur=s.root
    def handle_starttag(s,t,a):
        n=N(t,a,s.cur); s.cur.kids.append(n)
        if t not in VOID: s.cur=n
    def handle_startendtag(s,t,a): s.cur.kids.append(N(t,a,s.cur))
    def handle_endtag(s,t):
        x=s.cur
        while x is not None and x.tag!=t: x=x.parent
        if x is not None and x.parent is not None: s.cur=x.parent
    def handle_data(s,d): s.cur.kids.append(d)
def parse(path):
    b=B(); b.feed(open(path,encoding='utf-8').read()); return b.root
def C(c): return lambda n: c in n.cls
def skel(n,depth=0,maxd=6,out=None):
    if out is None: out=[]
    if depth>maxd: return out
    for k in n.kids:
        if isinstance(k,N) and k.tag not in('script','style','svg'):
            t=k.text()
            out.append('  '*depth+f"<{k.tag}.{'.'.join(k.cls)}> {t[:28]}")
            skel(k,depth+1,maxd,out)
    return out
