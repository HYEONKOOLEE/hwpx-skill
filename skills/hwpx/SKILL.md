---
name: hwpx
description: "한글 문서(.hwp / .hwpx)를 읽고·편집하고·생성해 저장하는 단독 스킬. 다른 스킬을 함께 설치할 필요가 없다. **.hwp를 그대로 업로드해도 자동으로 .hwpx로 변환해 처리하고, 올린 형식 그대로 되돌려준다**(한컴오피스 불필요). '한글 문서','hwp','hwpx','한글파일','HWP 문서 생성','보고서','공문','기안문','사내 규정','매뉴얼','지침서','계약서','한글로 작성','한글 원고 수정','hwp 편집','hwpx 편집' 등의 요청에 사용. 양식 없이 조문형 규정·매뉴얼을 새로 작성하는 작업에도 적용한다(C 워크플로). 일반 Word(.docx)는 docx 스킬을 쓸 것."
---

# HWPX 문서 생성·편집 스킬

> **버전** v1.4.1 · **최종 수정** 2026-09-05 · **변경 이력** `CHANGELOG.md`
> v1.4 변경점: **C. 새 문서 생성 워크플로 신설(R5~R9)** — 양식 없이 `HwpxDocument.new()`로 규정·매뉴얼 같은 조문형 장문을 만들 때의 함정을 규칙으로 못 박는다. **R5(서식 속성 전파)**는 가운데 정렬·페이지나눔이 뒤 단락 수백 개로 번져 문서를 통째로 망가뜨리는데 `verify_hwpx.py`가 잡지 못하는 영역이다. R6은 단락 id를 정리하는 안전장치이고, R7~R9는 용지 속성·검증 대체수단·표 서식 기본값을 정한다.
> v1.3 변경점: **R4(표 구조 무결성) 신설** — 행·열을 지우거나 추가할 때 세로 병합(rowSpan) 정합성을 함께 맞추지 않으면 한글이 파일을 열지 못한다. `verify_hwpx.py`에 검사 5번(표 병합 정합성)을 FAIL 조건으로 추가하고, 6번으로 단락 id 분포를 진단 정보로 낸다.
> ⚠️ **v1.4.1 정정** — "단락 id 중복이 한글의 파일 거부 원인"이라던 v1.3~v1.4 서술은 실측 결과 사실이 아니다. 동봉 `assets/report-template.hwpx`(한글이 직접 만든 정상 파일)는 단락 103개에 고유 id가 **3개뿐**이고(`2147483648` 69회, `0` 33회) 정상적으로 열린다. id는 유일 키가 아니라 sentinel 값이다. 검사 6번을 FAIL로 두면 이 스킬이 동봉한 자기 템플릿조차 FAIL이 되므로 진단 정보로 바꿨다.
> v1.2 변경점: 스킬 범위를 읽기·편집·저장으로 한정 — 다른 스킬로 넘기는 분기 제거, 단독 설치로 완결
> 설치·사용법은 같은 폴더의 `README.md`를 먼저 보세요.

## 개요

HWPX는 한컴오피스 한글의 개방형 문서 포맷이다. 내부는 **ZIP 패키지 + XML 파트** 구조이며, KS X 6101(OWPML) 표준에 기반한다. 이 스킬은 `python-hwpx`와 직접 XML 조작으로 HWPX 문서를 생성·편집·템플릿 치환한다.

### 이 스킬의 범위

| 한다 | 하지 않는다 |
|---|---|
| `.hwp`/`.hwpx` **읽기**(본문·표 텍스트 추출, 전수 조사) | 누름틀(필드) 서식 자동 채우기·메일머지 |
| **편집**(문자열 치환, 단락 삽입·삭제, 표 조작) | 한글 앱 자동화(매크로·COM 제어) |
| **생성**(양식 기반 보고서·공문 / 양식 없는 조문형 규정·매뉴얼) | PDF 변환, 전자결재 시스템 연동 |
| **저장·검증**(올린 형식 그대로 반환) | Word(.docx) 처리 → `docx` 스킬 |

**이 네 가지는 이 스킬 폴더 하나로 완결된다. 추가 스킬을 설치할 필요가 없다.**

## 설치

```bash
pip install python-hwpx --break-system-packages       # HWPX 처리 (필수)
npm i @rhwp/core                                       # .hwp 입력을 받을 때만 (0-A단계)
```

> 표 구조를 코드로 다룰 때는 `lxml`이 편하다(`pip install lxml`). `scripts/`의 검증 도구는 표준 라이브러리만 쓰므로 별도 설치가 필요 없다.

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

변환 스크립트는 `$SKILL_DIR/scripts/hwp_bridge.mjs`를 그대로 쓴다.

### 실행

```bash
node "$SKILL_DIR/scripts/hwp_bridge.mjs" to-hwpx ./원본.hwp ./work.hwpx
python "$SKILL_DIR/scripts/verify_hwpx.py" ./work.hwpx        # 변환 직후 1차 검증
```

**판정 규칙**

- `contentLoss.count: 0` → 무손실. 그대로 진행한다.
- `contentLoss.count > 0` (종료코드 3) → `losses[]` 항목을 **사용자에게 그대로 보고**하고,
  계속할지 물어본다. 조용히 진행하지 않는다.
- `verify_hwpx.py`가 FAIL이면 변환 실패다. 사용자에게 "한글에서 직접 `.hwpx`로
  저장해 다시 올려달라"고 요청한다(최후 수단).
