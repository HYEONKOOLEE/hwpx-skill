---
name: hwpx
description: "한글 문서(.hwp / .hwpx)를 읽고·편집하고·생성해 저장하는 단독 스킬. 다른 스킬을 함께 설치할 필요가 없다. **.hwp를 그대로 업로드해도 자동으로 .hwpx로 변환해 처리하고, 올린 형식 그대로 되돌려준다**(한컴오피스 불필요). '한글 문서','hwp','hwpx','한글파일','HWP 문서 생성','보고서','공문','기안문','한글로 작성','한글 원고 수정','hwp 편집','hwpx 편집' 등의 요청에 사용. 기존 한글 원고에 내용을 추가·수정하는 작업에도 적용한다. 일반 Word(.docx)는 docx 스킬을 쓸 것."
---

# HWPX 문서 생성·편집 스킬

> **버전** v1.2 · **최종 수정** 2026-09-01 · **변경 이력** `CHANGELOG.md`
> v1.2 변경점: **스킬 범위를 읽기·편집·저장으로 한정** — 다른 스킬로 넘기는 분기 제거, 단독 설치로 완결
> 설치·사용법은 같은 폴더의 `README.md`를 먼저 보세요.

## 개요

HWPX는 한컴오피스 한글의 개방형 문서 포맷이다. 내부는 **ZIP 패키지 + XML 파트** 구조이며, KS X 6101(OWPML) 표준에 기반한다. 이 스킬은 `python-hwpx`와 직접 XML 조작으로 HWPX 문서를 생성·편집·템플릿 치환한다.

### 이 스킬의 범위

| 한다 | 하지 않는다 |
|---|---|
| `.hwp`/`.hwpx` **읽기**(본문·표 텍스트 추출, 전수 조사) | 누름틀(필드) 서식 자동 채우기·메일머지 |
| **편집**(문자열 치환, 단락 삽입·삭제, 표 조작) | 한글 앱 자동화(매크로·COM 제어) |
| **생성**(양식 기반 보고서·공문 작성) | PDF 변환, 전자결재 시스템 연동 |
| **저장·검증**(올린 형식 그대로 반환) | Word(.docx) 처리 → `docx` 스킬 |

**이 네 가지는 이 스킬 폴더 하나로 완결된다. 추가 스킬을 설치할 필요가 없다.**

## 설치

```bash
pip install python-hwpx --break-system-packages       # HWPX 처리 (필수)
npm i @rhwp/core                                       # .hwp 입력을 받을 때만 (0-A단계)
```

> ### ⚠️ `@rhwp/core`는 npm 라이브러리다 — 설치할 "다른 스킬"이 아니다
>
> 이름이 비슷해 오해가 잦다. 정리하면:
>
> | 이름 | 정체 | 이 스킬과의 관계 |
> |---|---|---|
> | **`@rhwp/core`** | npm 패키지(Rust+WASM 파서) | **이 스킬의 내부 의존성.** `npm i` 한 줄로 끝. 0-A단계 `.hwp` 변환에만 쓴다 |
> | `rhwp` CLI / 관련 별도 스킬 | 누름틀 채우기·메일머지용 **다른 도구** | **무관하다. 설치하지 않는다.** 이 스킬은 그쪽을 호출하지 않는다 |
>
> `npm i @rhwp/core`가 실패해도 `.hwpx` 작업은 전부 정상 동작한다. 실패는 `.hwp` 직접 입력에만 영향을 준다.

> 이 문서에서 `$SKILL_DIR`는 이 스킬 폴더의 실제 경로다(환경에 따라 `/mnt/skills/user/hwpx` 또는 `~/.claude/skills/hwpx`). 스크립트를 호출하기 전에 경로를 한 번 확인한다.

---

## ⚠️ 0-A단계: 입력 형식 게이트 — `.hwp`면 먼저 변환한다

> **사용자가 `.hwp`를 올렸든 `.hwpx`를 올렸든 이 스킬은 똑같이 동작한다.**
> 사용자에게 "hwpx로 저장해서 다시 올려달라"고 요구하지 않는다. 여기서 자동 변환한다.

