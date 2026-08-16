# 기존 HWPX 문서 편집 가이드 (원고 수정·증보)

> 사용자가 **이미 완성된 원고**(칼럼, 보고서, 논문 등)를 주면서
> "이 내용 수정해줘", "이 부분 추가해줘", "팩트체크 반영해줘"라고 요청하는 경우.
> 플레이스홀더를 채우는 템플릿 치환과는 **다른 작업**이다.

## 이 워크플로가 템플릿 치환과 다른 점

| | 템플릿 치환 | 기존 문서 편집 |
|---|---|---|
| 원본 텍스트 | 버릴 더미 | **지켜야 할 자산** |
| 텍스트 길이 | 대체로 비슷 | **크게 늘거나 줄어듦** |
| 서식 | 양식이 결정 | **원본 서식을 그대로 승계해야 함** |
| 최대 리스크 | 치환 누락 | **레이아웃 깨짐 · 내용 유실** |

---

## 절대 규칙 3가지

### 1. 텍스트를 건드렸으면 레이아웃 캐시를 지운다

한 글자만 바꿔도 마찬가지다. 표가 아니라 **본문 단락도 똑같이 겹친다.**
자세한 원리는 SKILL.md의 「필수 후처리 2」 참조.

```bash
python "$SKILL_DIR/scripts/clear_layout_cache.py" out.hwpx
```

### 2. 새로 만드는 단락에는 linesegarray를 넣지 않는다

기존 단락을 복사해 붙여넣는 방식으로 새 단락을 만들면 캐시까지 딸려 온다.
새 `<hp:p>`는 아래 최소 형태로 만든다. 캐시는 아예 없는 편이 안전하다.

```xml
<hp:p id="910000001" paraPrIDRef="0" styleIDRef="0"
      pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="17"><hp:t>본문 텍스트</hp:t></hp:run>
</hp:p>
```

`id`는 문서 내에서 겹치지 않는 정수면 된다(기존 값과 안 겹치게 큰 수부터 증가).

### 3. 원본 서식 ID를 조사해서 재사용한다

`paraPrIDRef` / `charPrIDRef`를 임의로 정하면 글꼴·크기가 튄다.
편집 전에 문서가 실제로 쓰는 ID를 뽑아서 표를 만든다.

```python
import re, html
s = open("Contents/section0.xml", encoding="utf-8").read()
for p in re.split(r"(?=<hp:p )", s):
    m = re.match(r'<hp:p id="([^"]*)" paraPrIDRef="(\d+)"', p)
    if not m:
        continue
    runs = sorted(set(re.findall(r'charPrIDRef="(\d+)"', p)))
    txt = html.unescape(re.sub(r"<[^>]+>", "", p)).strip()
    print(m.group(1), "pPr=" + m.group(2), "cPr=" + ",".join(runs), "|", txt[:50])
```

굵기·크기는 header.xml에서 확인한다.

```python
h = open("Contents/header.xml", encoding="utf-8").read()
for m in re.finditer(r'<hh:charPr id="(\d+)".*?</hh:charPr>', h, re.S):
    t = m.group(0)
    size = re.search(r'height="(\d+)"', t)
    print(m.group(1), "bold=", "<hh:bold" in t, "size=", int(size.group(1)) / 100 if size else "?")
```

이 결과로 **본문용 / 굵은 강조용 / 소제목용 / 캡션용** ID를 확정한 뒤 새 단락에 재사용한다.

---

## 표준 절차

```
[1] 원본을 작업 폴더에 복사 (원본 파일은 절대 덮어쓰지 않는다)
     ↓
[2] 압축 해제 → Contents/section0.xml 텍스트 추출해 전체 통독
     ↓
[3] 서식 ID 조사 (위 스크립트) → 본문/굵게/소제목/캡션 ID 확정
     ↓
[4] 편집 스크립트 작성 — 문자열 치환 + 단락 삽입
     ↓
[5] section0.xml 저장 → mimetype-first 규약으로 재패키징
     ↓
[6] 레이아웃 캐시 제거 (clear_layout_cache.py)   ★ 빠뜨리면 글씨 겹침
     ↓
[7] verify_hwpx.py --base 원본  → PASS 확인 후 전달
```