- `npm i`가 네트워크 문제로 실패하면 변환할 수 없다. 위와 같이 수동 저장을 요청한다.

> ⚠️ **`contentLoss: 0` + `recovered: true`는 "한글에서 열린다"는 뜻이 아니다.**
> 이 리포트는 텍스트·쪽수 보존만 본다. 표 병합 같은 구조 무결성은 검사하지 않는다 → **R4** 참조.

### 산출 형식 규약 — **올린 형식 그대로 되돌린다**

작업이 끝나면 사용자가 올린 확장자로 맞춰 돌려준다.

| 사용자가 올린 것 | 최종 전달물 | 마지막 단계 |
|---|---|---|
| `.hwpx` | `.hwpx` | 그대로 전달 |
| `.hwp` | **`.hwp`** | 아래 역변환 후 전달 |

```bash
# 편집 완료본(.hwpx) → 제출용(.hwp)
node "$SKILL_DIR/scripts/hwp_bridge.mjs" to-hwp ./work.hwpx ./최종본.hwp
```

역변환 결과의 `verify` 블록에서 **`pageCountBefore == pageCountAfter`** 와
**`recovered: true`** 를 확인한 뒤에 전달한다. 어긋나면 `.hwpx`도 함께 전달하고
사실을 알린다.

> **표 구조를 변경한 문서라면 `.hwp`와 `.hwpx`를 항상 함께 전달한다.** 한글이 `.hwp`를 거부해도 사용자가 즉시 `.hwpx`로 확인할 수 있어야 한다.

> **원본은 절대 덮어쓰지 않는다.** 업로드된 `.hwp`는 그대로 두고 `work.hwpx`,
> `최종본.hwp` 같은 새 파일로만 작업한다.

> 역변환은 HWPX→HWP 어댑터를 거치므로 **한 번 왕복하면 내부 구조가 재작성된다.**
> 왕복은 작업당 1회로 끝낸다(변환 → 편집 → 역변환). 편집할 때마다 왕복하지 않는다.

---

## ⚠️⚠️⚠️ 0단계: 작업 유형부터 판별한다 ⚠️⚠️⚠️

무엇을 하려는지에 따라 절차가 완전히 다르다. **먼저 갈래를 정하고 시작한다.**

| 사용자 요청 | 작업 유형 | 따라갈 절차 |
|---|---|---|
| 양식 파일을 주며 "이 양식으로 채워줘", 기본 양식으로 보고서·공문 작성 | **A. 템플릿 치환** | 아래 「A. 템플릿 치환 워크플로」 |
| "이 원고 수정해줘", "이 내용 추가해줘", "팩트체크 반영해줘", 완성된 hwpx를 주며 고쳐 달라 | **B. 기존 문서 편집** | **`references/edit-existing.md`를 먼저 읽을 것** |
| **양식 없이** "규정 만들어줘", "매뉴얼 작성해줘", "지침서 써줘" 등 백지에서 조문형 장문 작성 | **C. 새 문서 생성** | **아래 「C. 새 문서 생성 워크플로」 + R5~R9** |

> **0-A단계를 먼저 통과했다고 전제한다** — 이 시점에서 손에 있는 파일은 반드시 `.hwpx`다.
>
> B를 A의 절차로 처리하면 원본 서식이 깨지고 내용이 유실된다. 사용자가 **이미 완성된 원고**를 줬다면 그것은 채울 양식이 아니라 지켜야 할 자산이다.
>
> A와 C를 혼동하지 않는다. **사용자가 준 양식이 있으면 무조건 A**다. 양식이 없을 때만 C로 간다.

---

## 🔴 유형 무관 절대 규칙 (R1~R4)

이 네 가지는 A·B·C 어느 쪽이든, 문서를 저장할 때마다 예외 없이 적용한다.

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

### R4. 표의 행·열을 지우거나 추가했으면 병합(span) 정합성을 맞춘다

> **이것을 빠뜨리면 한글이 "파일을 읽거나 저장하는데 오류가 있습니다"로 파일 자체를 거부한다.**
> v1.2까지는 `verify_hwpx.py`도, `@rhwp/core`의 `contentLoss`·`exportHwpVerify`도 이 오류를
> 잡지 못하고 **전부 PASS를 줬다.** v1.3에서 `verify_hwpx.py` 검사 5번으로 추가했다.

#### 무슨 일이 일어나는가

HWPX 표에서 세로로 병합된 셀은 `<hp:cellAddr rowAddr="7"/>` + `<hp:cellSpan rowSpan="11"/>`처럼 **시작 주소 + 걸치는 행 수**로 표현된다. 표 아래쪽 빈 행 3개를 지우면 표는 15행이 되는데, 병합 셀은 여전히 "나는 7행부터 11행을 차지한다"(= 18행까지)고 주장한다. 한글은 이 모순을 만나면 문서를 **아예 열지 않는다.**

서식 문서일수록 위험하다. 관공서 서식은 겉보기에 여러 표처럼 보여도 **전체가 표 하나**이고, 왼쪽 라벨 칸이 `rowSpan` 10 이상으로 크게 병합되어 있는 경우가 흔하다.

#### 규칙

