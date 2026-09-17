# vendor/rhwp — 동봉 변환 엔진

`.hwp`(HWP5) ↔ `.hwpx` 변환에 쓰는 엔진입니다. `scripts/hwp_bridge.mjs`가 이 폴더를 직접 로드하므로
**별도 설치가 필요 없습니다.** 이 폴더를 지우지 마세요.

- 출처: npm 패키지 `@rhwp/core` 0.8.6 (MIT 라이선스, `LICENSE` 참조)
- 구성: `rhwp.js`(로더) + `rhwp_bg.wasm`(파서 본체) + `package.json`
- 갱신 방법: `npm pack @rhwp/core` 후 위 파일들을 교체하고 `assets/form2.hwp` 왕복 테스트를 다시 돌립니다.
