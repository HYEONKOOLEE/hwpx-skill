# hwpx-skill

한글 문서(**`.hwp` / `.hwpx`**)를 AI 에이전트가 직접 **읽고, 고치고, 만들고, 저장**할 수 있게
해주는 스킬입니다. `.hwp`를 그대로 올려도 자동 변환해 처리하고, **올린 형식 그대로 되돌려줍니다**
(한컴오피스 설치 불필요).

**클로드 코드(Claude Code) · 코워크(Cowork) · 코덱스(Codex CLI)** 세 환경에서 모두 설치할 수 있습니다.

> **버전** v1.4.2 · **최종 수정** 2026-09-05
>
> **이 저장소 하나로 완결됩니다. 함께 설치해야 하는 다른 스킬은 없습니다.**
>
> **v1.4 변경점**: **새 문서 생성 워크플로(C)** 를 신설했습니다. 양식 없이 처음부터 만드는
> 사내 규정·매뉴얼에서, `set_paragraph_format()`의 인자를 생략하면 그 속성을 가진 기존 서식이
> **조용히 재사용**되어 본문 전체가 가운데 정렬로 나오거나 단락마다 쪽나눔이 걸립니다.
> 검증 도구는 텍스트·구조만 보므로 이를 **전부 통과**시킵니다. 빌더 클래스 패턴과 절대 규칙
> R5~R9(서식 속성 명시 · id 중복 재부여 · 표 배색과 정렬 · A4 세로 지정 · 저장 파이프라인)로
> 막습니다.
> 자세한 내용은 `skills/hwpx/CHANGELOG.md` 참조.

---

## ⚡ 가장 빠른 설치 — 링크 하나로 (Claude 앱·Cowork)

파일을 주고받을 필요 없이 **아래 링크 하나만 공유**하면 됩니다.

**📥 다운로드: https://github.com/HYEONKOOLEE/hwpx-skill/releases/download/v1.4.2/hwpx-v1.4.2.skill**

1. 위 링크를 눌러 `hwpx-v1.4.2.skill` 파일을 내려받습니다 (확장자를 바꾸지 마세요)
2. Claude 앱 왼쪽 메뉴 **사용자 지정** → **스킬** 탭 → 오른쪽 위 **추가 → 스킬 업로드**
3. 내려받은 `.skill` 파일을 선택하면 끝 — **내 것** 탭에 `hwpx`가 나타나고 토글이 켜져 있으면 바로 사용됩니다
4. 새 대화에서 "이 내용으로 한글 파일 만들어줘"라고 요청하면 자동으로 동작합니다
   (필요한 패키지는 Claude가 알아서 설치합니다)

> 클로드 코드(Claude Code)·코덱스(Codex CLI) 사용자는 아래 **설치** 절의 방법 A~C를 쓰세요.

---

## 무엇을 할 수 있나

| 하고 싶은 것 | 예시 요청 |
|---|---|
| 새 한글 문서 만들기 | "이 내용으로 보고서 한글 파일 만들어줘" |
| 공문·기안문 작성 | "이 안건으로 공문 하나 써줘" |
| 양식에 내용 채우기 | "이 hwpx 양식에 우리 회사 정보로 채워줘" |
| **기존 원고 수정** | "이 한글 원고에서 3장 내용만 고쳐줘" |

특히 **이미 완성된 원고를 고치는 작업**을 별도 절차(`skills/hwpx/references/edit-existing.md`)로
분리해 둔 것이 이 스킬의 핵심입니다. 이 절차 없이 새로 만들듯 처리하면 원본 서식이 깨지고
내용이 유실됩니다.

---

## 설치

### 공통 준비 — 저장소 내려받기

```bash
git clone https://github.com/HYEONKOOLEE/hwpx-skill.git
cd hwpx-skill
```

> 공개(Public) 저장소이므로 별도 권한 없이 내려받을 수 있습니다.
> git 없이 쓰려면 `dist/`의 `.skill`(=zip) 파일만 받아 아래 **방법 C**로 설치해도 됩니다.

---

### 방법 A — 스크립트로 한 번에 (권장)

