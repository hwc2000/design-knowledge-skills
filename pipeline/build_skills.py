"""지식트리 추출 결과(JSON)를 설계 질문 스킬의 references 로 나눠 넣는다.

사용:
  python3 -I build_skills.py <추출.json> <과목이름> [스킬폴더=~/.claude/skills]
  python3 -I build_skills.py --links-only [스킬폴더]     # 보조 태그 링크와 목록만 다시 만든다

- 한 과목의 자료는 각 스킬의 references/<과목이름>/ 아래에만 쓴다.
  JSON 에 들어 있는 강의의 파일(출처 아티팩트 id 로 찾음)만 지우고 다시 쓴다. 다른 강의·다른 과목 파일은 그대로 둔다.
- 강의 번호(lec)는 선택이다. 있으면 파일 이름 앞에 NN강- 을 붙이고, 없으면 제목만 쓴다.
- 주제 본문은 주 태그 스킬 한 곳에만 둔다. 보조 태그(tag.SEE)는 다른 스킬의 references/관련-주제.md 에 한 줄 링크로만 남긴다.
  링크는 references 전체를 훑어 매번 새로 만들므로 본문과 어긋나지 않는다.
- SKILL.md 의 <!-- INDEX --> ~ <!-- /INDEX --> 구간은 references 폴더 전체(모든 과목)를 훑어 다시 만든다.
- 태그 → 스킬 대응은 SKILL_OF 에서 정한다. 새 설계 질문 스킬을 만들면 여기에 추가한다.
"""
import json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tag as tagger

SKILL_OF = {
    '구조': 'design-structure', '통신': 'design-communication', '성능': 'design-performance',
    '분할': 'design-partitioning', '찾기': 'design-partitioning', '일관성': 'design-consistency',
    '복제': 'design-replication', '충돌': 'design-conflict-ordering', '순서': 'design-conflict-ordering',
    '조정': 'design-coordination', '장애': 'design-failure',
}

def slug(s):
    s = re.sub(r'^(분산(처리)?\s*\d+강\s*|\d+강\s*)', '', s)
    s = re.sub(r'(지식트리|시험노트|노트)$', '', s).strip()
    return re.sub(r'[^\w가-힣]+', '-', s).strip('-')[:30] or 'notes'

def clean(t):
    return re.sub(r'\s*p\.\d[\d–·, ]*$', '', re.sub(r' · p\.\d[\d–]*$', '', t)).strip()

DECIDE = re.compile(r'선택|고르|기준|체크리스트|트레이드오프|vs|VS|비교|판단|언제|고려사항|결정|대가|장단점|장점과|약점|한계|문제:|오해|함정|실무')
EXAM = [  # 시험 말투 → 설계 말투. 지워지는 건 시험에만 의미 있는 표현뿐
    (r'시험에서는\s*', '흔한 오해: '), (r'시험 포인트\s*', '핵심: '), (r'출제', ''),
    (r'서술형에 그대로 쓸 수 있는 ', ''), (r'p\.\d[\d–·,]*\s?', ' '), (r'외울 ?것|외운 ?가지|암기', ''),
]

def unexam(t):
    for a, b in EXAM:
        t = re.sub(a, b, t)
    return re.sub(r'\s{2,}', ' ', t).strip()

def first_sentence(t, n=110):
    t = unexam(t)
    m = re.search(r'^(.{15,%d}?(다\.|다 |\. |→))' % n, t)
    return (m.group(1) if m else t[:n]).strip() + ('' if m or len(t) <= n else '…')

def compact(title, body, gist):
    if DECIDE.search(title):
        return unexam(body)
    return unexam(gist) if gist else first_sentence(body)

def build(data, subject, root):
    files = {}  # (skill, filename) -> lines
    for x in data:
        lec, url = x.get('lec'), 'https://claude.ai/artifact/' + x['id']
        fname = (f"{lec:02d}강-" if lec else '') + f"{slug(x.get('h1') or x['title'])}.md"
        for ui, (unit, topics) in enumerate(x['units']):
            for tp in topics:
                title, body = tp[0], tp[1]
                gist = tp[2] if len(tp) > 2 else ''
                title = clean(title)
                skill = SKILL_OF.get(tagger.tag(x['tags'][ui], title))
                if not skill:
                    continue
                key = (skill, fname)
                if key not in files:
                    files[key] = [f"# {subject}" + (f" {lec}강" if lec else '') + f" · {x['title']}", '',
                                  f"출처 지식트리: {url} (자세한 설명·그림은 여기)", '',
                                  '> 개념은 한 줄 요지만 둔다. 판단·비교 주제만 본문을 남긴다. 근거로 쓰되 정답으로 쓰지 않는다.', '']
                head = f"### {title}" + (f"  〔{unit}〕" if unit and unit != title else '')
                files[key] += [head, compact(title, body, gist), '']
    ids = ['claude.ai/artifact/' + x['id'] + ' ' for x in data]
    for sk in set(SKILL_OF.values()):  # 이번에 넣는 강의의 옛 파일만 지운다 (머리말의 출처 id 로 찾음)
        d = os.path.join(root, sk, 'references', subject)
        if os.path.isdir(d):
            for fn in os.listdir(d):
                p = os.path.join(d, fn)
                if any(i in open(p).read(400) for i in ids):
                    os.remove(p)
    for (skill, fname), lines in files.items():
        d = os.path.join(root, skill, 'references', subject)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, fname), 'w') as f:
            f.write('\n'.join(lines))
    return sorted({s for s, _ in files})

