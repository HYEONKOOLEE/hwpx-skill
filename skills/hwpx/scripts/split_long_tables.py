#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_long_tables.py — 한 쪽을 넘는 표를 다음 쪽으로 이어지게 만든다(R11)

왜 필요한가
-----------
python-hwpx나 템플릿 복제로 만든 표는 대개 '글자처럼 취급'(hp:pos treatAsChar="1")이다.
글자처럼 취급한 표는 한 글자처럼 다뤄지므로 **쪽 경계에서 나뉘지 않는다.** 표가 본문 높이보다
길면 다음 쪽으로 통째로 밀리면서 앞 쪽은 비고, 넘치는 행은 잘려 보이지 않는다.

처리
----
추정 높이가 본문 높이의 THRESHOLD(기본 0.8) 이상인 표에 대해
  1) hp:pos treatAsChar="0"  (본문과 함께 흐르는 일반 개체: vertRelTo=PARA, flowWithText=1,
                              textWrap=TOP_AND_BOTTOM 유지)
  2) hp:tbl pageBreak="CELL" (쪽 경계에서 셀 단위로 나눔)
  3) hp:tbl repeatHeader="1" + 머리행 셀 hp:tc header="1" (나뉜 쪽마다 제목 줄 반복)
을 설정한다. 한글의 [표 속성 > 여러 쪽 지원 > 셀 단위로 나눔 + 제목 줄 자동 반복]과 같다.
행 수·셀 병합·내용은 바꾸지 않는다(R4 무관).

높이 추정
---------
셀 폭(cellSz width - 안 여백)과 글자 크기(charPr height)·줄 간격(paraPr lineSpacing %)으로
줄 수를 어림한다(한글 1.0em, 영문·숫자 0.55em). 정밀하지 않으므로 경계선 근처 표는 --all로
강제하거나, 렌더링(rhwp renderPageSvg)으로 쪽 배치를 확인한다.

사용법
------
python3 split_long_tables.py in.hwpx [out.hwpx] [--dry] [--all] [--threshold 0.8] [--match 텍스트]
  --dry       판정만 출력
  --all       높이와 무관하게 머리행 있는 표 모두 적용
  --match T   T가 들어 있는 표만 대상으로 한다(여러 번 지정 가능)
