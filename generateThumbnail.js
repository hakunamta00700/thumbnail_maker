#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');
const woff2 = require('woff2');           // WOFF2 -> TTF 변환 지원
const Font = require('fonteditor-core').Font;  // WOFF -> TTF 변환 지원
const { createCanvas, loadImage, registerFont } = require('canvas');

async function main() {
  const [,, dslPath = 'thumbnail.json', outPath = 'thumbnail.png'] = process.argv;
  if (!fs.existsSync(dslPath)) {
    console.error(`DSL 파일을 찾을 수 없습니다: ${dslPath}`);
    process.exit(1);
  }

  const dsl = JSON.parse(fs.readFileSync(dslPath, 'utf-8'));
  const faces = collectFontFaces(dsl);
  await ensureFonts(faces);

  // 폰트 등록
  faces.forEach(f => {
    let file = fontFilePath(f);
    const ext = path.extname(file).toLowerCase();
    // WOFF2 자동 변환
    if (ext === '.woff2') {
      try {
        const woffData = fs.readFileSync(file);
        const ttfData = woff2.decode(woffData);
        const ttfPath = file.replace(/\.woff2$/, '.ttf');
        fs.writeFileSync(ttfPath, ttfData);
        file = ttfPath;
        console.log(`🔄 WOFF2를 TTF로 변환: ${ttfPath}`);
      } catch (e) {
        console.warn(`WOFF2 변환 실패: ${file}`, e.message);
      }
    }
    // WOFF 자동 변환
    else if (ext === '.woff') {
      try {
        const woffBuffer = fs.readFileSync(file);
        const ttfBuf = Font.create(woffBuffer, { type: 'woff' }).write({ type: 'ttf' });
        const ttfPath = file.replace(/\.woff$/, '.ttf');
        fs.writeFileSync(ttfPath, Buffer.from(ttfBuf));
        file = ttfPath;
        console.log(`🔄 WOFF를 TTF로 변환: ${ttfPath}`);
      } catch (e) {
        console.warn(`WOFF 변환 실패: ${file}`, e.message);
      }
    }

    // 최종 확장자 체크 후 등록
    const finalExt = path.extname(file).toLowerCase();
    if (['.ttf', '.otf'].includes(finalExt)) {
      try {
        registerFont(file, { family: f.name, weight: f.weight, style: f.style });
      } catch (err) {
        console.error(`폰트 등록 실패: ${file}`, err.message);
      }
    } else {
      console.warn(`지원되지 않는 폰트 형식입니다: ${file}`);
    }
  });

  await generateThumbnail(dsl.Thumbnail, outPath);
}

function collectFontFaces(dsl) {
  const map = new Map();
  dsl.Thumbnail.Texts.forEach(txt => {
    if (txt.font && Array.isArray(txt.font.faces)) {
      txt.font.faces.forEach(f => {
        const key = `${f.name}|${f.url}|${f.weight}|${f.style}`;
        if (!map.has(key)) map.set(key, f);
      });
    }
  });
  return Array.from(map.values());
}

async function ensureFonts(faces) {
  const dir = path.join(__dirname, 'fonts');
  if (!fs.existsSync(dir)) fs.mkdirSync(dir);
  for (const f of faces) {
    await downloadFont(f, dir);
  }
}

function downloadFont(f, dir) {
  return new Promise((resolve, reject) => {
    const file = fontFilePath(f, dir);
    if (fs.existsSync(file)) return resolve();
    console.log(`🔽 폰트 다운로드: ${f.name} from ${f.url}`);
    const stream = fs.createWriteStream(file);
    https.get(f.url, res => {
      if (res.statusCode !== 200) {
        return reject(new Error(`다운로드 실패 ${f.url}: ${res.statusCode}`));
      }
      res.pipe(stream);
      stream.on('finish', () => stream.close(resolve));
    }).on('error', err => {
      fs.unlinkSync(file);
      reject(err);
    });
  });
}

function fontFilePath(f, dir = path.join(__dirname, 'fonts')) {
  const ext = path.extname(new URL(f.url).pathname) || '.ttf';
  const safeName = `${sanitize(f.name)}-${f.weight}-${f.style}${ext}`;
  return path.join(dir, safeName);
}

// 파일명 안전화
function sanitize(name) {
  return name.replace(/[^a-zA-Z0-9\-_]/g, '_');
}

async function generateThumbnail(cfg, outFile) {
  let width, height;
  if (cfg.Resolution.type === 'preset') {
    switch (cfg.Resolution.value) {
      case '16:9': [width, height] = [480, 270]; break;
      case '9:16': [width, height] = [270, 480]; break;
      case '4:3':  [width, height] = [480, 360]; break;
      case '1:1':  [width, height] = [360, 360]; break;
      default: throw new Error(`알 수 없는 프리셋: ${cfg.Resolution.value}`);
    }
  } else {
    width = cfg.Resolution.width;
    height = cfg.Resolution.height;
  }

  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext('2d');

  // 배경
  const bg = cfg.Background;
  if (bg.type === 'solid') {
    ctx.fillStyle = bg.color;
    ctx.fillRect(0, 0, width, height);
  } else if (bg.type === 'gradient') {
    const grad = ctx.createLinearGradient(0, 0, width, 0);
    bg.colors.forEach((c, i) => grad.addColorStop(i/(bg.colors.length-1), c));
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, width, height);
  } else if (bg.type === 'image') {
    try {
      const img = await loadImage(bg.imagePath);
      ctx.drawImage(img, 0, 0, width, height);
    } catch (e) {
      console.warn('배경 이미지 로드 실패:', e.message);
    }
  }

  // 텍스트 그리기
  const M = 20;
  function drawText(txtCfg) {
    if (!txtCfg.enabled) return;
    const lines = txtCfg.content.split('\n');
    const fontSpec = `${txtCfg.type==='title'?'bold ':''}${txtCfg.fontSize}px '${txtCfg.font.name}'`;
    ctx.font = fontSpec;
    ctx.fillStyle = txtCfg.color;
    ctx.textBaseline = 'top';
    if (txtCfg.outline) { ctx.lineWidth = txtCfg.outline.thickness; ctx.strokeStyle = txtCfg.outline.color; }

    const lh = txtCfg.fontSize * 1.1;
    let y = txtCfg.position.vertical === 'top' ? M
          : txtCfg.position.vertical === 'middle' ? (height - lines.length*lh)/2
          : height - lines.length*lh - M;

    for (const line of lines) {
      const textWidth = ctx.measureText(line).width;
      const x = txtCfg.position.horizontal === 'left' ? M
              : txtCfg.position.horizontal === 'center' ? (width - textWidth)/2
              : width - textWidth - M;
      if (ctx.lineWidth) ctx.strokeText(line, x, y);
      ctx.fillText(line, x, y);
      y += lh;
    }
  }

  for (const txt of cfg.Texts) drawText(txt);

  fs.writeFileSync(outFile, canvas.toBuffer('image/png'));
  console.log(`✅ 썸네일 생성됨: ${outFile}`);
}

main().catch(err => { console.error(err); process.exit(1); });