### 판정

```bash
ls -la ./*.hwp ./*.hwpx 2>/dev/null
file 업로드파일.hwp          # "Hancom HWP ... version 5.0" 이면 HWP5 바이너리
```

| 업로드 형식 | 조치 |
|---|---|
| `.hwpx` | 변환 없이 바로 0단계(A/B 판별)로 |
| `.hwp` (HWP5) | **아래 변환 절차 실행 → `.hwpx` 확보 후** 0단계로 |
| `.hml` | 위 변환기가 함께 처리한다(`to-hwpx` 동일) |

### 변환기 설치 (작업 폴더에서 1회)

`@rhwp/core`는 Rust+WASM 기반 HWP/HWPX 파서 **라이브러리**로, **한컴오피스 없이** HWP5 ↔ HWPX 상호 변환을 한다. 이 스킬이 직접 `require`해 쓰는 의존성이며, 사용자가 별도의 스킬이나 CLI를 설치할 필요는 없다.

```bash
mkdir -p ./_bridge && cd ./_bridge && npm init -y >/dev/null && npm i @rhwp/core
```

### 변환 스크립트 `_bridge/hwp_bridge.mjs` (그대로 생성한다)

```javascript
#!/usr/bin/env node
// hwp_bridge.mjs — HWP5 <-> HWPX 변환 게이트 (@rhwp/core WASM, 한컴오피스 불필요)
//   node hwp_bridge.mjs to-hwpx <입력.hwp>  <출력.hwpx>
//   node hwp_bridge.mjs to-hwp  <입력.hwpx> <출력.hwp>
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const [, , mode, src, dst] = process.argv;
if (!['to-hwpx', 'to-hwp'].includes(mode) || !src || !dst) {
  console.error('usage: node hwp_bridge.mjs <to-hwpx|to-hwp> <src> <dst>');
  process.exit(2);
}

const require = createRequire(import.meta.url);
const pkgDir = path.dirname(require.resolve('@rhwp/core/package.json'));
const { default: init, HwpDocument } = await import(path.join(pkgDir, 'rhwp.js'));
await init({ module_or_path: fs.readFileSync(path.join(pkgDir, 'rhwp_bg.wasm')) });

const doc = new HwpDocument(new Uint8Array(fs.readFileSync(src)));
const exp = mode === 'to-hwpx' ? doc.exportHwpxWithReport() : doc.exportHwpWithReport();
const loss = JSON.parse(exp.contentLoss() || '{}');
const bytes = exp.takeBytes();
fs.writeFileSync(dst, Buffer.from(bytes));

const out = { mode, src, dst, bytes: bytes.length, contentLoss: loss };
if (mode === 'to-hwp') out.verify = JSON.parse(doc.exportHwpVerify());   // 쪽수 보존 검증
console.log(JSON.stringify(out, null, 2));

// 손실이 보고되면 종료코드 3 — 조용히 넘어가지 않는다
process.exit((loss.count ?? 0) > 0 ? 3 : 0);
```

### 실행

```bash
node ./_bridge/hwp_bridge.mjs to-hwpx ./원본.hwp ./work.hwpx
python "$SKILL_DIR/scripts/verify_hwpx.py" ./work.hwpx        # 변환 직후 1차 검증
```

**판정 규칙**

- `contentLoss.count: 0` → 무손실. 그대로 진행한다.
- `contentLoss.count > 0` (종료코드 3) → `losses[]` 항목을 **사용자에게 그대로 보고**하고,
  계속할지 물어본다. 조용히 진행하지 않는다.
- `verify_hwpx.py`가 FAIL이면 변환 실패다. 사용자에게 "한글에서 직접 `.hwpx`로
  저장해 다시 올려달라"고 요청한다(최후 수단).
- `npm i`가 네트워크 문제로 실패하면 변환할 수 없다. 위와 같이 수동 저장을 요청한다.

### 산출 형식 규약 — **올린 형식 그대로 되돌린다**

