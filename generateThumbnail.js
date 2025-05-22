#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');

async function main() {
  // 1) 첫 번째 인자: DSL JSON 파일 경로 (default: thumbnail.json)
  // 2) 두 번째 인자: 출력 이미지 파일 경로 (default: thumbnail.png)
  const [,, dslPath = 'thumbnail.json', outPath = 'thumbnail.png'] = process.argv;

  if (!fs.existsSync(dslPath)) {
    console.error(`DSL 파일을 찾을 수 없습니다: ${dslPath}`);
    process.exit(1);
  }

  const dsl = JSON.parse(fs.readFileSync(dslPath, 'utf-8'));
  await generateThumbnail(dsl.Thumbnail, outPath);
}

async function generateThumbnail(cfg, outFile) {
  // ─── 해상도 설정 ─────────────────────────
  let width, height;
  if (cfg.Resolution.type === 'preset') {
    switch (cfg.Resolution.value) {
      case '16:9': [width,height] = [480,270]; break;
      case '9:16': [width,height] = [270,480]; break;
      case '4:3':  [width,height] = [480,360]; break;
      case '1:1':  [width,height] = [360,360]; break;
      default:
        throw new Error(`알 수 없는 프리셋: ${cfg.Resolution.value}`);
    }
  } else if (cfg.Resolution.type === 'custom') {
    width  = cfg.Resolution.width;
    height = cfg.Resolution.height;
  } else {
    throw new Error(`Unsupported resolution type: ${cfg.Resolution.type}`);
  }

  // Canvas 생성
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext('2d');

  // ─── 배경 그리기 ─────────────────────────
  const bg = cfg.Background;
  if (bg.type === 'solid') {
    ctx.fillStyle = bg.color;
    ctx.fillRect(0, 0, width, height);

  } else if (bg.type === 'gradient') {
    // 좌→우 그라데이션 예시
    const grad = ctx.createLinearGradient(0, 0, width, 0);
    bg.colors.forEach((c, i) => {
      grad.addColorStop(i/(bg.colors.length-1), c);
    });
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, width, height);

  } else if (bg.type === 'image') {
    try {
      const img = await loadImage(bg.imagePath);
      ctx.drawImage(img, 0, 0, width, height);
    } catch (e) {
      console.warn('배경 이미지 로드 실패:', e.message);
      ctx.fillStyle = '#ccc';
      ctx.fillRect(0, 0, width, height);
    }
  }

  // ─── 텍스트 그리기 헬퍼 ──────────────────────
  const MARGIN = 20;
  function drawTextBlock(txtCfg) {
    if (!txtCfg.enabled) return;
    const lines = txtCfg.content.split('\n');
    const fontSpec = `${txtCfg.type==='title' ? 'bold ' : ''}${txtCfg.fontSize}px ${txtCfg.font.name}`;
    ctx.font = fontSpec;
    ctx.fillStyle = txtCfg.color;
    ctx.textBaseline = 'top';

    // 외곽선 설정
    if (txtCfg.outline) {
      ctx.lineWidth = txtCfg.outline.thickness;
      ctx.strokeStyle = txtCfg.outline.color;
    } else {
      ctx.lineWidth = 0;
    }

    // 전체 블록 높이 계산
    const lineHeight = txtCfg.fontSize * 1.1;
    const blockHeight = lines.length * lineHeight;

    // Y 위치: top / middle / bottom
    let y;
    switch (txtCfg.position.vertical) {
      case 'top':    y = MARGIN; break;
      case 'middle': y = (height - blockHeight)/2; break;
      case 'bottom': y = height - blockHeight - MARGIN; break;
      default: y = MARGIN;
    }

    // 각 줄 그리기
    for (const line of lines) {
      // 글자 너비 측정
      const metrics = ctx.measureText(line);
      const textWidth = metrics.width;

      // X 위치: left / center / right
      let x;
      switch (txtCfg.position.horizontal) {
        case 'left':   x = MARGIN; break;
        case 'center': x = (width - textWidth)/2; break;
        case 'right':  x = width - textWidth - MARGIN; break;
        default: x = MARGIN;
      }

      // 외곽선, 채우기
      if (ctx.lineWidth > 0) ctx.strokeText(line, x, y);
      ctx.fillText(line, x, y);

      y += lineHeight;
    }
  }

  // ─── 타이틀, 부제목 순서대로 ─────────────────
  for (const txt of cfg.Texts) {
    drawTextBlock(txt);
  }

  // ─── 파일에 저장 ───────────────────────────
  const buffer = canvas.toBuffer('image/png');
  fs.writeFileSync(outFile, buffer);
  console.log(`✅ 썸네일이 생성되었습니다: ${outFile}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