1. **꼬리 행만 지운다.** 중간 행을 지우면 아래 행들의 `rowAddr`가 전부 밀려 훨씬 복잡해진다.
2. **`rowAddr`를 재부여하지 않는다.** 꼬리만 지우면 남은 행의 주소는 이미 맞다. 순번을 다시 매기면 병합 셀 주소가 깨진다.
3. **걸쳐 있던 병합 셀의 `rowSpan`을 줄이고**, `<hp:tbl rowCnt>`를 남은 행 수로 갱신한다.
4. **저장 직전 `verify_hwpx.py`(v1.3 이상) 또는 아래 assert를 반드시 통과시킨다.**
5. **애매하면 지우지 말고 빈 행으로 남긴다.** 빈 행 몇 개는 흠이지만, 안 열리는 파일은 산출물이 아니다.

#### 검사·보정 코드 (표 구조를 건드렸다면 그대로 붙여 쓴다)

```python
from lxml import etree
P = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"

def fix_and_check_table(tbl):
    """행 삭제 후 rowSpan/rowCnt 보정 + 정합성 assert"""
    rows = tbl.findall(P + "tr")
    n_rows = len(rows)
    for tr in rows:
        for tc in tr.findall(P + "tc"):
            a, s = tc.find(P + "cellAddr"), tc.find(P + "cellSpan")
            if a is None or s is None:
                continue
            top, span = int(a.get("rowAddr")), int(s.get("rowSpan"))
            if top + span > n_rows:                       # 삭제된 행까지 걸친 병합
                s.set("rowSpan", str(n_rows - top))
                print(f"[fix] rowSpan {span} -> {n_rows - top} (rowAddr={top})")
    tbl.set("rowCnt", str(n_rows))

    # 최종 검사 — 하나라도 걸리면 저장하지 않는다
    for tr in tbl.findall(P + "tr"):
        for tc in tr.findall(P + "tc"):
            a, s = tc.find(P + "cellAddr"), tc.find(P + "cellSpan")
            if a is not None and s is not None:
                assert int(a.get("rowAddr")) + int(s.get("rowSpan")) <= n_rows, \
                    f"rowSpan 초과: rowAddr={a.get('rowAddr')} rowSpan={s.get('rowSpan')} rows={n_rows}"

for tbl in root.iter(P + "tbl"):
    fix_and_check_table(tbl)
```

#### 표 구조 조사 (편집 전에 반드시 한 번)

```python
for ti, tbl in enumerate(root.iter(P + "tbl")):
    print(f"--- tbl {ti} rowCnt={tbl.get('rowCnt')} colCnt={tbl.get('colCnt')}")
    for i, tr in enumerate(tbl.findall(P + "tr")):
        cells = []
        for tc in tr.findall(P + "tc"):
            a, s = tc.find(P + "cellAddr"), tc.find(P + "cellSpan")
            cells.append(f"r{a.get('rowAddr')}c{a.get('colAddr')}"
                         f"/rs{s.get('rowSpan')}cs{s.get('colSpan')}")
        print("   tr", i, cells)
```

`rs`가 2 이상인 셀이 보이면 그 행 범위는 함부로 건드리지 않는다. **`colSpan`(가로 병합)도 열을 지울 때 같은 규칙이 적용된다.**

---

## A. 템플릿 치환 워크플로

### A-1단계: 사용자 업로드 양식이 있는가?

사용자가 `.hwpx`(또는 0-A단계에서 변환한 `.hwp`) 양식 파일을 업로드했다면 **반드시 해당 파일을 템플릿으로 사용**한다.
- 업로드 폴더에 `.hwpx`/`.hwp` 파일이 있는지 확인
- 있다면 → 그 파일을 복사하여 템플릿으로 사용 (기본 양식 무시)
- "이 양식으로 만들어줘", "이 파일 기반으로" 등의 표현 → 100% 해당 파일 사용

### A-2단계: 기본 제공 양식 사용

- 보고서 → `assets/report-template.hwpx`

### A-3단계: 양식이 없으면 C 워크플로로

양식 파일이 있는데도 `HwpxDocument.new()`로 만들지 않는다. 양식이 아예 없는 경우에만 **C. 새 문서 생성 워크플로**를 따르며, 그때는 R5~R9를 반드시 함께 적용한다.

### 치환 절차

```
[1] 양식 파일을 작업 폴더로 복사
     ↓
[2] ObjectFinder로 양식 내 텍스트 전수 조사
     ↓
[2-1] 표 구조(rowSpan/colSpan) 조사                 ★ R4 — 표를 건드릴 예정이면 필수
     ↓
[3] 플레이스홀더 목록 작성 (어떤 텍스트를 뭘로 바꿀지 매핑)
     ↓
[4] ZIP-level 전체 치환 (표 내부 포함)
     ↓  (동일 플레이스홀더가 여러 번 나오면 순차 치환)
[4-1] 행·열을 지웠다면 span 보정 + assert           ★ R4
     ↓
[5] 네임스페이스 후처리 (fix_namespaces.py)
     ↓
[6] 레이아웃 캐시 제거 (clear_layout_cache.py)      ★ R1
     ↓
[7] 무결성 검증 (verify_hwpx.py)                    ★ R3
     ↓
[8] 결과물 전달 (표 구조를 바꿨으면 .hwp + .hwpx 동시 전달)
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

### 셀 내용을 여러 줄로 교체할 때 (lxml)

한 셀에 여러 줄을 넣으려면 기존 `<hp:p>`를 복제해 줄 수만큼 만든다. **서식(`paraPrIDRef`·`charPrIDRef`)은 같은 표의 채워진 셀에서 가져와 맞춘다.** 빈 셀은 서식 ID가 다른 경우가 많다.

```python
import copy