작업이 끝나면 사용자가 올린 확장자로 맞춰 돌려준다.

| 사용자가 올린 것 | 최종 전달물 | 마지막 단계 |
|---|---|---|
| `.hwpx` | `.hwpx` | 그대로 전달 |
| `.hwp` | **`.hwp`** | 아래 역변환 후 전달 |

```bash
# 편집 완료본(.hwpx) → 제출용(.hwp)
node ./_bridge/hwp_bridge.mjs to-hwp ./work.hwpx ./최종본.hwp
```

역변환 결과의 `verify` 블록에서 **`pageCountBefore == pageCountAfter`** 와
**`recovered: true`** 를 확인한 뒤에 전달한다. 어긋나면 `.hwpx`도 함께 전달하고
사실을 알린다.

> **원본은 절대 덮어쓰지 않는다.** 업로드된 `.hwp`는 그대로 두고 `work.hwpx`,
> `최종본.hwp` 같은 새 파일로만 작업한다.

> 역변환은 HWPX→HWP 어댑터를 거치므로 **한 번 왕복하면 내부 구조가 재작성된다.**
> 왕복은 작업당 1회로 끝낸다(변환 → 편집 → 역변환). 편집할 때마다 왕복하지 않는다.

---

## ⚠️⚠️⚠️ 0단계: 작업 유형부터 판별한다 ⚠️⚠️⚠️

무엇을 하려는지에 따라 절차가 완전히 다르다. **먼저 갈래를 정하고 시작한다.**

| 사용자 요청 | 작업 유형 | 따라갈 절차 |
|---|---|---|
| "보고서 만들어줘", "공문 써줘", "이 양식으로 채워줘" | **A. 생성 / 템플릿 치환** | 아래 「A. 템플릿 치환 워크플로」 |
| "이 원고 수정해줘", "이 내용 추가해줘", "팩트체크 반영해줘", 완성된 hwpx를 주며 고쳐 달라 | **B. 기존 문서 편집** | **`references/edit-existing.md`를 먼저 읽을 것** |

> **0-A단계를 먼저 통과했다고 전제한다** — 이 시점에서 손에 있는 파일은 반드시 `.hwpx`다.
>
> B를 A의 절차로 처리하면 원본 서식이 깨지고 내용이 유실된다. 사용자가 **이미 완성된 원고**를 줬다면 그것은 채울 양식이 아니라 지켜야 할 자산이다.

---

## 🔴 유형 무관 절대 규칙 3가지

이 세 가지는 A·B 어느 쪽이든, 문서를 저장할 때마다 예외 없이 적용한다.

### R1. 텍스트를 한 글자라도 바꿨으면 레이아웃 캐시를 지운다

```bash
python "$SKILL_DIR/scripts/clear_layout_cache.py" out.hwpx
```

**표 셀만의 문제가 아니다. 본문 단락에도 똑같이 발생한다.** 원리는 아래 「필수 후처리 2」 참조.

### R2. 재패키징은 mimetype-first + 무압축

수동 zip으로 다시 묶을 때 mimetype을 압축하면 한글이 파일을 열지 못한다.

```bash
cd 압축푼폴더
zip -X -0 -q ../out.hwpx mimetype          # 첫 항목, 무압축(STORED)
zip -X -r -q ../out.hwpx . -x mimetype     # 나머지
```

### R3. 전달 전 반드시 검증한다

```bash
python "$SKILL_DIR/scripts/verify_hwpx.py" out.hwpx --base 원본.hwpx
```

**PASS**가 뜨고 `linesegarray 잔존 0개`를 확인하기 전에는 사용자에게 파일을 보내지 않는다.

---

## A. 템플릿 치환 워크플로

### A-1단계: 사용자 업로드 양식이 있는가?

사용자가 `.hwpx`(또는 0-A단계에서 변환한 `.hwp`) 양식 파일을 업로드했다면 **반드시 해당 파일을 템플릿으로 사용**한다.
- 업로드 폴더에 `.hwpx`/`.hwp` 파일이 있는지 확인
- 있다면 → 그 파일을 복사하여 템플릿으로 사용 (기본 양식 무시)
- "이 양식으로 만들어줘", "이 파일 기반으로" 등의 표현 → 100% 해당 파일 사용

