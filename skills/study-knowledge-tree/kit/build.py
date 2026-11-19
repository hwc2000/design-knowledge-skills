#!/usr/bin/env python3
"""지식트리 페이지 조립기.
사용: python3 build.py --title "로봇 7강 모션 플래닝" --key robot7 --body body.html --content content.js --out page.html
공용 머리(CSS) + 본문 + [엔진 앞부분 + 강의별 스크립트 + 엔진 뒷부분]을 이어 붙인다."""
import argparse, os
here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
for a in ('title', 'key', 'body', 'content', 'out'): ap.add_argument('--' + a, required=True)
o = ap.parse_args()
rd = lambda p: open(p, encoding='utf-8').read()
page = (rd(os.path.join(here, 'base-head.html')).replace('{{TITLE}}', o.title) + rd(o.body) + '\n<script>' +
        rd(os.path.join(here, 'engine-core.js')) + "\nconst PAGE_KEY = '" + o.key + "';\n" + rd(o.content) + '\n' +
        rd(os.path.join(here, 'engine-run.js')) + '</script>\n')
open(o.out, 'w', encoding='utf-8').write(page)
print('built', o.out, len(page.encode()), 'bytes')
