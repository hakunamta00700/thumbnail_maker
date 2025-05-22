#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

async function main() {
  const [,, dslPath = 'thumbnail.json', outPath = 'thumbnail.png'] = process.argv;
  if (!fs.existsSync(dslPath)) throw new Error(`DSL 파일 없음: ${dslPath}`);
  const dsl = JSON.parse(fs.readFileSync(dslPath, 'utf-8'));

  const html = buildHtml(dsl);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: null });
  await page.setContent(html, { waitUntil: 'networkidle' });

  const thumb = await page.$('#thumb');
  await thumb.screenshot({ path: outPath });
  await browser.close();
  console.log(`✅ 생성됨: ${outPath}`);
}

function buildHtml(dsl) {
  const { Resolution, Background, Texts } = dsl.Thumbnail;
  const [w, h] = (() => {
    switch (Resolution.value) {
      case '16:9': return [480, 270];
      case '9:16': return [270, 480];
      case '4:3':  return [480, 360];
      case '1:1':  return [360, 360];
      default: throw new Error(`알 수 없는 해상도: ${Resolution.value}`);
    }
  })();

  // font-face CSS
  let fontCss = '';
  Texts.forEach(txt => {
    if (!Array.isArray(txt.font.faces)) return;
    txt.font.faces.forEach(f => {
      fontCss += `@font-face {
  font-family: '${f.name}';
  src: url('${f.url}') format('woff2');
  font-weight: ${f.weight};
  font-style: ${f.style};
}\n`;
    });
  });

  // background style
  let bgStyle = '';
  if (Background.type === 'solid') {
    bgStyle = `background-color: ${Background.color};`;
  } else if (Background.type === 'gradient') {
    const stops = Background.colors.map((c,i) =>
      `${c} ${(i/(Background.colors.length-1))*100}%`
    ).join(', ');
    bgStyle = `background: linear-gradient(90deg, ${stops});`;
  } else if (Background.type === 'image') {
    bgStyle = `background-image: url('${Background.imagePath}');
background-size: cover; background-position: center;`;
  }

  // text layers
  let textHtml = '';
  Texts.forEach(txt => {
    if (!txt.enabled) return;
    // split on actual newlines or literal \n
    const lines = txt.content.split(/\\n|\r\n|\r|\n/);
    const weight = txt.type === 'title' ? 'bold' : 'normal';
    const size = txt.fontSize;
    const outlineCss = txt.outline ? (
      Array(4).map((_,i) => {
        const offsets = [[-1,0],[0,1],[1,0],[0,-1]][i];
        return `${offsets[0]}px ${offsets[1]}px 0 ${txt.outline.color}`;
      }).join(',')
    ) : '';

    const verticalPos = {
      top: '10px',
      middle: '50%',
      bottom: 'auto'
    }[txt.position.vertical];
    const bottomPos = txt.position.vertical === 'bottom' ? '10px' : 'auto';
    const transform = txt.position.vertical === 'middle' ? 'translateY(-50%)' : '';

    textHtml += `
<div style="
  position: absolute;
  left: 10px;
  top: ${verticalPos};
  bottom: ${bottomPos};
  transform: ${transform};
  font-family: '${txt.font.name}';
  font-size: ${size}px;
  font-weight: ${weight};
  color: ${txt.color};
  text-shadow: ${outlineCss};
  line-height: 1.1;
">
  ${lines.map(line => `<div>${line}</div>`).join('')}
</div>`;
  });

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
${fontCss}
body,html { margin:0; padding:0; }
#thumb {
  position: relative;
  width: ${w}px;
  height: ${h}px;
  overflow: hidden;
  ${bgStyle}
}
#thumb div { /* ensure block for each line */ }
  </style>
</head>
<body>
  <div id="thumb">
    ${textHtml}
  </div>
</body>
</html>`;
}

main().catch(e => { console.error(e); process.exit(1); });
