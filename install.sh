#!/usr/bin/env bash
# hwpx 스킬을 Claude Code / Codex CLI에 설치합니다. (macOS / Linux)
#
# 사용법:
#   ./install.sh            # Claude Code + Codex 모두 (기본값)
#   ./install.sh claude     # Claude Code 개인 스킬 폴더에만
#   ./install.sh codex      # Codex CLI 개인 스킬 폴더에만
#
# 파일을 덮어쓰기만 하며, 기존 폴더를 지우지 않습니다.

set -euo pipefail

TARGET="${1:-all}"

# 이 스크립트가 있는 폴더 = 저장소 루트
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$REPO_ROOT/skills/hwpx"

if [ ! -d "$SKILL_SRC" ]; then
  echo "오류: 스킬 폴더를 찾을 수 없습니다 → $SKILL_SRC" >&2
  exit 1
fi

case "$TARGET" in
  all|claude|codex) ;;
  *) echo "오류: 대상은 all / claude / codex 중 하나여야 합니다 (입력값: $TARGET)" >&2; exit 1 ;;
esac

install_skill() {
  local dest_root="$1" label="$2"
  local dest="$dest_root/hwpx"

  mkdir -p "$dest_root"
  [ -d "$dest" ] && echo "  기존 설치를 덮어씁니다: $dest"

  cp -R "$SKILL_SRC" "$dest_root/"
  echo "  [OK] $label → $dest ($(find "$dest" -type f | wc -l | tr -d ' ')개 파일)"
}

echo
echo "hwpx 스킬 설치"
echo "----------------------------------------"

if [ "$TARGET" = "all" ] || [ "$TARGET" = "claude" ]; then
  install_skill "$HOME/.claude/skills" "Claude Code"
fi

if [ "$TARGET" = "all" ] || [ "$TARGET" = "codex" ]; then
  install_skill "$HOME/.agents/skills" "Codex CLI"
fi

echo "----------------------------------------"
echo
echo "다음 단계"
echo "  1) 의존 패키지 설치 (한 번만)"
echo "       pip install python-hwpx"
echo "  2) 도구를 재시작한 뒤 이렇게 요청해 보세요"
echo '       "이 내용으로 한글 문서 만들어줘"'
echo
echo "  Cowork(클로드 데스크톱 앱)에서 쓰려면 이 스크립트가 아니라"
echo "  dist/hwpx-v1.0.0.skill 파일을 대화창에 올려 저장하세요."
echo