def set_cell(tc, lines, para_ref=None, char_ref=None):
    sub = tc.find(P + "subList")
    paras = sub.findall(P + "p")
    base = copy.deepcopy(paras[0])
    for r in base.findall(P + "run")[1:]:
        base.remove(r)
    run = base.find(P + "run")
    if para_ref: base.set("paraPrIDRef", para_ref)
    if char_ref: run.set("charPrIDRef", char_ref)
    for p in paras:
        sub.remove(p)
    for line in lines:
        np = copy.deepcopy(base)
        np.find(P + "run").find(P + "t").text = line
        sub.append(np)
```

> `<hp:p>`를 복제하면 id까지 그대로 복사된다. 한글은 id 중복을 문제 삼지 않지만(**R6**), 복제본에는 새 id를 부여해 두는 편이 깔끔하다. 분포는 `verify_hwpx.py` 검사 6번이 알려 준다.
> lxml로 다시 직렬화할 때 XML 선언이 바뀌지 않도록 주의한다 — 원본과 동일하게 `<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>`를 붙인다.

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
[4-1] 표 행·열을 지웠다면 span 보정 + assert          ★ R4
[5] mimetype-first 재패키징                          ★ R2
[6] 레이아웃 캐시 제거                                ★ R1
[7] verify_hwpx.py --base 원본 → PASS                ★ R3
```

---

# C. 새 문서 생성 워크플로 (양식 없이 백지에서)

규정·매뉴얼·지침서·계약서처럼 **사용자가 양식을 주지 않고 내용만 요구한** 장문 문서를 만들 때의 절차다. `HwpxDocument.new()`로 시작하되, 아래 R5~R9를 지키지 않으면 **문서 전체가 가운데 정렬로 밀리거나, 쪽수가 4배로 늘거나, 한글이 파일을 열지 못한다.** 실제로 전부 겪은 함정이다.

## C-1. 빌더 클래스를 먼저 만든다

단락 하나하나에 `set_paragraph_format`을 직접 호출하지 말고, **문서 요소별 헬퍼(제목·장·조·항·표·별지)를 가진 빌더 클래스를 만들어 그것만 사용한다.** 규칙 위반을 한 곳에서 막을 수 있고, "표 색을 연하게" "본문을 왼쪽 정렬로" 같은 수정 요구가 와도 한 줄만 고치면 전체에 반영된다.

```
Doc 클래스 구성 예
  __init__      용지·여백·머리글·바닥글·쪽번호, 글자 스타일 사전, 셀 전용 paraPr 2종(좌/중앙)
  _p()          모든 단락의 단일 진입점 — R5를 여기서 강제한다
  chapter()     장 제목 (가운데, 새 쪽)
  art()         제N조(제목)
  hang()        ① / 1. / 가. 계층 본문 (내어쓰기)
  table()       머리행 있는 표
  strip()       1행짜리 라벨·값 서식 줄
  sign()        결재란
  annex()       별표·별지 제목 (새 쪽)
  save()        R6 → 후처리 3종 일괄 수행
```

## 🆕 R5. `set_paragraph_format`은 **모든 속성을 매번 명시**한다

> **이 규칙 하나를 빠뜨리면 문서 전체가 망가진다. C 워크플로에서 가장 중요한 규칙이다.**
> `verify_hwpx.py`는 이것을 검사하지 않는다. 서식은 문법이 아니라 의도의 문제이기 때문이다.

`python-hwpx`는 요청한 서식 조합에 맞는 `paraPr`를 찾아 재사용한다. 그런데 **인자를 생략하면 그 속성은 "상관없음"이 되어, 앞서 만들어 둔 다른 paraPr가 그대로 붙는다.** 표지 제목에 한 번 준 `alignment='CENTER'`, 장 제목에 한 번 준 `page_break_before=True`가 **그 뒤 수백 개 단락에 전파된다.**

실제 증상:

| 생략한 속성 | 증상 |
|---|---|
| `alignment` | 조·항·호 본문이 전부 **가운데 정렬**로 나온다. 사용자가 가장 먼저 지적하는 문제 |
| `page_break_before` | 문단마다 쪽이 넘어가 **35쪽 문서가 153쪽**이 된다 |
| `indent_left_mm` / `first_line_indent_mm` | 들여쓰기가 엉뚱한 문단에 붙는다 |
| `spacing_before_pt` / `spacing_after_pt` | 문단 간격이 제멋대로 벌어진다 |

**해결 — 단일 진입점에서 전부 명시한다.**

```python
def _p(self, text='', style='body', align=None, before=None, after=None,
       left=None, first=None, page_break=False, line=160):
    """모든 서식 속성을 항상 명시적으로 전달한다.
    생략하면 앞서 만든 paraPr(가운데 정렬·페이지나눔 등)이 뒤 단락으로 전파된다."""
    para = self.d.add_paragraph(text, char_pr_id_ref=self.st[style])
    self.d.set_paragraph_format(
        paragraph_index=len(self.d.paragraphs) - 1,
        line_spacing_percent=line,
        alignment=align or 'LEFT',                       # ← None 금지
        spacing_before_pt=0 if before is None else before,
        spacing_after_pt=0 if after is None else after,
        indent_left_mm=0 if left is None else left,
        first_line_indent_mm=0 if first is None else first,
        page_break_before=bool(page_break),              # ← 항상 True/False
    )
    return para
```