세 환경 중 **클로드 코드**와 **코덱스**를 자동으로 설치합니다.

**Windows (PowerShell)**

```powershell
.\install.ps1              # 클로드 코드 + 코덱스 모두
.\install.ps1 -Target codex   # 코덱스에만
```

> 실행이 차단되면 한 번만: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

**macOS / Linux**

```bash
chmod +x install.sh
./install.sh               # 클로드 코드 + 코덱스 모두
./install.sh claude        # 클로드 코드에만
```

---

### 방법 B — 클로드 코드 플러그인으로 설치

저장소 자체가 플러그인 마켓플레이스로 구성돼 있습니다.
스킬이 업데이트되면 `/plugin marketplace update`로 최신본을 받을 수 있어 관리가 편합니다.

```
/plugin marketplace add HYEONKOOLEE/hwpx-skill
/plugin install hwpx@hyeonkoolee-skills
```

> 공개 저장소라 별도 GitHub 인증 없이 바로 설치됩니다.

---

### 방법 C — 폴더 직접 복사 (수동)

`skills/hwpx` 폴더를 통째로 아래 위치에 넣습니다.

| 환경 | 넣을 위치 |
|---|---|
| **클로드 코드** | `~/.claude/skills/hwpx/` <br> Windows: `%USERPROFILE%\.claude\skills\hwpx\` |
| **코덱스 CLI** | `~/.agents/skills/hwpx/` <br> Windows: `%USERPROFILE%\.agents\skills\hwpx\` |

프로젝트 단위로만 쓰고 싶다면 각각 `.claude/skills/hwpx/`, `.agents/skills/hwpx/`에
넣으면 해당 프로젝트에서만 동작합니다.

---

### 방법 D — 코워크(Cowork)

코워크는 폴더 복사가 아니라 **파일 업로드** 방식입니다. 맨 위 **⚡ 가장 빠른 설치**와 같습니다.

1. `dist/hwpx-v1.4.2.skill` 파일을 내려받습니다 ([바로 받기](https://github.com/HYEONKOOLEE/hwpx-skill/releases/download/v1.4.2/hwpx-v1.4.2.skill))
2. Claude 앱 **사용자 지정 → 스킬 → 추가 → 스킬 업로드**에서 파일을 선택합니다
   (대화창에 파일을 올린 뒤 **저장** 버튼을 눌러도 됩니다)

끝입니다. 이후 모든 코워크 세션에서 자동으로 쓰입니다.

---

### 의존 패키지

문서를 실제로 만들 때 아래 패키지가 필요합니다. 에이전트가 알아서 설치하지만, 막히면 직접 실행하세요.

```bash
pip install python-hwpx
# 시스템 파이썬이 보호돼 있다면
pip install python-hwpx --break-system-packages

