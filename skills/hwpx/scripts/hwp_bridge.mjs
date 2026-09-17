#!/usr/bin/env node
// hwp_bridge.mjs — HWP5 <-> HWPX 변환 게이트 (@rhwp/core WASM, 한컴오피스 불필요)
//   node hwp_bridge.mjs to-hwpx <입력.hwp>  <출력.hwpx>
//   node hwp_bridge.mjs to-hwp  <입력.hwpx> <출력.hwp>
//
// 변환 엔진(@rhwp/core)은 이 스킬의 vendor/rhwp/ 에 동봉되어 있다.
// → 네트워크·npm 설치 없이 바로 동작한다. (v1.5부터)
// 동봉본을 찾지 못한 경우에만 npm 으로 설치된 @rhwp/core 를 찾는다(폴백).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const [, , mode, src, dst] = process.argv;
if (!['to-hwpx', 'to-hwp'].includes(mode) || !src || !dst) {
  console.error('usage: node hwp_bridge.mjs <to-hwpx|to-hwp> <src> <dst>');
  process.exit(2);
}

// ── 엔진 위치 결정: 1) 동봉본  2) npm 폴백 ─────────────────────────────
const here = path.dirname(fileURLToPath(import.meta.url));
const vendored = path.resolve(here, '..', 'vendor', 'rhwp');

let pkgDir;
if (fs.existsSync(path.join(vendored, 'rhwp.js')) && fs.existsSync(path.join(vendored, 'rhwp_bg.wasm'))) {
  pkgDir = vendored;                                   // 기본 경로: 동봉본
} else {
  try {
    const require = createRequire(import.meta.url);
    pkgDir = path.dirname(require.resolve('@rhwp/core/package.json'));   // 폴백: npm
  } catch {
    console.error(
      '변환 엔진을 찾을 수 없습니다.\n' +
      `  기대 위치: ${vendored}\n` +
      '  스킬 폴더의 vendor/rhwp/ 가 누락된 것 같습니다. 스킬을 다시 설치하세요.'
    );
    process.exit(4);
  }
}

const { default: init, HwpDocument } = await import(path.join(pkgDir, 'rhwp.js'));
await init({ module_or_path: fs.readFileSync(path.join(pkgDir, 'rhwp_bg.wasm')) });

// ── 변환 ────────────────────────────────────────────────────────────────
const doc = new HwpDocument(new Uint8Array(fs.readFileSync(src)));
const exp = mode === 'to-hwpx' ? doc.exportHwpxWithReport() : doc.exportHwpWithReport();
const loss = JSON.parse(exp.contentLoss() || '{}');
const bytes = exp.takeBytes();
fs.writeFileSync(dst, Buffer.from(bytes));

const out = { mode, src, dst, bytes: bytes.length, engine: pkgDir === vendored ? 'vendored' : 'npm', contentLoss: loss };
if (mode === 'to-hwp') out.verify = JSON.parse(doc.exportHwpVerify());   // 쪽수 보존 검증
console.log(JSON.stringify(out, null, 2));

// 손실이 보고되면 종료코드 3 — 조용히 넘어가지 않는다
process.exit((loss.count ?? 0) > 0 ? 3 : 0);
