#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
align_tables.py — HWPX 표 셀 정렬 기준(R10) 일괄 적용

정렬 기준 (사용자 지정, 2026-10-09)
------------------------------------
1. 첫 열이 번호(No.·번호·순번·연번, 또는 1·2·3 / ①② / Q-01 같은 값)면  → 가운데
2. 금액 열(1,000 / 3,516,800원 / 2,500천원 …)                         → 오른쪽 + 오른쪽 여백(영문 한 글자)
3. 부호 열(O, X, ○, ●, △, ✓, □, -, 예/아니오 …)                      → 가운데
4. 행마다 글자 수가 크게 다른 열(설명·내용)                             → 왼쪽
5. 글자 수 변화가 거의 없는 열(항목 구분·날짜·성명·버전 등)               → 가운데
머리행(제목 행)은 항상 가운데. 1열짜리 표(박스·주석 상자)는 건드리지 않는다.
여러 열에 걸친 병합 셀(colSpan>1)은 값이 금액·부호일 때만 정렬하고 나머지는 둔다.

동작
----
- 셀 단락의 paraPrIDRef를 정렬만 다른 paraPr 복제본으로 갈아 끼운다(원본 paraPr는 그대로 두므로
  본문 단락에 영향 없음). 금액 칸 paraPr는 오른쪽 여백(hc:right)을 추가한다.
- header.xml의 paraProperties itemCnt를 갱신한다.
- 레이아웃 캐시(linesegarray)는 건드리지 않으므로 실행 후 clear_layout_cache.py를 돌린다(R1).

사용법
------
python3 align_tables.py in.hwpx [out.hwpx] [--dry]      # out 생략 시 덮어쓰기
  --dry : 바꾸지 않고 표·열별 판정만 출력