LINKS = '관련-주제.md'
MAX_SEE = 2

def links(root):
    """모든 스킬의 references 를 훑어, 보조 태그가 가리키는 스킬마다 관련-주제.md 를 새로 쓴다."""
    skills = sorted(set(SKILL_OF.values()))
    inv = {sk: [] for sk in skills}
    for sk in skills:
        ref = os.path.join(root, sk, 'references')
        if not os.path.isdir(ref):
            continue
        for subj in sorted(os.listdir(ref)):
            sd = os.path.join(ref, subj)
            if not os.path.isdir(sd):
                continue
            for fn in sorted(os.listdir(sd)):
                lines = open(os.path.join(sd, fn)).read().split('\n')
                for i, l in enumerate(lines):
                    if not l.startswith('### '):
                        continue
                    title = re.sub(r'\s+〔.*〕$', '', l[4:]).strip()
                    gist = next((x for x in lines[i + 1:i + 3] if x.strip() and not x.startswith('###')), '')
                    gist = gist[:90] + ('…' if len(gist) > 90 else '')
                    targets = []
                    for tg in tagger.extras(title):
                        t = SKILL_OF.get(tg)
                        if t and t != sk and t not in targets:
                            targets.append(t)
                    for t in targets[:MAX_SEE]:
                        lab = (re.match(r'\d+강', fn) or re.match(r'.{1,20}', fn[:-3])).group(0)
                        inv[t].append(f"- {title} · {subj} {lab} → `~/.claude/skills/{sk}/references/{subj}/{fn}` — {gist}")
    for sk in skills:
        p = os.path.join(root, sk, 'references', LINKS)
        if not inv[sk]:
            if os.path.exists(p):
                os.remove(p)
            continue
        head = ['# 다른 스킬에 있는 관련 주제', '',
                '> 자동 생성(build_skills.py · tag.SEE). 본문은 화살표 뒤 파일에 있다.',
                '> 필요한 줄을 Grep 으로 찾고, 그 파일에서 `### 제목` 을 Grep 해 읽는다. 여기 적힌 요지만으로 결론 내지 않는다.', '']
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w').write('\n'.join(head + inv[sk]) + '\n')
    return {sk: len(v) for sk, v in inv.items()}

def reindex(root, skill):
    p = os.path.join(root, skill, 'SKILL.md')
    ref = os.path.join(root, skill, 'references')
    out = []
    for subj in sorted(os.listdir(ref)) if os.path.isdir(ref) else []:
        sd = os.path.join(ref, subj)
        if not os.path.isdir(sd):
            continue
        out.append(f"**{subj}**")
        for fn in sorted(os.listdir(sd)):
            n = sum(1 for l in open(os.path.join(sd, fn)) if l.startswith('### '))
            out.append(f"- `references/{subj}/{fn}` (주제 {n}개)")
        out.append('')
    lp = os.path.join(ref, LINKS)
    if os.path.exists(lp):
        n = sum(1 for l in open(lp) if l.startswith('- '))
        out += ['**다른 스킬의 관련 주제** (보조 태그)',
                f"- `references/{LINKS}` (주제 {n}개) — 이 스킬 질문에 걸치는 다른 스킬의 주제 링크. 질문이 이 스킬 범위를 넘으면 여기서 찾는다.", '']
    s = open(p).read()
    s = re.sub(r'<!-- INDEX -->.*<!-- /INDEX -->',
               '<!-- INDEX -->\n' + '\n'.join(out).rstrip() + '\n<!-- /INDEX -->', s, flags=re.S)
    open(p, 'w').write(s)
    return len(out)

if __name__ == '__main__':
    if sys.argv[1] == '--links-only':
        root = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else '~/.claude/skills')
        print('링크:', links(root))
        for sk in sorted(set(SKILL_OF.values())):
            if os.path.exists(os.path.join(root, sk, 'SKILL.md')):
                reindex(root, sk)
        sys.exit()
    src, subject = sys.argv[1], sys.argv[2]
    root = os.path.expanduser(sys.argv[3] if len(sys.argv) > 3 else '~/.claude/skills')
    skills = build(json.load(open(src)), subject, root)
    print('링크:', links(root))
    for sk in sorted(set(SKILL_OF.values())):
        if os.path.exists(os.path.join(root, sk, 'SKILL.md')):
            reindex(root, sk)
    for sk in skills:
        d = os.path.join(root, sk, 'references', subject)
        size = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d))
        print(f"{sk}: 파일 {len(os.listdir(d))}개, {size//1024}KB")
