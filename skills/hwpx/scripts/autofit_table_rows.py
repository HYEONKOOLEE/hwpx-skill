#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
autofit_table_rows.py — HWPX 레이아웃 캐시 정리 + 제목표 높이 정규화

왜 필요한가
-----------
HWPX(.hwpx)의 각 단락/셀에는 한글이 마지막으로 그릴 때의 줄 배치 캐시인
<hp:linesegarray>(줄별 vertpos/textpos)가 들어 있다. 셀 텍스트를 파이썬으로
교체하면 이 캐시가 옛 텍스트 기준으로 남는데, 한글은 캐시가 있으면 그것을 믿고
그리기 때문에 늘어난 텍스트를 마지막 줄 위에 겹쳐 그리는 "글씨 중복(겹침)"이
발생한다. (셀 높이가 작아서가 아니라 캐시가 stale이라 생기는 문제.)

해결 원리
---------
캐시(linesegarray)를 제거하면 한글이 파일을 열 때 줄 위치를 전면 재계산하고,
자동 높이 행은 내용에 맞게 스스로 늘어난다. 따라서 높이를 파이썬에서 무리하게
추정·보정하지 않는다(과거 그 추정이 한 줄짜리 제목표를 3032→5402로 부풀리는
회귀 버그를 일으켰음).

이 스크립트가 하는 일
--------------------
A. 레이아웃 캐시 정리 — 문서 전체의 <hp:linesegarray>를 제거하여 한글이 줄 위치를
   다시 계산하게 한다. → 글씨 중복(겹침) 방지(핵심).
B. 제목표 높이 정규화/예외 — "①번호박스+②여백+③제목"으로 된 1행 3열 인라인 제목표
   (treatAsChar)는 높이 추정 대상에서 제외하고, 과거 보정으로 부풀려진 높이가 있으면
   정상 셀(번호박스)의 최소 높이로 복원한다.

사용법
------
  python autofit_table_rows.py <file.hwpx>

권장: 텍스트 치환/편집 후 fix_namespaces.py 다음 단계에서 실행한다.
재패키징은 mimetype-first(ZIP_STORED) 규약을 지킨다.
"""
import sys
import os
import zipfile
import shutil
import tempfile
from lxml import etree

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"


def q(tag):
    return f"{{{HP}}}{tag}"


def cell_text(tc):
    return "".join("".join(t.itertext()) for t in tc.iter(q("t")))


def is_heading_table(tbl):
    """인라인 1행 3열 번호박스형 제목표인지 판별."""
    if tbl.get("rowCnt") != "1" or tbl.get("colCnt") != "3":
        return False
    pos = tbl.find(q("pos"))
    if pos is None or pos.get("treatAsChar") != "1":
        return False
    rows = tbl.findall(q("tr"))
    if not rows:
        return False
    cells = rows[0].findall(q("tc"))
    if len(cells) != 3:
        return False
    c0 = cell_text(cells[0]).strip()
    return c0.isdigit() and len(c0) <= 2  # 첫 셀이 한두 자리 절·항 번호


def normalize_heading_height(tbl):
    """부풀려진 제목표 높이를 정상 셀의 최소 높이로 복원. 변경 여부 반환."""
    cells = tbl.findall(q("tr"))[0].findall(q("tc"))
    heights = []
    for c in cells:
        cs = c.find(q("cellSz"))
        if cs is not None and cs.get("height"):
            heights.append(int(cs.get("height")))
    if not heights:
        return False
    base_h = min(heights)  # 한 줄 제목 기준 = 번호박스 셀 높이
    changed = False
    for c in cells:
        cs = c.find(q("cellSz"))
        if cs is not None and cs.get("height") and int(cs.get("height")) > base_h:
            cs.set("height", str(base_h))
            changed = True
    sz = tbl.find(q("sz"))
    if sz is not None and sz.get("height") and int(sz.get("height")) > base_h:
        sz.set("height", str(base_h))
        changed = True
    return changed


def process_section(xml_bytes):
    root = etree.fromstring(xml_bytes)
    headings_normalized = 0
    # B. 제목표 높이 정규화(예외 처리)
    for tbl in root.iter(q("tbl")):
        if is_heading_table(tbl):
            if normalize_heading_height(tbl):
                headings_normalized += 1
    # A. 레이아웃 캐시 전면 제거(겹침 방지 — 한글이 줄 위치 재계산)
    cache_removed = 0
    for lsa in list(root.iter(q("linesegarray"))):
        lsa.getparent().remove(lsa)
        cache_removed += 1
    out = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return out, cache_removed, headings_normalized


def main():
    if len(sys.argv) < 2:
        print("사용법: python autofit_table_rows.py <file.hwpx>")
        sys.exit(1)
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"파일 없음: {path}")
        sys.exit(1)

    workdir = tempfile.mkdtemp(prefix="autofit_")
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            zf.extractall(workdir)

        total_cache = total_head = 0
        contents = os.path.join(workdir, "Contents")
        for fn in os.listdir(contents):
            if fn.startswith("section") and fn.endswith(".xml"):
                fp = os.path.join(contents, fn)
                with open(fp, "rb") as f:
                    data = f.read()
                out, c, h = process_section(data)
                with open(fp, "wb") as f:
                    f.write(out)
                total_cache += c
                total_head += h

        # mimetype-first(ZIP_STORED) 규약 재패키징
        tmp_out = path + ".tmp"
        with zipfile.ZipFile(tmp_out, "w") as zf:
            mt = os.path.join(workdir, "mimetype")
            if os.path.exists(mt):
                zf.write(mt, "mimetype", compress_type=zipfile.ZIP_STORED)
            for name in names:
                if name == "mimetype":
                    continue
                full = os.path.join(workdir, name)
                if os.path.isfile(full):
                    zf.write(full, name, compress_type=zipfile.ZIP_DEFLATED)
        shutil.move(tmp_out, path)

        print(f"[autofit] 레이아웃 캐시 정리 {total_cache}개 | 제목표 높이 정규화 {total_head}개")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