"""
import sys, re, os, zipfile, copy
from lxml import etree

HP = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
HH = 'http://www.hancom.co.kr/hwpml/2011/head'
HC = 'http://www.hancom.co.kr/hwpml/2011/core'
P, H, C = '{%s}' % HP, '{%s}' % HH, '{%s}' % HC

RIGHT_PAD = 500          # 금액 칸 오른쪽 여백(HWPUNIT, 5pt ≈ 10pt 글꼴의 영문 한 글자)
NO_HEAD = re.compile(r'^(no\.?|번호|순번|연번|순위|#)$', re.I)
NO_VAL = re.compile(r'^(\d{1,3}|[①-⑳]|[ⅰ-ⅹⅠ-Ⅹ]|[A-Z]?-?\d{1,3}|Q-\d+|[가-하]\.|\d{1,3}[.)])$')
AMT_HEAD = re.compile(r'금액|단가|예산|비용|원\)|천원|만원|합계|소계|공급가|세액|집행액|편성')
AMT_LEAD = re.compile(r'^[-−]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?\s*(원|천원|만원|백만원|억원)?(?=\s|$|[(〔+])')
AMT_VAL = re.compile(r'^[-−]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?\s*(원|천원|만원|백만원|억원)?$')
SYM_VAL = re.compile(r'^([OXoxＯＸ○●◎◯△▲▽×✓✔✗□■☐☑◇◆\-–—·/]|예|아니오|해당|미해당|유|무|Y|N|y|n)$')
CAT_HEAD = re.compile(r'^(항목|구분|분류|유형|단계|계층|종류|항목명|구분명)$')
SYM_IN = re.compile(r'[○●◎△×✓□]|O/X|O·X')
DESC_HEAD = re.compile(r'내용|요약|조치|비고|현황|의견|사유|원인|사항|근거')
ROLE_HEAD = re.compile(r'^[^()]{1,6}\((.{2,12})\)$')       # 점검(관리감독자) 같은 결재·서명 칸
SIGN_HEAD = re.compile(r'작성|검토|승인|확인|서명|결재|보고|조사')
AMT_PREFIX = re.compile(r'^(월|총|연|약)\s*[\d,]+(\.\d+)?\s*(원|천원|만원)?')
NEUTRAL = re.compile(r'^[-–—―·\s]*$')


def own(p):
    return ''.join((t.text or '') for r in p.findall(P + 'run') for t in r.findall(P + 't'))


def cell_text(tc):
    return '\n'.join(own(p) for p in tc.iter(P + 'p')).strip()


def kind(v):
    s = v.strip()
    if not s or NEUTRAL.match(s):
        return 'empty'
    if AMT_VAL.match(s.replace(' ', '')) and (',' in s or re.search(r'원$', s)):
        return 'amount'
    m = AMT_LEAD.match(s)
    if m and (',' in m.group(0) or re.search(r'원', m.group(0))):
        return 'amountx'                   # 금액 + 부기(35.2%)·〔Q-xx〕 등
    if SYM_VAL.match(s):
        return 'symbol'
    if NO_VAL.match(s):
        return 'no'
    return 'text'


def tlen(v):
    # 가장 긴 줄 기준 글자 수(한글·영문 동일 1자)
    return max((len(x.strip()) for x in v.split('\n')), default=0)


class Aligner:
    def __init__(self, path):
        self.z = zipfile.ZipFile(path)
        self.names = self.z.namelist()
        self.hdr = etree.fromstring(self.z.read('Contents/header.xml'))
        self.secs = {n: etree.fromstring(self.z.read(n)) for n in self.names
                     if re.match(r'Contents/section\d+\.xml$', n)}
        self.pp = self.hdr.find('.//' + H + 'paraProperties')
        self.byid = {e.get('id'): e for e in self.pp.findall(H + 'paraPr')}
        self.cache = {}
        self.log = []

    # ── paraPr 복제 ──
    def ref_for(self, src_id, align, pad=0):
        key = (src_id, align, pad)
        if key in self.cache:
            return self.cache[key]
        src = self.byid.get(src_id)
        if src is None:
            return src_id
        a = src.find(H + 'align')
        cur_pad = 0
        for m in src.iter(H + 'margin'):
            r = m.find(C + 'right')
            cur_pad = max(cur_pad, int(r.get('value', '0')) if r is not None else 0)
            break
        if a is not None and a.get('horizontal') == align and cur_pad == pad:
            self.cache[key] = src_id
            return src_id
        new = copy.deepcopy(src)
        nid = str(max(int(k) for k in self.byid) + 1)
        new.set('id', nid)
        new.find(H + 'align').set('horizontal', align)
        # 오른쪽 여백: hp:case(HwpUnitChar)는 값 그대로, hp:default는 2배로 기록하는 한글 관례를 따른다
        for m in new.iter(H + 'margin'):
            r = m.find(C + 'right')
            if r is None:
                continue
            in_default = m.getparent().tag.endswith('default')
            r.set('value', str(pad * 2 if in_default else pad))
        self.pp.append(new)
        self.byid[nid] = new
        self.pp.set('itemCnt', str(len(self.byid)))
        self.cache[key] = nid
        return nid

    def set_align(self, tc, align, pad=0):
        for p in tc.iter(P + 'p'):
            src = p.get('paraPrIDRef')
            p.set('paraPrIDRef', self.ref_for(src, align, pad))

    # ── 표 판정 ──
    @staticmethod
    def addr(tc):
        a, s = tc.find(P + 'cellAddr'), tc.find(P + 'cellSpan')
        return int(a.get('colAddr')), int(a.get('rowAddr')), int(s.get('colSpan')), int(s.get('rowSpan'))

    def header_rows(self, tbl, trs):
        """머리행 수: 1행 셀들의 테두리/배경(borderFillIDRef)이 본문 셀과 겹치지 않으면 머리행으로 본다."""
        if len(trs) < 2:
            return 0
        head = {tc.get('borderFillIDRef') for tc in trs[0].findall(P + 'tc')}
        body = set()
        for tr in trs[1:]:
            for tc in tr.findall(P + 'tc'):
                c, r, cs, rs = self.addr(tc)
                if c > 0:
                    body.add(tc.get('borderFillIDRef'))
        if body and not (head & body):
            return 1
        # 셀 header="1" 표시가 있으면 그것을 따른다
        if all(tc.get('header') == '1' for tc in trs[0].findall(P + 'tc')):
            return 1
        return 0

    def collect(self, tbl, label):
        trs = tbl.findall(P + 'tr')
        ncol = int(tbl.get('colCnt', '1'))
        if ncol < 2 or not trs:
            return None
        nh = self.header_rows(tbl, trs)
        cols, heads, fills = {}, {}, {}
        for tr in trs:
            for tc in tr.findall(P + 'tc'):
                c, r, cs, rs = self.addr(tc)
                if r < nh:
                    if cs == 1:
                        heads[c] = cell_text(tc)
                    continue
                cols.setdefault(c, []).append((tc, cs))
                if cs == 1:
                    fills.setdefault(c, set()).add(tc.get('borderFillIDRef'))
        # 라벨 열: 본문 1열의 배경/테두리가 다른 열과 겹치지 않으면(머리행처럼 칠한 항목명 칸)
        others = set().union(*[v for k, v in fills.items() if k > 0]) if len(fills) > 1 else set()
        label_col = nh > 0 and 0 in fills and others and not (fills[0] & others)
        key = ('H',) + tuple(re.sub(r'\s+', '', heads.get(c, '')) for c in range(ncol)) if nh else ('T', id(tbl))
        return dict(tbl=tbl, trs=trs, nh=nh, cols=cols, heads=heads, label_col=label_col, key=key, label=label)

    def decide(self, c, head, vals, label_col):
        kinds = [kind(v) for v in vals]
        real = [k for k in kinds if k != 'empty']
        lens = [tlen(v) for v, k in zip(vals, kinds) if k != 'empty']
        if c == 0 and (NO_HEAD.match(head) or (real and all(k == 'no' for k in real) and len(real) >= 2)):
            return ('CENTER', 0, 'No.')
        amt = [k for k in real if k in ('amount', 'amountx')]
        if real and len(amt) == len(real):
            return ('RIGHT', RIGHT_PAD, '금액')
        if AMT_HEAD.search(head):              # 머리글이 금액이면 '월 510'·'총 2,800' 같은 접두 금액도 금액으로 본다
            amt = [v for v, k in zip(vals, kinds) if k in ('amount', 'amountx') or AMT_PREFIX.match(v.strip())]
        if real and AMT_HEAD.search(head) and len(amt) * 2 >= len(real):
            return ('RIGHT', RIGHT_PAD, '금액(머리글 기준)')
        if real and all(k == 'symbol' for k in real):
            return ('CENTER', 0, '부호')
        if c == 0 and (label_col or CAT_HEAD.match(head)) and real and max(lens) <= 15:
            return ('CENTER', 0, '항목 구분 열')
        if not real:
            if AMT_HEAD.search(head) and not DESC_HEAD.search(head):
                return ('RIGHT', RIGHT_PAD, '금액 기입란')
            if SYM_IN.search(head):
                return ('CENTER', 0, '부호 기입란')
            if ROLE_HEAD.match(head):
                return ('CENTER', 0, '서명란')
            if DESC_HEAD.search(head):
                return ('LEFT', 0, '빈칸·서술 머리')
            if SIGN_HEAD.search(head):
                return ('CENTER', 0, '서명란')
            if 0 < len(head) <= 4 and not re.search(r'내용|조치|비고|현황|의견|사유|원인', head):
                return ('CENTER', 0, '빈칸·짧은 머리')
            return ('LEFT', 0, '빈칸·서술 머리')
        if max(lens) <= 15 and (max(lens) - min(lens)) <= 4:
            return ('CENTER', 0, f'구분형(글자 수 {min(lens)}~{max(lens)})')
        return ('LEFT', 0, f'서술형(글자 수 {min(lens)}~{max(lens)})')

    def apply(self, info, decided):
        for tr in info['trs'][:info['nh']]:
            for tc in tr.findall(P + 'tc'):
                self.set_align(tc, 'CENTER')
        for c, items in info['cols'].items():
            dec = decided.get(c)
            for tc, cs in items:
                if cs == 1 and dec:
                    self.set_align(tc, dec[0], dec[1])
                elif cs > 1:
                    k = kind(cell_text(tc))
                    if k in ('amount', 'amountx'):
                        self.set_align(tc, 'RIGHT', RIGHT_PAD)
                    elif k == 'symbol':
                        self.set_align(tc, 'CENTER')
        self.log.append((info['label'], info['nh'],
                         {c: (info['heads'].get(c, '')[:10], d[0], d[2]) for c, d in sorted(decided.items())}))

    def run(self):
        infos = []
        for name, root in self.secs.items():
            for tbl in root.iter(P + 'tbl'):
                first = ''
                for tc in tbl.iter(P + 'tc'):
                    first = cell_text(tc)[:14]
                    break
                info = self.collect(tbl, f'표{len(infos) + 1} [{first}]')
                infos.append(info)
        # 머리행이 같은 표(한 표를 여러 개로 나눈 경우 등)는 열 판정을 합쳐서 한다
        # (연속해서 놓인 표만 묶는다 — 떨어져 있는 같은 머리행 표는 각자 판정)
        runs, prev = [], None
        for info in infos:
            if not info:
                prev = None
                continue
            if prev is not None and prev['key'] == info['key'] and info['key'][0] == 'H':
                runs[-1].append(info)
            else:
                runs.append([info])
            prev = info
        for members in runs:
            decided = {}
            ncols = set().union(*[m['cols'].keys() for m in members])
            for c in sorted(ncols):
                vals = [cell_text(tc) for m in members for tc, cs in m['cols'].get(c, []) if cs == 1]
                head = re.sub(r'\s+', '', members[0]['heads'].get(c, ''))
                decided[c] = self.decide(c, head, vals, any(m['label_col'] for m in members))
            for m in members:
                self.apply(m, decided)
        self.log.sort(key=lambda x: int(re.match(r'표(\d+)', x[0]).group(1)))
        return len(infos)

    def save(self, out):
        data = {n: b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + etree.tostring(r, encoding='utf-8')
                for n, r in self.secs.items()}
        data['Contents/header.xml'] = b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + \
            etree.tostring(self.hdr, encoding='utf-8')
        tmp = out + '.tmp'
        with zipfile.ZipFile(tmp, 'w') as zo:
            infos = self.z.infolist()
            infos.sort(key=lambda i: i.filename != 'mimetype')      # R2: mimetype 맨 앞
            for it in infos:
                d = data.get(it.filename, None)
                if d is None:
                    d = self.z.read(it.filename)
                zi = zipfile.ZipInfo(it.filename, date_time=it.date_time)
                zi.compress_type = zipfile.ZIP_STORED if it.filename == 'mimetype' else zipfile.ZIP_DEFLATED
                zi.external_attr = it.external_attr
                zo.writestr(zi, d)
        os.replace(tmp, out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry' in sys.argv
    if not args:
        print(__doc__); sys.exit(1)
    src = args[0]
    out = args[1] if len(args) > 1 else src
    a = Aligner(src)
    n = a.run()
    for label, nh, d in a.log:
        print(f'{label} 머리행 {nh}:', '; '.join(f'{c}열[{h}]→{al}({why})' for c, (h, al, why) in d.items()))
    if not dry:
        a.save(out)
        print(f'[align] 표 {n}개 처리 → {out}')


if __name__ == '__main__':
    main()
