#!/usr/bin/env bash
# skills/ 아래 스킬마다 ~/.claude/skills/<이름> 에 바로가기(심볼릭 링크)를 건다.
# 이미 같은 이름의 진짜 폴더가 있으면 덮어쓰지 않고 알려 준다.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$dest"
for d in "$here"/skills/*/; do
  name="$(basename "$d")"
  target="$dest/$name"
  if [ -L "$target" ]; then
    ln -sfn "${d%/}" "$target"; echo "갱신: $name"
  elif [ -e "$target" ]; then
    echo "건너뜀: $target 에 이미 진짜 폴더가 있다. 옮기거나 지운 뒤 다시 실행한다."
  else
    ln -s "${d%/}" "$target"; echo "연결: $name"
  fi
done