**검증 — 저장 후 정렬·페이지나눔 분포를 반드시 세어 본다.**

```python
import zipfile, collections
from lxml import etree
H = '{http://www.hancom.co.kr/hwpml/2011/head}'
P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'

z = zipfile.ZipFile('out.hwpx')
hr = etree.fromstring(z.read('Contents/header.xml'))
al = {pp.get('id'): pp.find(H + 'align').get('horizontal')
      for pp in hr.iter(H + 'paraPr') if pp.find(H + 'align') is not None}
sec = etree.fromstring(z.read('Contents/section0.xml'))

print(collections.Counter(al.get(p.get('paraPrIDRef')) for p in sec.iter(P + 'p')))
for p in sec.iter(P + 'p'):                      # 가운데 정렬 단락을 눈으로 확인
    if al.get(p.get('paraPrIDRef')) == 'CENTER':
        t = ''.join(x.text or '' for x in p.iter(P + 't')).strip()
        if t:
            print('CENTER:', t[:50])
```

가운데 정렬로 남아야 할 것은 **표지 제목·장 제목·부칙 정도**다. 조문 본문이 목록에 섞여 있으면 R5를 어긴 것이다. 페이지나눔(`breakSetting @pageBreakBefore`)도 같은 방식으로 세어, 장 제목과 별표·별지 수의 합과 일치하는지 확인한다.

## 🆕 R6. 단락 id는 정리해 두되, **중복 자체를 오류로 보지 않는다**

`new()`로 만든 문서는 단락 id를 난수로 부여해 **문서당 2~3개꼴로 중복이 발생한다.** 한글이 "파일을 읽거나 저장하는데 오류가 있습니다"로 거부하는 원인이다.

**중복 자체는 오류가 아니다.** 한글 원본도 id를 대량 재사용하므로 `verify_hwpx.py` 검사 6번은 고유·중복 건수를 진단 정보로만 낸다(FAIL 아님). 다만 `<hp:p>`를 복제해 셀·단락을 늘렸다면 복제본에 새 id를 주는 편이 깔끔하다. 무해하므로 아래 함수를 `save()`에 기본 적용해도 된다.

> 파일이 안 열리면 id가 아니라 **R4(표 병합) → R2(mimetype) → XML 이스케이프** 순으로 의심할 것.

```python
def dedupe_ids(path):
    """저장 후 <hp:p id> 중복 제거. mimetype-first + STORED 규약(R2)을 지켜 재패키징한다."""
    import zipfile, os
    from lxml import etree
    P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
    tmp, seen, nxt, fixed = path + '.tmp', set(), [900000000], 0
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w') as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith('Contents/') and item.filename.endswith('.xml'):
                root = etree.fromstring(data)
                for p in root.iter(P + 'p'):
                    pid = p.get('id')
                    if pid is None:
                        continue
                    if pid in seen:
                        nxt[0] += 1
                        p.set('id', str(nxt[0]))
                        fixed += 1
                    else:
                        seen.add(pid)
                data = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
                        + etree.tostring(root, encoding='utf-8'))
            zi = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            zi.compress_type = (zipfile.ZIP_STORED if item.filename == 'mimetype'
                                else zipfile.ZIP_DEFLATED)
            zi.external_attr = item.external_attr
            zout.writestr(zi, data)
    os.replace(tmp, path)
    return fixed
```

> 구버전(v1.2 이하) `verify_hwpx.py`를 쓰고 있다면 검출조차 되지 않으므로 이 보정이 필수다.

## 🆕 R7. `set_page_setup`에 `orientation`을 주지 않는다

OWPML의 `<hp:pagePr @landscape>`는 `WIDELY` / `NARROWLY`만 허용한다. `orientation='portrait'`를 주면 **`landscape="PORTRAIT"`라는 비표준 값**이 들어간다.

실제 한글이 만든 A4 세로 문서는 `landscape="WIDELY"` + `width=59528 height=84188`(210×297mm)로 저장한다. 즉 **한글은 방향을 폭·높이로 판단한다.** 따라서 `orientation`은 생략하고 용지 크기와 여백만 지정한다.

```python
d.set_page_setup(paper_size='A4',
                 margins_mm={'left': 22, 'right': 22, 'top': 20, 'bottom': 18,
                             'header': 12, 'footer': 12})
```

## 🆕 R8. 눈으로 볼 수 없다 — LibreOffice는 HWPX를 못 읽는다

`soffice --headless --convert-to pdf out.hwpx`는 **"source file could not be loaded"로 실패한다.** `.hwp`로 변환해도 마찬가지다. 즉 **생성한 HWPX는 렌더링해서 확인할 수 없다.** 대신 다음으로 대체한다.

```bash
# 1) 기본 검증 (v1.3은 표 병합 정합성까지 FAIL로 잡는다)
python "$SKILL_DIR/scripts/verify_hwpx.py" out.hwpx

# 2) 한글 파서 왕복 — 구조가 실제로 읽히는지 확인
node ./_bridge/hwp_bridge.mjs to-hwp out.hwpx /tmp/check.hwp
#    contentLoss.count == 0 / recovered == true / pageCount가 상식적인지 확인
```

