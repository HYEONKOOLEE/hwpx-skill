#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anonymize_hwpx.py — 실전 HWPX 문서를 "구조는 그대로, 내용은 소거"한 회귀 테스트용 샘플로 만든다.

왜 필요한가
-----------
회귀 테스트(evals)에 필요한 것은 문서의 *구조*다 — 표 개수·병합 형태, 단락 수,
단락 id 분포, 이미지 참조, linesegarray. 그러나 실전 문서는 기관명·이름·연락처 같은
내용을 담고 있어 그대로 저장소에 올릴 수 없다. 이 스크립트는 글자를 전부 바꾸되
글자 수·문자 종류(한글/숫자/영문/기호/공백)는 유지해서, 한글이 계산하는 줄바꿈과
verify_hwpx.py의 모든 검사 결과가 원본과 같게 나오도록 한다.

무엇을 바꾸나
-------------
  Contents/section*.xml   <hp:t> 텍스트(자식 요소 tail 포함)를 글자 단위로 치환
                          - 한글 음절  → 다른 한글 음절 (고정 시드의 난수, 재현 가능)
                          - 숫자       → 다른 숫자
                          - 영문       → 같은 대소문자의 다른 영문
                          - 공백·문장부호·기호(□ ◦ Ⅲ 등)·한자 외 기타 → 그대로
  Contents/content.hpf    제목·작성자·최종저장자 메타데이터를 익명 값으로
  Preview/PrvText.txt     동일 규칙으로 치환(미리보기 텍스트)
  Preview/PrvImage.png    같은 크기의 단색 회색 이미지로 교체(미리보기 썸네일)
  BinData/*               같은 형식·크기의 단색 회색 이미지로 교체(로고·사진 소거)

무엇을 보존하나
---------------
  표 구조(tbl/tr/tc, cellAddr/cellSpan), paraPrIDRef/charPrIDRef, <hp:p id>,
  linesegarray, 이미지 참조(binaryItemIDRef), header.xml(글꼴·스타일 이름만 있음),
  ZIP 항목 순서, mimetype-first + STORED 규약(R2)

사용법
------
  python anonymize_hwpx.py <원본.hwpx> <출력.hwpx> [--seed 20260905]
  python anonymize_hwpx.py <원본.hwpx> <출력.hwpx> --check   # 원본 한글 단어 잔존 여부까지 검사

주의
----
  header.xml은 건드리지 않는다(글꼴·스타일 이름은 내용이 아니다). 실행 후 출력되는
  "[남은 한글]" 목록을 반드시 눈으로 확인하고, 사람이 최종 검토한 뒤에만 저장소에 넣는다.
"""
import io
import random
import re
import struct
import sys
import zipfile
import zlib
from xml.etree import ElementTree as ET

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
T_TAG = "{%s}t" % HP
HANGUL = re.compile(r"[가-힣]")
HANGUL_WORD = re.compile(r"[가-힣]{2,}")

# 치환에 쓸 한글 음절 풀 — 받침 있는/없는 글자를 섞어 원본과 비슷한 폭 분포를 만든다
SYLLABLES = list("가나다라마바사아자차카타파하거너더러머버서어저처커터퍼허"
                 "고노도로모보소오조초코토포호구누두루무부수우주추쿠투푸후"
                 "기니디리미비시이지치키티피히각난달람밥상앙장창칵탄팔함"
                 "건널덤렬멈법선업정천컴털펌헐곡논돌롬몸복송옹종총콕톤폴홈")


class Anonymizer:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.cache = {}   # 같은 글자는 항상 같은 글자로 — 반복 패턴(예: 같은 표제어)을 보존해 구조 비교가 쉬움

    def ch(self, c):
        if c in self.cache:
            return self.cache[c]
        if "가" <= c <= "힣":
            r = self.rng.choice(SYLLABLES)
        elif c.isdigit() and c.isascii():
            r = str(self.rng.randint(0, 9))
        elif "a" <= c <= "z":
            r = chr(self.rng.randint(97, 122))
        elif "A" <= c <= "Z":
            r = chr(self.rng.randint(65, 90))
        elif "一" <= c <= "鿿":            # 한자 → 임의 한자
            r = chr(self.rng.randint(0x4e00, 0x9fa5))
        else:
            r = c                                   # 공백·부호·기호·전각문자 등은 유지
        self.cache[c] = r
        return r

    def text(self, s):
        return "".join(self.ch(c) for c in s) if s else s


def anonymize_section(xml_bytes, anon):
    """<hp:t> 안의 텍스트(자식 tail 포함)만 치환. 그 외 XML은 바이트 단위로 보존하기 위해
    문자열 치환 방식으로 처리한다(ElementTree 재직렬화는 네임스페이스 접두어를 바꾸므로 피한다)."""
    s = xml_bytes.decode("utf-8")
    out = []
    pos = 0
    # <hp:t ...>...</hp:t> 블록을 찾아 내부 텍스트 노드만 치환 (태그·엔티티는 유지)
    for m in re.finditer(r"<hp:t(?:\s[^>]*)?>(.*?)</hp:t>", s, flags=re.S):
        out.append(s[pos:m.start(1)])
        inner = m.group(1)
        # 내부의 자식 태그(<hp:tab/>, <hp:lineBreak/> 등)는 유지하고 텍스트 조각만 치환
        parts = re.split(r"(<[^>]+>)", inner)
        for i, part in enumerate(parts):
            if i % 2 == 1:                          # 태그
                out.append(part)
            else:                                   # 텍스트(엔티티 포함 가능)
                pieces = re.split(r"(&[#\w]+;)", part)
                for j, piece in enumerate(pieces):
                    out.append(piece if j % 2 == 1 else anon.text(piece))
        pos = m.end(1)
    out.append(s[pos:])
    s = "".join(out)

    # 그림 설명(<hp:shapeComment>) — 한글이 자동으로 "원본 그림의 이름: 로고.jpg / 사진 찍은 날짜: …"를
    # 넣어 두는 곳이라 파일명·촬영일이 새어 나간다. 요소는 남기고 내용을 치환.
    # 글자 수를 유지하도록 고정 문구가 아니라 글자 단위 치환(한글·영문·숫자 모두)을 적용한다 →
    # verify_hwpx.py의 글자 수까지 원본과 동일하게 맞춰진다.
    s = re.sub(r"(<hp:shapeComment>)(.*?)(</hp:shapeComment>)",
               lambda m: m.group(1) + anon.text(m.group(2)) + m.group(3), s, flags=re.S)

    # 그 밖에 <hp:t> 바깥에 남은 한글(누름틀 안내문, 책갈피 이름, 하이퍼링크 표시문 등)을 요소 텍스트·속성값
    # 가리지 않고 글자 단위로 치환한다. 태그 이름·속성 이름은 ASCII이므로 영향 없음.
    # (<hp:t> 안 텍스트는 한 번 더 치환되지만 글자 종류·수가 유지되므로 무해)
    s = re.sub(r"[가-힣]+", lambda m: anon.text(m.group(0)), s)
    return s.encode("utf-8")


def anonymize_hpf(xml_bytes):
    s = xml_bytes.decode("utf-8")
    s = re.sub(r"<opf:title>.*?</opf:title>", "<opf:title>anonymized-sample</opf:title>", s, flags=re.S)
    for key in ("creator", "lastsaveby"):
        s = re.sub(r'(<opf:meta name="%s"[^>]*>)(.*?)(</opf:meta>)' % key, r"\1anon\3", s, flags=re.S)
    s = re.sub(r'(<opf:meta name="date"[^>]*>)(.*?)(</opf:meta>)', r"\1\3", s, flags=re.S)
    return s.encode("utf-8")


# ---- 이미지 교체: PIL 있으면 사용, 없으면 PNG/BMP는 직접 생성 --------------------------
def gray_image_like(data, name):
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        fmt = im.format
        w, h = im.size
        mode = "RGBA" if fmt in ("PNG", "BMP") and im.mode == "RGBA" else "RGB"
        g = Image.new(mode, (w, h), (200, 200, 200, 255) if mode == "RGBA" else (200, 200, 200))
        buf = io.BytesIO()
        g.save(buf, format=fmt)
        return buf.getvalue(), (fmt, w, h)
    except Exception:
        pass
    # PIL 불가: 최소한 PNG는 손으로 만든다(크기는 원본 헤더에서 읽음)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
        return _png_gray(w, h), ("PNG", w, h)
    return data, ("원본 유지(교체 실패)", None, None)


def _png_gray(w, h):
    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xffffffff)
    raw = b"".join(b"\x00" + b"\xc8" * w for _ in range(h))       # grayscale 8bit
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__); sys.exit(2)
    src, dst = args
    seed = 20260905
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    check = "--check" in sys.argv
    anon = Anonymizer(seed)

    orig_words = set()
    report = []
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        names = zin.namelist()
        assert names[0] == "mimetype", "mimetype이 첫 항목이 아님 — 원본이 규약 위반"
        for info in zin.infolist():
            data = zin.read(info.filename)
            n = info.filename
            if n == "mimetype":
                zout.writestr(info, data, compress_type=zipfile.ZIP_STORED)   # R2
                continue
            if n.startswith("Contents/section") and n.endswith(".xml"):
                if check:   # 원본의 모든 한글 단어(2자 이상) — <hp:t> 밖(그림 설명 등)까지 포함
                    orig_words |= set(HANGUL_WORD.findall(data.decode("utf-8")))
                new = anonymize_section(data, anon)
                report.append(f"{n}: <hp:t> 텍스트 치환 ({len(HANGUL.findall(data.decode('utf-8')))}자 한글)")
            elif n == "Contents/content.hpf":
                new = anonymize_hpf(data); report.append(f"{n}: 제목·작성자 메타데이터 익명화")
            elif n == "Preview/PrvText.txt":
                new = anon.text(data.decode("utf-8", "replace")).encode("utf-8"); report.append(f"{n}: 미리보기 텍스트 치환")
            elif n.startswith("Preview/") or n.startswith("BinData/"):
                new, (fmt, w, h) = gray_image_like(data, n)
                report.append(f"{n}: {fmt} {w}x{h} 단색 회색 이미지로 교체" if w else f"{n}: {fmt}")
            else:
                new = data
            zout.writestr(info, new, compress_type=zipfile.ZIP_DEFLATED)

    print(f"■ {src} → {dst}  (seed={seed})")
    for r in report:
        print("  ·", r)

    # 남은 한글 점검 — header.xml(글꼴·스타일명)과 치환 후 파일 전체를 보고
    with zipfile.ZipFile(dst) as z:
        leftover = {}
        for n in z.namelist():
            if n.endswith((".xml", ".hpf", ".txt", ".rdf")):
                txt = z.read(n).decode("utf-8", "replace")
                if n.startswith("Contents/section") or n == "Preview/PrvText.txt":
                    if check and orig_words:
                        hit = sorted(w for w in orig_words if w in txt)
                        print(f"  {'✗' if hit else '✓'} {n}: 원본 한글 단어(2자 이상) 잔존 {len(hit)}개" + (f" — 예: {hit[:5]}" if hit else ""))
                    continue
                words = sorted(set(HANGUL_WORD.findall(txt)))
                if words:
                    leftover[n] = words
        for n, words in leftover.items():
            print(f"  ⚠ [남은 한글] {n}: {len(words)}종 — {words[:12]}{' …' if len(words) > 12 else ''}")
            print("     (글꼴·스타일 이름이면 정상. 기관명·인명이 보이면 수동 처리 필요)")
    print("  → 완료. 사람이 한글에서 열어 최종 확인한 뒤 저장소에 넣을 것.")


if __name__ == "__main__":
    main()