# .hwp 파일을 직접 올려서 쓸 때만 (생략해도 .hwpx 작업은 전부 정상 동작)
npm i @rhwp/core
```

> ### ⚠️ `@rhwp/core`는 npm 패키지입니다 — 설치할 "다른 스킬"이 아닙니다
>
> 이름 때문에 "rhwp 스킬도 같이 깔아야 하나?" 하는 오해가 자주 생깁니다. 정리하면:
>
> | 이름 | 정체 | 필요 여부 |
> |---|---|---|
> | **`@rhwp/core`** | npm 라이브러리(Rust+WASM HWP 파서) | `.hwp`를 직접 올릴 때만. `npm i` 한 줄 |
> | `rhwp` CLI · 누름틀 채우기 스킬 | 메일머지용 **별개 도구** | **불필요.** 이 스킬과 무관합니다 |

---

## 설치 확인

설치 후 에이전트에게 이렇게 물어보세요.

> "hwpx 스킬 설치됐어? 한글 문서 만들 수 있어?"

또는 아래 표현이 나오면 스킬이 자동으로 켜집니다.

> "한글 문서로 만들어줘" · "hwpx로 저장해줘" · "한글파일" · "공문 써줘" · "기안문"
> "이 한글 원고 수정해줘" · "이 양식에 채워줘"

Word(.docx)가 필요하면 이 스킬이 아니라 각 도구의 `docx` 스킬이 쓰입니다.

---

## 저장소 구성

```
hwpx-skill/
├── skills/hwpx/                  ← 스킬 본체 (이 폴더 하나가 정본)
│   ├── SKILL.md                    에이전트가 읽는 지침
│   ├── README.md                   스킬 자체 설명서
│   ├── CHANGELOG.md                스킬 변경 이력
│   ├── references/                 서식 규격·편집 절차 4종
│   ├── scripts/                    후처리·검증·변환·익명화 스크립트 6종
│   ├── assets/                     공공기관 표준 양식 2종
│   └── evals/                      동작 검증 테스트 케이스 7종 + 실전 고정 샘플
├── dist/                         ← 코워크 업로드용 배포 파일
│   ├── hwpx-v1.4.2.skill
│   └── hwpx-v1.4.2.zip
├── .claude-plugin/               ← 클로드 코드 플러그인 매니페스트
│   ├── marketplace.json
│   └── plugin.json
├── install.ps1                   ← Windows 설치 스크립트
├── install.sh                    ← macOS·Linux 설치 스크립트
├── README.md                     ← 이 파일
└── CHANGELOG.md                  ← 저장소 변경 이력
```

`skills/hwpx` **한 폴더가 모든 설치 경로의 원본**입니다. 스킬을 고칠 때는 여기만 수정하고,
`dist/`의 배포 파일을 다시 만들면 됩니다.

---

## 꼭 알아둘 3가지

1. **텍스트를 한 글자라도 바꿨으면 레이아웃 캐시를 지워야 합니다.**
   안 지우면 한글에서 열었을 때 글자가 겹치거나 잘려 보입니다. → `scripts/clear_layout_cache.py`

2. **다시 압축할 때는 `mimetype`을 무압축으로 맨 앞에 넣어야 합니다.**
   순서나 압축 방식이 틀리면 한글이 파일을 아예 열지 못합니다.

3. **전달 전 반드시 검증하세요.** → `scripts/verify_hwpx.py`

세 가지 모두 `SKILL.md`에 절차가 적혀 있고, 에이전트가 자동으로 따릅니다.

---

## 문제가 생기면

| 증상 | 확인할 것 |
|---|---|
| 스킬이 안 불려옴 | 폴더 위치가 맞는지 / 도구를 재시작했는지 / `SKILL.md` 맨 앞에 BOM이 붙지 않았는지 |
| 한글에서 파일이 안 열림 | 재압축 시 `mimetype`이 맨 앞·무압축인지 |
| 글자가 겹치거나 잘림 | 레이아웃 캐시를 지웠는지 |
| 표가 삐뚤어짐 | `autofit_table_rows.py`를 돌렸는지 |
| 태그 오류·파싱 실패 | `fix_namespaces.py`로 복구 시도 |

> **BOM 주의** — `SKILL.md`를 Windows PowerShell의 `Out-File`이나 `>`로 저장하면 파일 앞에
> 보이지 않는 표식(BOM)이 붙습니다. 그러면 YAML 앞머리가 통째로 인식되지 않아
> **스킬이 아예 검색되지 않습니다.** 편집할 때는 BOM 없는 UTF-8로 저장하세요.

---

## 동봉 양식 관련 안내

`skills/hwpx/assets/`의 두 양식은 **공공기관 보고서 서식을 익히기 위한 일반 샘플**입니다.
특정 기관의 실제 문서가 아니며, 자리표시자(`기관명`, `제 목`, `2000. 00. 00`,
`내용을 입력하세요` 등)로 채워져 있습니다.

- `form2.hwp`의 차례 항목에 `유네스코 한국위원회 사업지원`이라는 **예시 문구**가 남아
  있습니다. 실제 사용 시 본인 내용으로 치환하면 됩니다.
- 소속 기관에 지정 양식이 있다면 그 파일을 `assets/`에 넣고 `SKILL.md`의 템플릿 경로만
  바꿔 쓰는 것을 권합니다.

---

작성일: 2026-09-06 | 버전: v1.4.2 | 작성: 프랭크 × 에이미 협업