```python
# 3) 정렬·페이지나눔 분포 (R5의 검증 코드) — verify_hwpx.py가 보지 않는 영역
# 4) 본문 통독
from hwpx.document import HwpxDocument
print(HwpxDocument.open('out.hwpx').export_text()[:2000])
```

> **쪽수는 가장 민감한 이상 신호다.** 글자 15,000자짜리 규정이 150쪽으로 나오면 R5(페이지나눔 전파)를 의심한다. 대략 **A4 한 쪽에 한글 900~1,200자**가 들어간다고 보면 된다.

## 🆕 R9. 표 색과 정렬의 기본 규약

사용자가 별도로 지정하지 않으면 다음을 기본값으로 한다. 한국 실무 문서에서 가장 무난하고, "머리행이 너무 진하다" / "본문이 왜 가운데냐"는 재작업 요구를 막아 준다.

| 요소 | 기본값 | 이유 |
|---|---|---|
| 표 머리행 배경 | **아주 연한 색** `#E9EEF6` | 짙은 남색(`#1F3864`) 바탕에 흰 글씨는 인쇄 시 잉크를 많이 먹고 답답해 보인다 |
| 표 머리행 글자 | 진한 남색 `#1F3864` 굵게 | 연한 바탕에는 진한 글자 |
| 라벨 칸(문서정보·결재란) | `#F4F6F9` | 머리행보다 더 연하게 |
| **표 1행(머리행) 텍스트** | **가운데 정렬** | 항목명이므로 |
| **표 2행 이후 내용** | **왼쪽 정렬** | 본문이므로 |
| 1행짜리 서식 줄(라벨·값) | 라벨·값 모두 가운데 | 서식 기입란은 가운데가 자연스럽다 |
| 본문 조·항·호 | 왼쪽 정렬 | **가운데 정렬은 제목에만 쓴다** |
| 가운데 정렬 허용 | 표지 제목, 장 제목, 부칙, 박스 제목 | 그 외에는 쓰지 않는다 |
| 본문 글꼴 | `함초롬바탕` 10.5pt | 한글 기본 탑재 글꼴 |
| 제목·표 글꼴 | `함초롬돋움` | 본문과 구분 |

**표 셀 정렬은 셀 단락의 `paraPrIDRef`를 직접 바꿔야 한다.** `set_cell_text`는 기본 paraPr(JUSTIFY)를 쓰므로, 셀 전용 paraPr를 좌·중앙 2종 미리 만들어 두고 갈아끼운다.

```python
# __init__에서 셀 전용 paraPr 2종을 미리 확보한다
def _make_cell_para_pr(d, alignment):
    tmp = d.add_paragraph('')
    d.set_paragraph_format(paragraph_index=len(d.paragraphs) - 1,
                           alignment=alignment, line_spacing_percent=140,
                           spacing_before_pt=0, spacing_after_pt=0,
                           indent_left_mm=0, first_line_indent_mm=0,
                           page_break_before=False)
    ref = tmp.element.get('paraPrIDRef')
    d.remove_paragraph(tmp)
    return ref

self.cell_left   = _make_cell_para_pr(d, 'LEFT')
self.cell_center = _make_cell_para_pr(d, 'CENTER')

# 셀에 글자 서식 + 정렬을 함께 입힌다
def style_cell(self, cell, char_style, center=False):
    if cell is None:
        return
    ref = self.cell_center if center else self.cell_left
    for p in cell.paragraphs:
        p.element.set('paraPrIDRef', ref)
        for run in p.element.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}run'):
            run.set('charPrIDRef', char_style)

# 표 전체에 적용 — 1행만 가운데
for ri in range(t.row_count):
    for ci in range(t.column_count):
        head = has_header and ri == 0
        self.style_cell(t.cell(ri, ci), self.st['th'] if head else self.st['td'], center=head)
```

배경색은 `t.set_cell_shading(row, col, '#E9EEF6')`으로 지정하고, 열 너비는 `t.set_column_widths([...])`에 HWPUNIT(1mm = 283.465)으로 준다. A4 좌우 여백 22mm 기준 본문 폭은 166mm다. 색 적용 여부는 `header.xml`의 `faceColor` 값으로 확인한다.

## C-2. 조문형 문서의 표준 구성

규정·지침·매뉴얼은 다음 순서를 따르면 사내 결재에 그대로 올릴 수 있다.

```
표지 제목 + 문서번호
■ 문서 정보    (문서명·문서번호·제정일·목적·주관·승인권자·보존기간·배포처)
■ 결 재        (작성 / 검토 / 승인 — 서명란 공백 2줄)
■ 개정 이력    (개정번호·개정일자·개정내용·작성자·승인자)
제 1 장  총칙   (목적 / 적용범위 / 용어의 정의 / 다른 규정과의 관계)
제 2 장 ~       (본문 — 각 장은 새 쪽에서 시작)
부      칙      (시행일 / 경과조치 / 다른 규정과의 관계)
[별표 N] ~      (기준표·목록 — 새 쪽)
[별지 제N호 서식] ~  (기입 서식 — 새 쪽)
```

