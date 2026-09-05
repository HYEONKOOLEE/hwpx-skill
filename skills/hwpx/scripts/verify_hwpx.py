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
5. 표 구조       : 병합(rowSpan/colSpan) 범위가 표 밖으로 넘치지 않는가  ★ v1.3 신설
6. 단락 id 분포  : <hp:p id> 고유·중복 건수 (진단 정보, FAIL 아님)       ★ v1.3 신설
7. 이미지 무결성 : content.hpf에 등록된 BinData 항목이 실제로 존재하는가
8. 본문 통계     : 단락 수 / 이미지 수 / 추출 글자 수

원본과 비교하려면 --base 로 편집 전 파일을 함께 준다. 텍스트 diff 요약을 낸다.

※ 5번은 한글이 "파일을 읽거나 저장하는데 오류가 있습니다"로 파일 자체를 거부하는
   대표 원인이다. 표에서 행·열을 지운 뒤 병합 셀의 span을 줄이지 않으면 발생하며,
   `@rhwp/core`의 contentLoss·exportHwpVerify로는 잡히지 않는다.

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
import xml.etree.ElementTree as ET
from collections import Counter

REQUIRED = ["mimetype", "version.xml", "META-INF/container.xml"]


def local(el):
    """네임스페이스 프리픽스를 뗀 태그 이름."""
    return el.tag.rsplit("}", 1)[-1]


def check_tables(xml_bytes):
    """표의 병합 정합성 검사. 오류 메시지 리스트와 검사한 표 수를 돌려준다.

    HWPX의 세로 병합 셀은 <hp:cellAddr rowAddr=".."/> + <hp:cellSpan rowSpan=".."/>로
    '시작 주소 + 걸치는 행 수'를 표현한다. 행을 지운 뒤 rowSpan을 줄이지 않으면
    셀이 표 밖까지 걸친 상태가 되고, 한글은 그런 문서를 열지 않는다.
    """
    errors, n_tbl = [], 0
    root = ET.fromstring(xml_bytes)
    for tbl in root.iter():
        if local(tbl) != "tbl":
            continue
        n_tbl += 1
        # 중첩 표의 행을 끌어오지 않도록 직계 자식만 센다
        rows = [c for c in tbl if local(c) == "tr"]
        n_rows = len(rows)
        declared = tbl.get("rowCnt")
        if declared is not None and int(declared) != n_rows:
            errors.append(f"tbl rowCnt={declared} 인데 실제 <hp:tr>은 {n_rows}개")

        n_cols = int(tbl.get("colCnt") or 0)
        for tr in rows:
            for tc in tr:
                if local(tc) != "tc":
                    continue
                addr = span = None
                for child in tc:
                    if local(child) == "cellAddr":
                        addr = child
                    elif local(child) == "cellSpan":
                        span = child
                if addr is None or span is None:
                    continue
                r0, rs = int(addr.get("rowAddr")), int(span.get("rowSpan"))
                c0, cs = int(addr.get("colAddr")), int(span.get("colSpan"))
                if r0 + rs > n_rows:
                    errors.append(
                        f"세로 병합이 표 밖으로 넘침: rowAddr={r0} rowSpan={rs} "
                        f"(표 행 수 {n_rows}) — 행을 지웠다면 rowSpan을 {max(n_rows - r0, 1)}로 줄일 것")
                if n_cols and c0 + cs > n_cols:
                    errors.append(
                        f"가로 병합이 표 밖으로 넘침: colAddr={c0} colSpan={cs} "
                        f"(표 열 수 {n_cols})")
    return errors, n_tbl


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

        # 5. 표 구조 — 병합 범위가 표 밖으로 넘치지 않는가
        #    (한글이 파일 자체를 거부하는 대표 원인. 다른 검증 도구는 잡지 못한다)
        tbl_errors, n_tbl = [], 0
        for n in sections(z):
            try:
                errs, cnt = check_tables(z.read(n))
            except ET.ParseError:
                continue          # XML 파싱 실패는 3번에서 이미 보고됨
            tbl_errors += [f"{n}: {e}" for e in errs]
            n_tbl += cnt
        if tbl_errors:
            bad("표 병합 정합성 오류 — 한글이 파일을 열지 못합니다:\n     "
                + "\n     ".join(tbl_errors))
        elif n_tbl:
            print(f"  ✓ 표 구조 정상 ({n_tbl}개 표, 병합 범위 이상 없음)")

        # 6. 단락 id 분포 (진단 정보 — FAIL 사유가 아니다)
        #
        # ⚠ 2026-09-05 실측 정정. 한글이 직접 만든 문서도 <hp:p id>를 대량 재사용한다.
        #   이 스킬 동봉 assets/report-template.hwpx는 단락 103개에 고유 id가 3개뿐이고
        #   ('2147483648'=0x80000000 69회, '0' 33회) 한글에서 정상적으로 열린다.
        #   id는 유일 키가 아니라 sentinel 값에 가깝다. 중복을 FAIL로 잡으면 이 스킬이
        #   동봉한 자기 템플릿조차 FAIL이 되고, R3("PASS 없이는 전달하지 않는다") 때문에
        #   정상 산출물이 계속 막힌다. 그래서 건수만 보고한다.
        dup_report = []
        for n in sections(z):
            ids = re.findall(r"<\w*:?p\s[^>]*\bid=\"(\d+)\"", z.read(n).decode("utf-8"))
            c = Counter(ids)
            dups = [k for k, v in c.items() if v > 1]
            if dups:
                dup_report.append(f"{os.path.basename(n)}: 단락 {len(ids)}개 / 고유 {len(c)}개 "
                                  f"(재사용 id {len(dups)}종, 예: {dups[:3]})")
        if dup_report:
            print("  · 단락 id 재사용 — 한글 원본도 그렇게 한다(정상):\n     "
                  + "\n     ".join(dup_report))
        else:
            print("  ✓ 단락 id 유일")

        # 7. 이미지 참조 무결성
        if "Contents/content.hpf" in names:
            hpf = z.read("Contents/content.hpf").decode("utf-8")
            refs = re.findall(r'href="(BinData/[^"]+)"', hpf)
            lost = [r for r in refs if r not in names]
            if lost:
                bad(f"content.hpf가 참조하는 파일 없음: {lost}")
            elif refs:
                print(f"  ✓ 이미지 참조 {len(refs)}건 모두 존재")

        # 8. 통계
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