### A-2단계: 기본 제공 양식 사용

- 보고서 → `assets/report-template.hwpx`

### A-3단계: HwpxDocument.new()는 최후의 수단

빈 문서 생성은 **아주 단순한 메모·목록 수준**에만 허용한다. 보고서·공문·기안문은 절대 `new()`로 만들지 않는다.

### 치환 절차

```
[1] 양식 파일을 작업 폴더로 복사
     ↓
[2] ObjectFinder로 양식 내 텍스트 전수 조사
     ↓
[3] 플레이스홀더 목록 작성 (어떤 텍스트를 뭘로 바꿀지 매핑)
     ↓
[4] ZIP-level 전체 치환 (표 내부 포함)
     ↓  (동일 플레이스홀더가 여러 번 나오면 순차 치환)
[5] 네임스페이스 후처리 (fix_namespaces.py)
     ↓
[6] 레이아웃 캐시 제거 (clear_layout_cache.py)      ★ R1
     ↓
[7] 무결성 검증 (verify_hwpx.py)                    ★ R3
     ↓
[8] 결과물 전달
```

### 핵심: HwpxDocument.open()은 사용하지 않는다

`python-hwpx` 버전에 따라 `HwpxDocument.open()`이 복잡한 양식 파일을 파싱하지 못할 수 있다. **ZIP-level 치환만 사용**하는 것이 안전하다.

---

## ZIP-level 치환 함수 (직접 구현)

`hwpx_replace` 모듈은 별도로 존재하지 않으므로 아래 함수를 직접 코드에 포함한다.

### 일괄 치환

```python
import zipfile, os

def zip_replace(src_path, dst_path, replacements):
    """HWPX ZIP 내 모든 XML에서 텍스트 치환 (표 내부 포함)"""
    tmp = dst_path + ".tmp"
    with zipfile.ZipFile(src_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.startswith("Contents/") and item.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    for old, new in replacements.items():
                        text = text.replace(old, new)
                    data = text.encode("utf-8")
                zout.writestr(item, data)
    if os.path.exists(dst_path):
        os.remove(dst_path)
    os.rename(tmp, dst_path)
```

### 순차 치환 (동일 플레이스홀더를 순서대로 다른 값으로)

```python
def zip_replace_sequential(src_path, dst_path, old, new_list):
    """section XML에서 old를 순서대로 new_list 값으로 하나씩 치환"""
    tmp = dst_path + ".tmp"
    with zipfile.ZipFile(src_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if "section" in item.filename and item.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    for new_val in new_list:
                        text = text.replace(old, new_val, 1)
                    data = text.encode("utf-8")
                zout.writestr(item, data)
    if os.path.exists(dst_path):
        os.remove(dst_path)
    os.rename(tmp, dst_path)
```

> **치환이 조용히 실패하는 경우가 가장 위험하다.** 굵은 글씨나 색상 때문에 한 문장이 여러 `<hp:run>`으로 쪼개져 있으면 문장 전체로는 매칭되지 않는다. 굵게 구간을 넘지 않는 **부분 문자열**을 앵커로 잡고, 치환 함수에 `assert`를 넣어 실패를 드러낸다. 자세한 내용은 `references/edit-existing.md`「함정 1」.

---

## 양식 내 텍스트 전수 조사 방법

```python
from hwpx import ObjectFinder

finder = ObjectFinder("양식파일.hwpx")
for r in finder.find_all(tag="t"):
    if r.text and r.text.strip():
        print(repr(r.text))
```

---

## 기본 양식(report-template.hwpx) 활용 가이드

### 양식 구조

```
1쪽: 표지      → 기관명(30pt) + 보고서 제목(25pt) + 작성일(25pt)
2쪽: 목차      → 로마숫자(Ⅰ~Ⅴ) + 제목 + 페이지, 붙임/참고
3쪽~: 본문     → 결재란 + 제목(22pt) + 섹션 바(Ⅰ~Ⅳ) + □○―※ 계층 본문
```