- 조문은 `제N조(제목)`을 굵은 고딕 한 줄로 두고, 그 아래 `①②③` → `1. 2. 3.` → `가. 나. 다.` 순으로 계층을 내려간다. 계층마다 내어쓰기(`first_line_indent_mm` 음수)를 준다.
- 머리글에 `문서명 (문서번호)`, 바닥글에 `작성일 | 버전 | 회사명 (대외비)` + 쪽번호를 넣는다.
- 법령을 인용할 때는 **작업 시점에 원문을 확인한다.** 조문 번호와 호수는 개정으로 자주 바뀐다.
- 확정되지 않은 값(금액 한도, 비율, 인원, 담당자)은 **`【확인필요】` 같은 눈에 띄는 표시**를 본문에 남기고, 문서 앞부분에 그 표기 규칙을 안내한다. 빈칸으로 두면 검토자가 놓친다.

## C-3. 저장 파이프라인

```python
def save(self, path):
    self.d.save_to_path(path)
    dedupe_ids(path)                                             # R6
    subprocess.run([sys.executable, f'{SKILL}/scripts/fix_namespaces.py', path], check=True)
    subprocess.run([sys.executable, f'{SKILL}/scripts/clear_layout_cache.py', path], check=True)  # R1
    r = subprocess.run([sys.executable, f'{SKILL}/scripts/verify_hwpx.py', path],
                       capture_output=True, text=True)           # R3
    print(r.stdout)
    if 'PASS' not in r.stdout:
        raise SystemExit(f'검증 실패: {path}')
```

이후 R8의 왕복 검증과 정렬·쪽수 확인을 거쳐 전달한다.

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

검사 항목(v1.3 기준):

| # | 항목 | 놓치면 |
|---|---|---|
| 1 | mimetype 규약 | 한글이 파일을 못 엶 |
| 2 | 필수 파트 | 한글이 파일을 못 엶 |
| 3 | XML well-formed | 한글이 파일을 못 엶 |
| 4 | linesegarray 잔존 | 글씨 겹침 |
| 5 | **표 병합(rowSpan/colSpan) 정합성** ★신설 | **한글이 파일을 못 엶** |
| 6 | **단락 id 분포** ★신설 | — (진단 정보, FAIL 아님) |
| 7 | 이미지 참조 무결성 | 그림 깨짐 |
| 8 | 단락·이미지·글자 수 통계 | — |

`--base`를 주면 원본 대비 글자 수 증감을 보고한다.

**PASS + 캐시 잔존 0**을 확인한 뒤에 사용자에게 전달한다.

> ### 이 스크립트도 검사하지 **않는** 것
>
> | 항목 | 확인 방법 |
> |---|---|
> | **정렬·페이지나눔 속성 전파** | **R5의 분포 검증** — 본문이 가운데로 밀렸는지, 쪽수가 부풀었는지 |
> | XML 선언 형태 변화 | 원본과 동일한 선언을 붙였는지 확인 |
> | HWP5 역변환 어댑터의 자체 실패 | `.hwpx`도 함께 전달해 사용자가 대조 |
> | 실제 한글 앱에서의 열림 여부 | **R8의 HWP 역변환 왕복** + 최종 확인은 사용자가 한글에서 연다 |
>
> **구버전(v1.2 이하) `verify_hwpx.py`를 쓰고 있다면 5·6번을 직접 확인해야 한다.**

---

## Quick Reference

| 작업 | 접근 방식 |
|------|----------|
| **`.hwp` 파일을 받았을 때** | **0-A단계 — `hwp_bridge.mjs to-hwpx`로 변환 후 진행** |
| **`.hwp`로 돌려줘야 할 때** | **`hwp_bridge.mjs to-hwp` + `verify` 쪽수 확인** |
| 보고서/공문/양식 문서 생성 | **양식 파일 + ZIP-level 치환** (★ 권장) |
| **기존 원고 수정·증보** | **`references/edit-existing.md` 절차** |
| **양식 없이 규정·매뉴얼 생성** | **C 워크플로 + R5~R9** |
| 표(테이블) 추가 | `d.add_table(rows, cols)` → `set_cell_text()` → `style_cell()` (R9) |
| **표의 빈 행 삭제** | **R4 — rowSpan 보정 + verify 검사 5번 통과 필수** |
| 머리글/바닥글/쪽번호 | `d.set_header_text()` / `d.set_footer_text()` / `d.set_page_number()` |
| 텍스트 검색/추출 | `ObjectFinder(filepath)` |
| 셀 병합 | `table.merge_cells(row1, col1, row2, col2)` |
| 글씨 겹침 발생 | `clear_layout_cache.py` |
| **본문이 전부 가운데 정렬로 나옴** | **R5 — `set_paragraph_format` 인자 생략 여부 확인** |
| **쪽수가 비정상적으로 많음** | **R5 — `page_break_before` 전파 확인** |
| **한글이 "파일을 읽거나 저장하는데 오류"** | **아래 트러블슈팅 표** |
| 전달 전 최종 확인 | `verify_hwpx.py --base 원본` |

---

## 트러블슈팅 — 한글이 파일을 못 열 때

> 증상: **"파일을 읽거나 저장하는데 오류가 있습니다."** 대화상자

의심 순서대로 확인한다.

| # | 원인 | 확인·조치 |
|---|---|---|
| 1 | **표 병합 정합성 깨짐** (행·열을 지웠는데 span 미보정) | `verify_hwpx.py` 검사 5번 → 보고된 셀의 `rowSpan` 보정 (**R4**) |
| 2 | ~~단락 id 중복~~ — **원인이 아니다** (v1.4.1 정정) | 한글 원본도 id를 재사용한다. 다음 항목으로 넘어갈 것 |
| 3 | mimetype이 압축됨 / 첫 항목이 아님 | **R2** 규약대로 재패키징 |
| 4 | XML not well-formed (이스케이프 누락) | `&`, `<`, `>` 이스케이프 확인 |
| 5 | 네임스페이스 프리픽스 변형 | `fix_namespaces.py` 실행 |
| 6 | HWPX→HWP 역변환 자체 실패 | `.hwpx`를 전달하고 사용자가 한글에서 "다른 이름으로 저장"하도록 안내 |

