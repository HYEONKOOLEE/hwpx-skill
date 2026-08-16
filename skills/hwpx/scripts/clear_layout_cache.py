#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clear_layout_cache.py — HWPX 레이아웃 캐시(linesegarray) 전면 제거

왜 필요한가
-----------
HWPX의 모든 단락(<hp:p>)에는 한글이 마지막으로 그렸을 때의 줄 배치 캐시
<hp:linesegarray>가 들어 있다. 여기에는 줄마다 vertpos(세로 위치)와
textpos(그 줄이 시작하는 글자 offset)가 박혀 있다.

파이썬으로 텍스트를 바꾸면 글자 수는 달라지는데 이 캐시는 옛 텍스트 기준으로
남는다. 한글은 캐시가 있으면 그것을 믿고 그리기 때문에,

  * 텍스트가 길어진 경우  → 캐시에 없는 줄들이 마지막 줄 위치에 겹쳐 찍힌다
                            (본문·표 셀 모두 발생. "글씨 중복/겹침")
  * 텍스트가 짧아진 경우  → 줄 사이에 빈 공간이 남는다
  * 표 셀인 경우          → 행 높이가 옛 줄 수 기준으로 고정돼 잘려 보인다

캐시를 지우면 한글이 파일을 열 때 줄 위치를 전면 재계산하고, 자동 높이 행도
내용에 맞게 스스로 늘어난다. 높이를 파이썬에서 추정해 보정하지 말 것.

적용 범위
---------
표뿐 아니라 **본문 단락에도 똑같이 발생한다.** 텍스트를 한 글자라도 바꿨거나,
단락을 삽입/삭제했다면 종류를 가리지 말고 실행한다.

사용법
------
  python clear_layout_cache.py <file.hwpx> [file2.hwpx ...]
  python clear_layout_cache.py <file.hwpx> --check   # 제거하지 않고 잔존 개수만 보고

재패키징은 mimetype-first(ZIP_STORED) 규약을 지킨다.
"""
import os
import re
import sys
import zipfile

# self-closing 형태(<hp:linesegarray/>)와 짝 태그 형태 모두 처리한다.
PAT_PAIR = re.compile(r"<(\w+:)?linesegarray\b[^>]*>.*?</(\w+:)?linesegarray>", re.S)
PAT_SELF = re.compile(r"<(\w+:)?linesegarray\b[^>]*/>")
PAT_ANY = re.compile(r"<(\w+:)?linesegarray\b")

TARGET = lambda n: n.startswith("Contents/") and n.endswith(".xml")


def strip(text):
    """XML 문자열에서 linesegarray를 제거하고 (결과, 제거 개수)를 반환."""
    n = len(PAT_ANY.findall(text))
    text = PAT_PAIR.sub("", text)
    text = PAT_SELF.sub("", text)
    return text, n


def count_file(path):
    total = 0
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if TARGET(name):
                total += len(PAT_ANY.findall(z.read(name).decode("utf-8")))
    return total


def process(path):
    tmp = path + ".tmp"
    removed = 0
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if TARGET(item.filename):
                text, n = strip(data.decode("utf-8"))
                data = text.encode("utf-8")
                removed += n
            # mimetype은 반드시 무압축(STORED)으로 첫 항목 위치에 유지된다.
            ctype = zipfile.ZIP_STORED if item.filename == "mimetype" else zipfile.ZIP_DEFLATED
            zi = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            zi.compress_type = ctype
            zi.external_attr = item.external_attr
            zout.writestr(zi, data)
    os.replace(tmp, path)
    return removed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    if not args:
        print("사용법: python clear_layout_cache.py <file.hwpx> [--check]")
        sys.exit(1)
    for path in args:
        if not os.path.exists(path):
            print(f"파일 없음: {path}")
            sys.exit(1)
        if check:
            print(f"[check] {os.path.basename(path)} — linesegarray 잔존 {count_file(path)}개")
        else:
            n = process(path)
            left = count_file(path)
            print(f"[clear] {os.path.basename(path)} — 캐시 {n}개 제거, 잔존 {left}개")
            if left:
                print("  ⚠ 잔존이 0이 아니다. 정규식이 놓친 형태가 있는지 확인할 것.")
                sys.exit(2)


if __name__ == "__main__":
    main()