### 본문 기호 체계 (공문서와 완전히 다름!)

```
1단계:  □    (HY헤드라인M 16pt, 문단 위 15)
2단계:  ○    (휴먼명조 15pt, 문단 위 10)
3단계:  ―    (휴먼명조 15pt, 문단 위 6)
4단계:  ※    (한양중고딕 13pt, 문단 위 3)
```

### 치환 가능한 플레이스홀더 목록

| 플레이스홀더 | 위치 | 치환 대상 | 치환 방법 |
|------------|------|----------|----------|
| `브라더 공기관` | 표지 1줄 | 기관명 | 일괄 치환 |
| `기본 보고서 양식` | 표지 2줄 | 보고서 제목 | 일괄 치환 |
| `2024. 5. 23.` | 표지 작성일 | 실제 작성일 | 일괄 치환 |
| `제 목` | 본문 페이지 제목 | 보고서 제목 | 일괄 치환 |
| `. 개요` 등 | 목차 항목 | 실제 목차 제목 | 일괄 치환 |
| ` 추진 배경` 등 | 섹션 바 제목 | 실제 섹션 제목 | 일괄 치환 |
| `헤드라인M 폰트 16포인트(문단 위 15)` | □ 본문 (8개) | 1단계 내용 | **순차 치환** |
| `  ○ 휴면명조 15포인트(문단위 10)` | ○ 본문 (8개) | 2단계 내용 | **순차 치환** |
| `   ― 휴면명조 15포인트(문단 위 6)` | ― 본문 (8개) | 3단계 내용 | **순차 치환** |
| `     ※ 중고딕 13포인트(문단 위 3)` | ※ 주석 (7개) | 4단계 참조 | **순차 치환** |
| `  1. 세부내용` / `  2. 세부내용` | 붙임/참고 | 첨부 목록 | 일괄 치환 |

### 전체 코드 예시

```python
import shutil, subprocess

SKILL_DIR = "/mnt/skills/user/hwpx"        # 환경에 맞게 확인
TEMPLATE  = f"{SKILL_DIR}/assets/report-template.hwpx"
WORK      = "./report.hwpx"
shutil.copy(TEMPLATE, WORK)

# 1. 표지 + 목차 + 섹션 바 + 제목 (일괄 치환)
zip_replace(WORK, WORK, {
    "브라더 공기관": "실제 기관명",
    "기본 보고서 양식": "실제 보고서 제목",
    "2024. 5. 23.": "2026. 2. 13.",
    "제 목": "실제 보고서 제목",
})

# 2. □ 항목 (순차 치환 — 8개)
zip_replace_sequential(WORK, WORK,
    "헤드라인M 폰트 16포인트(문단 위 15)",
    ["첫번째 □ 내용", "두번째 □ 내용"])

# 3. 후처리 3종 — 순서를 지킨다
subprocess.run(["python", f"{SKILL_DIR}/scripts/fix_namespaces.py", WORK], check=True)
subprocess.run(["python", f"{SKILL_DIR}/scripts/clear_layout_cache.py", WORK], check=True)
subprocess.run(["python", f"{SKILL_DIR}/scripts/verify_hwpx.py", WORK], check=True)
```

---

## B. 기존 문서 편집

사용자가 완성된 원고를 주고 수정·증보를 요청한 경우.

> **`references/edit-existing.md`를 반드시 먼저 읽는다.** 서식 ID 조사법, run 분할 함정,
> XML 이스케이프, 이미지 캡션 번호 재정렬, 검증 체크리스트가 모두 그 문서에 있다.

요약하면:

```
[1] 원본 복사 (원본은 절대 덮어쓰지 않는다)
[2] 본문 텍스트 추출해 통독
[3] 서식 ID 조사 → 본문/굵게/소제목/캡션 ID 확정
[4] 문자열 치환 + 단락 삽입 (새 단락에는 linesegarray를 넣지 않는다)
[5] mimetype-first 재패키징                          ★ R2
[6] 레이아웃 캐시 제거                                ★ R1
[7] verify_hwpx.py --base 원본 → PASS                ★ R3
```

