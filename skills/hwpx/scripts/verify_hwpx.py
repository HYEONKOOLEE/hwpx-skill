#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_hwpx.py — HWPX 산출물 무결성 검사 (사용자에게 전달하기 전 마지막 관문)

검사 항목
---------
1. ZIP 구조      : mimetype이 첫 항목이고 무압축(STORED)인가
2. 필수 파트     : mimetype / version.xml / META-INF/container.xml / Contents/*.xml
3. XML 유효성    : 모든 XML 파트가 well-formed인가
4. 레이아웃 캐시 : linesegarray 잔존 개수(텍스트를 편집했다면 0이어야 함)
5. 이미지 무결성 : content.hpf에 등록된 BinData 항목이 실제로 존재하는가
6. 본문 통계     : 단락 수 / 이미지 수 / 추출 글자 수

원본과 비교하려면 --base 로 편집 전 파일을 함께 준다. 텍스트 diff 요약을 낸다.

사용법
------
  python verify_hwpx.py <out.hwpx>
  python verify_hwpx.py <out.hwpx> --base <before.hwpx>
  python verify_hwpx.py <out.hwpx> --dump-text out.txt
"""
import html
import os
import re
import sys
import zipfile
import xml.dom.minidom as minidom

REQUIRED = ["mimetype", "version.xml", "META-INF/container.xml"]


def sections(z):
    return sorted(n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n))


def extract_text(z):
    out = []
    for n in sections(z):
        s = z.read(n).decode("utf-8").replace("</hp:p>", "\n")
        out.append(html.unescape(re.sub(r"<[^>]+>", "", s)))
    return "\n".join(out)


def check(path, base=None, dump=None):
    ok = True
    def bad(msg):
        nonlocal ok
        ok = False
        print("  ✗ " + msg)

    print(f"■ {os.path.basename(path)}")
    with zipfile.ZipFile(path) as z:
        names = z.namelist()

        # 1. mimetype 규약
        if not names:
            bad("빈 ZIP")
        elif names[0] != "mimetype":
            bad(f"mimetype이 첫 항목이 아님 (현재 첫 항목: {names[0]})")
        elif z.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
            bad("mimetype이 압축돼 있음 (ZIP_STORED여야 함)")
        else:
            mt = z.read("mimetype").decode().strip()
            if mt != "application/hwp+zip":
                bad(f"mimetype 값 이상: {mt!r}")
            else:
                print("  ✓ ZIP 규약 (mimetype first / stored)")

        # 2. 필수 파트
        missing = [r for r in REQUIRED if r not in names]
        if missing:
            bad(f"필수 파트 누락: {missing}")
        if not sections(z):
            bad("Contents/section*.xml 없음")
        if not missing and sections(z):
            print(f"  ✓ 필수 파트 ({len(sections(z))}개 섹션)")

        # 3. XML well-formed
        broken = []
        for n in names:
            if n.endswith(".xml") or n.endswith(".hpf"):
                try:
                    minidom.parseString(z.read(n))
                except Exception as e:
                    broken.append(f"{n}: {e}")
        if broken:
            bad("XML 파싱 실패:\n     " + "\n     ".join(broken))
        else:
            print("  ✓ XML well-formed")

        # 4. 레이아웃 캐시
        lsa = sum(len(re.findall(r"<\w*:?linesegarray\b", z.read(n).decode("utf-8")))
                  for n in names if n.startswith("Contents/") and n.endswith(".xml"))
        if lsa:
            print(f"  ⚠ linesegarray {lsa}개 잔존 — 텍스트를 편집했다면 "
                  f"clear_layout_cache.py를 실행할 것 (글씨 겹침 원인)")
        else:
            print("  ✓ 레이아웃 캐시 없음 (한글이 줄 위치 재계산)")

        # 5. 이미지 참조 무결성
        if "Contents/content.hpf" in names:
            hpf = z.read("Contents/content.hpf").decode("utf-8")
            refs = re.findall(r'href="(BinData/[^"]+)"', hpf)
            lost = [r for r in refs if r not in names]
            if lost:
                bad(f"content.hpf가 참조하는 파일 없음: {lost}")
            elif refs:
                print(f"  ✓ 이미지 참조 {len(refs)}건 모두 존재")

        # 6. 통계
        body = "".join(z.read(n).decode("utf-8") for n in sections(z))
        text = extract_text(z)
        print(f"  · 단락 {len(re.findall(r'<hp:p ', body))} / "
              f"이미지 {len(re.findall(r'<hp:pic', body))} / "
              f"글자 {len(re.sub(chr(92) + 's', '', text))}")

        if dump:
            open(dump, "w", encoding="utf-8").write(text)
            print(f"  · 본문 텍스트 저장: {dump}")

        if base:
            with zipfile.ZipFile(base) as zb:
                b = re.sub(r"\s", "", extract_text(zb))
            a = re.sub(r"\s", "", text)
            if a == b:
                print("  · 원본 대비 텍스트 변화 없음")
            else:
                print(f"  · 원본 대비 글자 수 {len(b)} → {len(a)} ({len(a)-len(b):+d})")
                if len(a) < len(b):
                    print("    ⚠ 글자가 줄었다. 의도한 삭제인지 확인할 것.")

    print("  →", "PASS" if ok else "FAIL")
    return ok


def main():
    argv = sys.argv[1:]
    if not argv:
        print("사용법: python verify_hwpx.py <out.hwpx> [--base before.hwpx] [--dump-text out.txt]")
        sys.exit(1)
    path = argv[0]
    base = argv[argv.index("--base") + 1] if "--base" in argv else None
    dump = argv[argv.index("--dump-text") + 1] if "--dump-text" in argv else None
    sys.exit(0 if check(path, base, dump) else 1)


if __name__ == "__main__":
    main()