실행 후 clear_layout_cache.py → verify_hwpx.py 를 돌린다.
"""
import sys, re, os, zipfile, math
from lxml import etree

HP = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
HH = 'http://www.hancom.co.kr/hwpml/2011/head'
P, H = '{%s}' % HP, '{%s}' % HH


def own(p):
    return ''.join((t.text or '') for r in p.findall(P + 'run') for t in r.findall(P + 't'))


def text_em(s):
    w = 0.0
    for ch in s:
        o = ord(ch)
        w += 0.55 if o < 0x2E80 and not (0x2460 <= o <= 0x24FF or 0x25A0 <= o <= 0x27BF) else 1.0
    return w


class Splitter:
    def __init__(self, path, threshold=0.8):
        self.z = zipfile.ZipFile(path)
        self.hdr = etree.fromstring(self.z.read('Contents/header.xml'))
        self.secs = {n: etree.fromstring(self.z.read(n)) for n in self.z.namelist()
                     if re.match(r'Contents/section\d+\.xml$', n)}
        self.th = threshold
        self.char_h = {e.get('id'): int(e.get('height', '1000')) for e in self.hdr.iter(H + 'charPr')}
        self.line_pct = {}
        for e in self.hdr.iter(H + 'paraPr'):
            ls = e.find('.//' + H + 'lineSpacing')
            pct = int(ls.get('value')) if ls is not None and ls.get('type', 'PERCENT') == 'PERCENT' else 160
            self.line_pct[e.get('id')] = pct
        self.log = []

    def body_height(self, root):
        pp = root.find('.//' + P + 'pagePr')
        if pp is None:
            return 84188 - 2 * 5668 - 2 * 4252
        m = pp.find(P + 'margin')
        g = lambda k: int(m.get(k, '0'))
        h = int(pp.get('height'))
        if pp.get('landscape') == 'NARROWLY' and int(pp.get('width')) > h:
            h = int(pp.get('width'))
        return h - g('top') - g('bottom') - g('header') - g('footer')

    def cell_height(self, tc, tbl_in):
        sz = tc.find(P + 'cellSz')
        w = int(sz.get('width'))
        cm = tc.find(P + 'cellMargin') if tc.get('hasMargin') == '1' else None
        src = cm if cm is not None else tbl_in
        l = int(src.get('left', '510')) if src is not None else 510
        r = int(src.get('right', '510')) if src is not None else 510
        t = int(src.get('top', '141')) if src is not None else 141
        b = int(src.get('bottom', '141')) if src is not None else 141
        inner = max(w - l - r, 1000)
        h = t + b
        for p in tc.iter(P + 'p'):
            runs = p.findall(P + 'run')
            size = max([self.char_h.get(r_.get('charPrIDRef'), 1000) for r_ in runs] or [1000])
            pct = self.line_pct.get(p.get('paraPrIDRef'), 160)
            lines = max(1, math.ceil(text_em(own(p)) * size / inner))
            h += lines * size * pct / 100
        return max(int(sz.get('height')), int(h))

    @staticmethod
    def header_rows(trs):
        if len(trs) < 2:
            return 0
        head = {tc.get('borderFillIDRef') for tc in trs[0].findall(P + 'tc')}
        body = {tc.get('borderFillIDRef') for tr in trs[1:] for tc in tr.findall(P + 'tc')
                if int(tc.find(P + 'cellAddr').get('colAddr')) > 0}
        if body and not (head & body):
            return 1
        if all(tc.get('header') == '1' for tc in trs[0].findall(P + 'tc')):
            return 1
        return 0

    def run(self, force=False, match=()):
        n = 0
        for name, root in self.secs.items():
            body = self.body_height(root)
            for tbl in root.iter(P + 'tbl'):
                n += 1
                trs = tbl.findall(P + 'tr')
                inm = tbl.find(P + 'inMargin')
                est = 0
                for tr in trs:
                    hs = [self.cell_height(tc, inm) for tc in tr.findall(P + 'tc')
                          if tc.find(P + 'cellSpan').get('rowSpan') == '1']
                    est += max(hs) if hs else max(int(tc.find(P + 'cellSz').get('height')) for tc in tr.findall(P + 'tc'))
                ratio = est / body
                pos = tbl.find(P + 'pos')
                inline = pos is not None and pos.get('treatAsChar') == '1'
                alltext = ''.join(own(p) for p in tbl.iter(P + 'p'))
                first = alltext[:16]
                hit = (force or ratio >= self.th)
                if match:
                    hit = any(m in alltext for m in match)
                nested = any(a.tag == P + 'tbl' for a in tbl.iterancestors())
                if not hit or nested or len(trs) < 3:
                    continue
                nh = self.header_rows(trs)
                if inline:
                    pos.set('treatAsChar', '0')
                    pos.set('flowWithText', '1')
                    pos.set('vertRelTo', 'PARA')
                    pos.set('horzRelTo', 'COLUMN')
                    pos.set('vertOffset', '0')
                    tbl.set('textWrap', 'TOP_AND_BOTTOM')
                tbl.set('pageBreak', 'CELL')
                if nh:
                    tbl.set('repeatHeader', '1')
                    for tc in trs[0].findall(P + 'tc'):
                        tc.set('header', '1')
                self.log.append(f'표{n} [{first}] 행 {len(trs)} · 추정 높이 {ratio:.2f}쪽 · '
                                f'{"글자처럼 취급 해제, " if inline else ""}셀 단위 나눔'
                                f'{", 제목 줄 반복" if nh else " (머리행 없음)"}')
        return n

    def save(self, out):
        data = {n: b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + etree.tostring(r, encoding='utf-8')
                for n, r in self.secs.items()}
        tmp = out + '.tmp'
        with zipfile.ZipFile(tmp, 'w') as zo:
            infos = sorted(self.z.infolist(), key=lambda i: i.filename != 'mimetype')
            for it in infos:
                d = data.get(it.filename)
                if d is None:
                    d = self.z.read(it.filename)
                zi = zipfile.ZipInfo(it.filename, date_time=it.date_time)
                zi.compress_type = zipfile.ZIP_STORED if it.filename == 'mimetype' else zipfile.ZIP_DEFLATED
                zi.external_attr = it.external_attr
                zo.writestr(zi, d)
        os.replace(tmp, out)


def main():
    argv = sys.argv[1:]
    th, match, pos = 0.8, [], []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--threshold':
            th = float(argv[i + 1]); i += 2; continue
        if a == '--match':
            match.append(argv[i + 1]); i += 2; continue
        if not a.startswith('--'):
            pos.append(a)
        i += 1
    if not pos:
        print(__doc__); sys.exit(1)
    s = Splitter(pos[0], th)
    n = s.run(force='--all' in argv, match=match)
    print('\n'.join(s.log) or '(대상 표 없음)')
    if '--dry' not in argv:
        out = pos[1] if len(pos) > 1 else pos[0]
        s.save(out)
        print(f'[split] 표 {n}개 중 {len(s.log)}개 적용 → {out}')


if __name__ == '__main__':
    main()