**즉시 조치**: 원인 규명 전이라도 `.hwpx`를 먼저 전달한다. 한글 2010 이상은 `.hwpx`를 그대로 열며, 사용자는 거기서 `.hwp`로 저장할 수 있다. **사용자를 기다리게 하지 않는 것이 우선이다.**

---

## 주의사항

1. **작업 유형 판별이 먼저**: A(양식 치환)·B(기존 편집)·C(신규 생성)를 혼동하지 않는다
2. **양식 우선**: 사용자 업로드 양식 > 기본 제공 양식 > C 워크플로
3. **ZIP-level 치환 우선**: `HwpxDocument.open()`보다 안전하고 호환성이 높다
4. **양식 텍스트 조사 필수**: 치환 전에 반드시 ObjectFinder로 전수 조사
5. **표를 건드릴 거면 표 구조부터 조사**: `rowSpan`이 2 이상인 셀 위치를 먼저 파악한다 (R4)
6. **순차 치환 주의**: 동일 플레이스홀더가 여러 번 나오면 `zip_replace_sequential`
7. **치환 실패를 조용히 넘기지 않는다**: run 분할 때문에 문장 전체 매칭은 자주 실패한다. `assert`로 드러낼 것
8. **XML 이스케이프**: 본문에 넣는 텍스트의 `&`, `<`, `>`를 반드시 이스케이프
9. **레이아웃 캐시 제거 필수**: 텍스트를 바꿨으면 표/본문 가리지 말고 실행. 안 하면 글씨 겹침
10. **셀 높이는 추정 금지**: 캐시만 지우면 한글이 자동으로 맞춘다
11. **재패키징 규약**: mimetype은 첫 항목 + 무압축(ZIP_STORED)
12. **행 삭제 시 병합 보정 필수**: `rowSpan`·`rowCnt`를 맞추고 검증으로 확인 (R4). 애매하면 빈 행으로 남긴다
13. **`set_paragraph_format`은 모든 속성 명시** (R5) — C 워크플로 최대의 함정. 생략하면 가운데 정렬·페이지나눔이 뒤 단락으로 전파된다. **검증 스크립트가 잡지 못하는 영역이다**
14. **단락 id 중복은 오류가 아니다** (R6) — 한글 원본도 id를 재사용한다. `dedupe_ids`는 복제 단락을 정리하는 안전장치일 뿐이고, 검사 6번은 FAIL을 내지 않는다
15. **`set_page_setup`에 `orientation` 인자 사용 금지** (R7) — 비표준 `landscape="PORTRAIT"`가 들어간다
16. **표 색은 연하게, 1행은 가운데, 나머지는 왼쪽** (R9). 짙은 남색 머리행 + 흰 글씨는 쓰지 않는다
17. **LibreOffice로 HWPX/HWP를 렌더링할 수 없다** (R8). 눈으로 보는 대신 검증 스크립트·텍스트 추출·HWP 역변환 왕복으로 확인한다
18. **검증 통과 ≠ 열린다**: `contentLoss: 0`과 `recovered: true`는 구조 무결성을 보장하지 않는다
19. **표 구조를 바꿨으면 `.hwp` + `.hwpx` 동시 전달**: 사용자가 즉시 대안을 열 수 있게 한다
20. **전달 전 검증 필수**: `verify_hwpx.py` PASS 없이는 파일을 보내지 않는다
21. **레이아웃 충실도**: python-hwpx는 레이아웃 엔진이 아님. 페이지 나눔은 한글 앱이 결정
22. **글꼴 임베딩**: 생성 HWPX에 글꼴 미포함. 열람 환경에 해당 글꼴 필요. 기본은 `함초롬바탕`(본문)·`함초롬돋움`(제목·표)
23. **공문서 날짜 형식**: `2026-02-13`이 아닌 `2026. 2. 13.` (월·일 앞 0 생략)
24. **HWPX ↔ HWP**: python-hwpx는 HWPX만 처리한다. 레거시 `.hwp`는 **0-A단계의 `@rhwp/core` 변환기**(npm 라이브러리, 별도 스킬 아님)로 앞뒤에서 감싼다(사용자에게 수동 변환을 요구하지 않는다)
25. **왕복은 1회**: `.hwp` → `.hwpx` → 편집 → `.hwp`. 편집 중간에 형식을 오가지 않는다
26. **변환 손실 보고 필수**: `contentLoss.count > 0`이면 항목을 사용자에게 알리고 진행 여부를 묻는다
27. **fix_namespaces 호출법**: `exec()` 말고 `subprocess.run()` 사용
28. **범위 밖 요청 처리**: 누름틀 자동 채우기·메일머지 요청이 오면 **다른 스킬 설치를 안내하지 않는다.** 이 스킬 범위 밖임을 한 줄로 알리고, 대신 가능한 방법(해당 텍스트를 ZIP-level 치환으로 직접 바꾸기)을 제시한다

---

작성일: 2026-09-05 | 버전: v1.4.1