---

## 문서 유형별 스타일 가이드

| 상황 | 읽을 문서 |
|---|---|
| 보고서(내부 보고용) 작성 | `references/report-style.md` |
| 공문서(기안문) 작성 | `references/official-doc-style.md` |
| **기존 원고 수정·증보** | `references/edit-existing.md` |
| 저수준 XML 조작 | `references/xml-internals.md` |

---

## ⚠️ 필수 후처리 1: 네임스페이스 수정

> **`python-hwpx`로 저장(`doc.save()`)했다면 반드시 실행.** 빠뜨리면 한글 Viewer에서 빈 페이지로 표시된다.

```python
subprocess.run(["python", f"{SKILL_DIR}/scripts/fix_namespaces.py", "output.hwpx"], check=True)
```

> ZIP-level 치환만 했다면 프리픽스가 바뀌지 않으므로 생략해도 무방하나, 실행해도 무해하다.
> 주의: `exec(open(...).read())` 방식은 스크립트의 `if __name__ == "__main__"` 블록 때문에 오동작할 수 있다. 반드시 `subprocess.run()`을 쓴다.

---

## ⚠️ 필수 후처리 2: 레이아웃 캐시 제거 (글씨 겹침 방지)

> **적용 조건: 텍스트를 한 글자라도 바꿨거나, 단락을 삽입·삭제했다면.**
> 표 셀만의 문제가 아니다. **본문 단락에서도 똑같이 겹친다.**

### 원리

HWPX의 모든 단락(`<hp:p>`)에는 한글이 마지막으로 그렸을 때의 줄 배치 캐시 `<hp:linesegarray>`가 들어 있다. 줄마다 `vertpos`(세로 위치)와 `textpos`(그 줄이 시작하는 글자 offset)가 박혀 있다.

파이썬으로 텍스트를 바꾸면 글자 수는 달라지는데 캐시는 옛 텍스트 기준으로 남는다. 한글은 캐시가 있으면 그것을 믿고 그리기 때문에:

- **텍스트가 길어지면** → 캐시에 없는 줄들이 마지막 줄 위치에 **겹쳐 찍힌다**
- **텍스트가 짧아지면** → 줄 사이에 빈 공간이 남는다
- **표 셀이면** → 행 높이가 옛 줄 수로 고정돼 잘려 보인다

캐시를 지우면 한글이 열 때 줄 위치를 전면 재계산하고, 자동 높이 행도 스스로 늘어난다.

### 실행

```bash
python "$SKILL_DIR/scripts/clear_layout_cache.py" output.hwpx           # 제거
python "$SKILL_DIR/scripts/clear_layout_cache.py" output.hwpx --check   # 잔존 개수만 확인
```

표 셀 높이가 과거 보정으로 부풀려진 문서를 정상화해야 한다면 `autofit_table_rows.py`를 대신 쓴다(캐시 제거 + 인라인 제목표 높이 정규화를 함께 수행).

> **셀 높이를 파이썬에서 줄 수로 추정해 올리지 않는다.** 한 줄짜리 제목표를 과대 추정해 높이를 부풀린 회귀 버그가 있었다. 높이는 캐시 제거 후 한글이 자동으로 맞춘다.

---

## ⚠️ 필수 후처리 3: 무결성 검증

```bash
python "$SKILL_DIR/scripts/verify_hwpx.py" output.hwpx
python "$SKILL_DIR/scripts/verify_hwpx.py" output.hwpx --base 원본.hwpx   # 편집 작업이면
```

검사 항목: mimetype 규약 / 필수 파트 / XML well-formed / **linesegarray 잔존** / 이미지 참조 무결성 / 단락·이미지·글자 수 통계. `--base`를 주면 원본 대비 글자 수 증감을 보고한다.

**PASS + 캐시 잔존 0**을 확인한 뒤에 사용자에게 전달한다.

---

## Quick Reference

