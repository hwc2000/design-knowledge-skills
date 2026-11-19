# design-knowledge-skills

수업에서 배운 시스템 설계 지식을, 실제로 설계할 때 AI 코딩 에이전트(Claude Code)가 꺼내 쓰는 **스킬**로 바꾸는 저장소입니다.
강의 자료를 주제 단위로 쪼개 "설계할 때 생기는 질문"별로 다시 묶고, 필요한 조각만 읽히게 만드는 파이프라인과 그 결과물을 담았습니다.

## 문제

- 강의 슬라이드는 수백~수천 장입니다. 통째로 에이전트에게 넣으면 컨텍스트가 넘치고 비용이 커집니다.
- 강의는 "16강, 17강" 순서로 나뉘지만, 설계할 때 떠오르는 건 "이 데이터를 어떻게 복제하지?" 같은 질문입니다.
- 같은 개념이 여러 질문에 걸칩니다. 복사해 두면 한쪽만 고쳐져 내용이 어긋납니다.

## 설계

**1. 스킬 하나 = 설계 질문 하나** (지금 9개는 첫 과목에서 나온 것이고, 과목이 늘면 질문도 늘어납니다)

| 스킬 | 설계 질문 |
|---|---|
| `design-structure` | 시스템을 어떤 모양으로 나누나 |
| `design-communication` | 어떻게 주고받나 |
| `design-performance` | 통신을 어떻게 빠르게 하나 |
| `design-partitioning` | 데이터를 어떻게 나누고 어디서 찾나 |
| `design-consistency` | 읽는 사람에게 무엇을 보장하나 |
| `design-replication` | 복사본을 어떻게 맞추나 |
| `design-conflict-ordering` | 동시에 쓰면 무엇이 먼저인가 |
| `design-coordination` | 누가 결정하나 (락·리더) |
| `design-failure` | 죽으면 어떻게 알고 견디나 |
| `design-review` | 설계안을 질문 라운드로 비판 검토 (입구) |

**2. 필요한 만큼만 읽힌다 (3단계)**

```
description 한 줄   ← 항상 읽힘. 이 스킬을 열지 판단
SKILL.md            ← 스킬을 열 때. 먼저 물을 질문 · 선택지 표 · 흔한 함정 (과목 중립)
references/<과목>/  ← 근거가 필요할 때. Grep 으로 해당 주제만
```

**3. 주 태그 + 보조 링크**

- 주제마다 9개 설계 질문 중 하나를 **주 태그**로 붙여 본문은 그 스킬에만 둡니다.
- 다른 질문에도 걸치면 **보조 태그**(최대 2개)로 그 스킬의 `references/관련-주제.md` 에 한 줄 링크만 남깁니다.
- 링크는 빌드할 때마다 전체 references 에서 새로 만들어, 본문과 어긋나지 않습니다.

**4. 과목 중립**

SKILL.md 에는 어느 과목을 넣어도 통하는 판단 기준만 씁니다. 제품 이름은 "예:"로만 쓰고, 과목별 내용은 `references/<과목>/` 에만 둡니다. 새 과목은 폴더만 늘어납니다.

자세한 결정 과정: [docs/design.md](docs/design.md)

## 파이프라인

```
강의 PDF ──(study-knowledge-tree 스킬)──▶ 지식트리 페이지
   ──extract.py──▶ 단원·주제·본문 JSON
   ──tag.py──▶ 주 태그(과목 설정의 단원 태그 + 주제 이름 규칙) · 보조 태그(SEE 규칙)
   ──build_skills.py──▶ skills/<스킬>/references/<과목>/NN강-….md
                        skills/<스킬>/references/관련-주제.md
                        SKILL.md 의 references 목록 갱신
```

- 과목마다 설정 파일 하나(`pipeline/subjects/<과목>.json`)에 강의 목록과 단원 태그를 둡니다. 강의 번호는 선택입니다.
- 강의를 하나씩 추가할 수 있습니다. 입력에 든 강의 파일만 지우고 다시 쓰고, 다른 강의·과목은 건드리지 않습니다.
- 지식트리를 만든 뒤 설계 스킬에 넣을지는 **매번 사용자에게 묻고** 허락할 때만 진행합니다.
- 지식트리를 만드는 쪽도 스킬입니다. `skills/study-knowledge-tree/kit/` 에 공용 부품(CSS·탭·트리·문제은행 엔진)과 조립·자동 점검 스크립트가 있어, 강의마다 본문과 내용 파일 두 개만 새로 씁니다.

## 검증

- **빌드 전후 비교:** 강의를 추가할 때 기존 references 파일이 한 글자도 바뀌지 않았는지 백업과 diff 로 확인합니다.
- **규칙 충돌 확인:** 새 태그 규칙이 예전 강의 주제를 엉뚱한 스킬로 옮기지 않는지, 같은 낱말을 쓰는 기존 주제를 먼저 검색합니다.
- **지식트리 자동 점검:** `kit/test.py` 가 문법, 문제은행 전 문항(정답·그림), 무작위 드릴 유형별 200회(보기 중복·정답 포함), 트리 그림, JS 오류를 검사합니다.

## 공개 범위

- `skills/*/references/` (강의 정리)는 저작권 때문에 올리지 않습니다 (`.gitignore`). 모양은 [examples/references-sample/](examples/references-sample/) 에 일반 지식으로 쓴 샘플로 보여 줍니다.
- 지식트리 키트의 실제 강의 예시도 올리지 않습니다.

## 설치

```bash
git clone <이 저장소>
cd design-knowledge-skills
./install.sh          # ~/.claude/skills 에 스킬마다 바로가기를 건다
```

강의 자료를 추가하는 절차는 [docs/design.md](docs/design.md#새-강의새-과목-추가) 에 있습니다.

## 다음

- 다른 과목(인프라 등) 추가: 같은 9개 스킬에 과목 폴더만 늘린다.
- 검증 스킬: AI 가 "테스트 통과" 라고 말할 때 그게 진짜 검증인지 판단하는 절차 (holdout · 대조군 · 하드코딩 감지).

## 라이선스

MIT. `skills/design-review/` 는 [mattpocock/skills](https://github.com/mattpocock/skills) 의 grilling(MIT)을 한국어로 고친 것입니다.