---

## 함정 1: 문장이 여러 run으로 쪼개져 있다

굵은 글씨나 색상이 섞인 문장은 하나의 `<hp:t>`가 아니다.

```xml
<hp:run charPrIDRef="11"><hp:t>여러 앱과 파일을 넘나들며 일을 </hp:t></hp:run>
<hp:run charPrIDRef="12"><hp:t>끝까지</hp:t></hp:run>
<hp:run charPrIDRef="11"><hp:t> 처리하는 것이 결정적 차이입니다.</hp:t></hp:run>
```

따라서 `"일을 끝까지 처리하는 것이 결정적 차이입니다."`로 치환을 시도하면 **실패한다.**

대처:
- **굵게 구간을 넘지 않는 부분 문자열**을 앵커로 잡는다 → `" 처리하는 것이 결정적 차이입니다."`
- 치환 함수에 `assert`를 넣어 실패를 조용히 넘기지 않는다

```python
def repl(old, new):
    global x
    assert esc(old) in x, "[MISS] " + old[:50]   # 조용한 실패 금지
    x = x.replace(esc(old), esc(new), 1)
```

## 함정 2: XML 이스케이프

본문에 넣는 텍스트는 `&`, `<`, `>`를 반드시 이스케이프한다.
치환 대상 문자열도 **이스케이프한 상태로** 찾아야 원본과 매칭된다.

```python
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
```

작은따옴표·큰따옴표는 한글 원고에서 대부분 둥근 따옴표(' ' " ")라 이스케이프 대상이 아니다.
복사·붙여넣기할 때 곧은 따옴표로 바뀌지 않게 주의한다.

## 함정 3: 재패키징에서 mimetype

수동으로 zip을 다시 만들 때 mimetype을 압축하면 한글이 파일을 열지 못한다.
**반드시 첫 항목 + 무압축(STORED).**

```bash
cd 압축푼폴더
zip -X -0 -q ../out.hwpx mimetype          # 무압축으로 먼저
zip -X -r -q ../out.hwpx . -x mimetype     # 나머지
```

파이썬이라면 `clear_layout_cache.py`의 재패키징 로직을 그대로 쓴다.

## 함정 4: 문단 사이 빈 줄

많은 한글 원고는 문단 간격을 `<hp:spacing>` 대신 **빈 단락**으로 만든다.
새 단락을 삽입할 때 앞뒤 빈 단락을 같이 넣지 않으면 문단이 붙어 보인다.
원본에서 문단 사이 패턴(본문 → 빈 단락 → 본문)을 확인하고 동일하게 재현한다.

## 함정 5: 이미지 캡션 번호

`[이미지 2]`처럼 번호가 붙은 캡션이 있는 문서에 새 이미지를 끼워 넣으면
뒤 번호를 전부 밀어야 한다. **뒤에서부터** 치환해야 충돌하지 않는다.

```python
repl("[이미지 4]", "[이미지 5]")   # 뒤에서부터
repl("[이미지 3]", "[이미지 4]")
repl("[이미지 2]", "[이미지 3]")
```

---

## 검증 체크리스트 (전달 직전)

- [ ] `verify_hwpx.py out.hwpx --base 원본.hwpx` → **PASS**
- [ ] linesegarray 잔존 **0개**
- [ ] 이미지 개수가 원본과 동일
- [ ] 글자 수 증감이 의도와 일치 (줄었다면 유실 여부 확인)
- [ ] 추출 텍스트를 눈으로 통독 — 문장이 중간에 잘리거나 중복되지 않았는가
- [ ] 삽입한 단락의 `charPrIDRef`가 본문용 ID와 같은가 (글꼴 튐 방지)

내용을 바꾸지 않은 리패키징이라면 텍스트가 **문자 단위로 동일**해야 한다.

```bash
diff <(tr -d ' \n' < before.txt) <(tr -d ' \n' < after.txt) && echo IDENTICAL
```