| 작업 | 접근 방식 |
|------|----------|
| **`.hwp` 파일을 받았을 때** | **0-A단계 — `hwp_bridge.mjs to-hwpx`로 변환 후 진행** |
| **`.hwp`로 돌려줘야 할 때** | **`hwp_bridge.mjs to-hwp` + `verify` 쪽수 확인** |
| 보고서/공문/양식 문서 생성 | **양식 파일 + ZIP-level 치환** (★ 권장) |
| **기존 원고 수정·증보** | **`references/edit-existing.md` 절차** |
| 아주 단순한 문서 | `HwpxDocument.new()` → `.save()` → 후처리 |
| 표(테이블) 추가 | `doc.add_table(rows, cols)` → `set_cell_text()` |
| 머리글/바닥글 | `doc.set_header_text()` / `doc.set_footer_text()` |
| 텍스트 검색/추출 | `ObjectFinder(filepath)` |
| 셀 병합 | `table.merge_cells(row1, col1, row2, col2)` |
| 글씨 겹침 발생 | `clear_layout_cache.py` |
| 전달 전 최종 확인 | `verify_hwpx.py --base 원본` |

---

## 주의사항

1. **작업 유형 판별이 먼저**: 완성 원고 수정(B)을 템플릿 치환(A) 절차로 처리하지 않는다
2. **양식 우선**: 사용자 업로드 양식 > 기본 제공 양식 > `HwpxDocument.new()`
3. **ZIP-level 치환 우선**: `HwpxDocument.open()`보다 안전하고 호환성이 높다
4. **양식 텍스트 조사 필수**: 치환 전에 반드시 ObjectFinder로 전수 조사
5. **순차 치환 주의**: 동일 플레이스홀더가 여러 번 나오면 `zip_replace_sequential`
6. **치환 실패를 조용히 넘기지 않는다**: run 분할 때문에 문장 전체 매칭은 자주 실패한다. `assert`로 드러낼 것
7. **XML 이스케이프**: 본문에 넣는 텍스트의 `&`, `<`, `>`를 반드시 이스케이프
8. **레이아웃 캐시 제거 필수**: 텍스트를 바꿨으면 표/본문 가리지 말고 실행. 안 하면 글씨 겹침
9. **셀 높이는 추정 금지**: 캐시만 지우면 한글이 자동으로 맞춘다
10. **재패키징 규약**: mimetype은 첫 항목 + 무압축(ZIP_STORED)
11. **전달 전 검증 필수**: `verify_hwpx.py` PASS 없이는 파일을 보내지 않는다
12. **레이아웃 충실도**: python-hwpx는 레이아웃 엔진이 아님. 페이지 나눔은 한글 앱이 결정
13. **글꼴 임베딩**: 생성 HWPX에 글꼴 미포함. 열람 환경에 해당 글꼴 필요
14. **공문서 날짜 형식**: `2026-02-13`이 아닌 `2026. 2. 13.` (월·일 앞 0 생략)
15. **HWPX ↔ HWP**: python-hwpx는 HWPX만 처리한다. 레거시 `.hwp`는 **0-A단계의 `@rhwp/core` 변환기**(npm 라이브러리, 별도 스킬 아님)로 앞뒤에서 감싼다(사용자에게 수동 변환을 요구하지 않는다)
16. **왕복은 1회**: `.hwp` → `.hwpx` → 편집 → `.hwp`. 편집 중간에 형식을 오가지 않는다
17. **변환 손실 보고 필수**: `contentLoss.count > 0`이면 항목을 사용자에게 알리고 진행 여부를 묻는다
18. **fix_namespaces 호출법**: `exec()` 말고 `subprocess.run()` 사용
19. **범위 밖 요청 처리**: 누름틀 자동 채우기·메일머지 요청이 오면 **다른 스킬 설치를 안내하지 않는다.** 이 스킬 범위 밖임을 한 줄로 알리고, 대신 가능한 방법(해당 텍스트를 ZIP-level 치환으로 직접 바꾸기)을 제시한다

---

작성일: 2026-09-01 | 버전: v1.2
