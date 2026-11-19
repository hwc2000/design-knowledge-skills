# 지식트리 부품 키트

페이지 = 공용 부품(매번 같음) + 강의별 내용(매번 새로 씀). 강의마다 **두 파일만** 쓴다.

| 파일 | 하는 일 | 강의마다 |
|---|---|---|
| `base-head.html` | 페이지 옷: 색·글꼴·간격·다크모드·카드·표·문제 카드 모양(CSS), 화살표 정의 | 그대로 |
| `engine-core.js` | 도우미: `$` `$$` 선택, `store`(localStorage), `esc`, `ri` 난수, `shuffle`, `fmtN`, `sup`, 탭 전환, 트리 펼치기 버튼, SVG 도우미 `T R L Ci P f1 svg`, `opts`, 빈 `FIG` | 그대로 |
| `engine-run.js` | 실행부: `[data-fig]`에 `TREE_FIGS` 그림 채우기, `data-reveal` 정답 펼치기, 드릴 엔진, 문제은행 엔진 | 그대로 |
| `body-skeleton.html` | 본문 뼈대(탭 4개, 트리 마크업, 박스 4종, 도구, 드릴·문제은행 자리). 복사해서 `body.html`로 채운다 | **새로 씀** |
| `content.js` (직접 작성) | 그림 함수 `FIG.x = s => svg(...)`, `TREE_FIGS`, 도구 코드, `DRILLS`, `Q`, `TOPIC` | **새로 씀** |

조립과 점검(한 명령으로):
```
python3 kit/build.py --title "분산처리 17강 최종 일관성" --key ds17 --body body.html --content content.js --out page.html && python3 kit/test.py page.html
```

## content.js가 정의해야 하는 것
- `const Q = [[유형, 주제키, 문제, [보기...], 정답index, 해설, 그림?], ...]` 그림은 `['함수이름', {설정}]` → `FIG.함수이름(설정)`으로 문제 카드에 그려진다.
- `const TOPIC = { 키: '표시 이름', ... }`
- 선택: `const QTYPES = ['전체', ...]` (기본 '전체·암기·상황·그림·계산')
- 선택: `const DRILLS = { 키: { label: '이름', gen(){ return { q, correct, opts, steps:[...] }; } } }` (`opts(정답, [오답 후보...])` 사용)
- 선택: `const TREE_FIGS = { 그림키: () => FIG.x({...}) }` → 본문의 `<div class="fig-box" data-fig="그림키">`
- `PAGE_KEY`는 build.py가 넣는다(기록 저장 키). 강의마다 다르게.

## SVG 클래스 (라이트·다크 자동)
상자 `fx-box fx-lead fx-soft fx-old fx-empty fx-warnbox fx-badbox fx-okbox fx-group` · 선 `fx-ln fx-ln-m fx-ln-lead fx-ln-bad fx-ln-ok fx-ln-warn` + `fx-dash` · 화살표 marker `ah ahm ahl ahb aho` · 글자 `fx-t fx-ts fx-tm fx-tmono fx-tinv(진한 상자 위) fx-tinvs fx-tlead fx-tbad fx-tok fx-twarn` · 기타 `fx-dot fx-miss fx-off fx-bar fx-bar-bad fx-bar-warn fx-curve fx-tail fx-grid fx-commit fx-cut fx-life`

## 예시
`examples/ds16-body.html` + `examples/ds16-content.js` = 분산처리 16강 완성본. 필요한 부분만 grep으로 찾아 읽는다(통째로 읽지 않는다).
