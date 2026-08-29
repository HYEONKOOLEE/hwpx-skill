#!/usr/bin/env node
// hwp_bridge.mjs — HWP5 <-> HWPX 변환 게이트 (@rhwp/core WASM, 한컴오피스 불필요)
//   node hwp_bridge.mjs to-hwpx <입력.hwp>  <출력.hwpx>
//   node hwp_bridge.mjs to-hwp  <입력.hwpx> <출력.hwp>
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const [, , mode, src, dst] = process.argv;
if (!['to-hwpx', 'to-hwp'].includes(mode) || !src || !dst) {
  console.error('usage: node hwp_bridge.mjs <to-hwpx|to-hwp> <src> <dst>');
  process.exit(2);
}

const require = createRequire(import.meta.url);
const pkgDir = path.dirname(require.resolve('@rhwp/core/package.json'));
const { default: init, HwpDocument } = await import(path.join(pkgDir, 'rhwp.js'));
await init({ module_or_path: fs.readFileSync(path.join(pkgDir, 'rhwp_bg.wasm')) });

const doc = new HwpDocument(new Uint8Array(fs.readFileSync(src)));
const exp = mode === 'to-hwpx' ? doc.exportHwpxWithReport() : doc.exportHwpWithReport();
const loss = JSON.parse(exp.contentLoss() || '{}');
const bytes = exp.takeBytes();
fs.writeFileSync(dst, Buffer.from(bytes));

const out = { mode, src, dst, bytes: bytes.length, contentLoss: loss };
if (mode === 'to-hwp') out.verify = JSON.parse(doc.exportHwpVerify());   // 쪽수 보존 검증
console.log(JSON.stringify(out, null, 2));

// 손실이 보고되면 종료코드 3 — 조용히 넘어가지 않는다
process.exit((loss.count ?? 0) > 0 ? 3 : 0);
