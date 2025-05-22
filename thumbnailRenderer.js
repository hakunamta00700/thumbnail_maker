// thumbnailRenderer.js
// DSL 기반 썸네일 렌더링 공통 모듈 (구조화/유지보수성 강화)

(function (root, factory) {
  if (typeof module === 'object' && typeof module.exports === 'object') {
    module.exports = factory();
  } else {
    root.thumbnailRenderer = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {

  // 해상도 매핑
  const RESOLUTIONS = {
    '16:9': [480, 270],
    '9:16': [270, 480],
    '4:3': [480, 360],
    '1:1': [360, 360]
  };

  function splitLines(text) {
    return text.split(/\\n|\r\n|\r|\n/);
  }

  function buildFontFace(f) {
    return `
@font-face {
  font-family: '${f.name}';
  src: url('${f.url}') format('woff2');
  font-weight: ${f.weight};
  font-style: ${f.style};
}
`;
  }

  function buildOutlineCss(color, thickness) {
    // thickness만큼 여러 방향으로 text-shadow 반복
    thickness = thickness || 4;
    let shadows = [];
    for (let t = 1; t <= thickness; t++) {
      shadows.push(
        `${-t}px 0 0 ${color}`,
        `${t}px 0 0 ${color}`,
        `0 ${-t}px 0 ${color}`,
        `0 ${t}px 0 ${color}`,
        `${-t}px ${-t}px 0 ${color}`,
        `${t}px ${-t}px 0 ${color}`,
        `${-t}px ${t}px 0 ${color}`,
        `${t}px ${t}px 0 ${color}`
      );
    }
    return shadows.join(', ');
  }

  function buildTextStyle({ font, fontSize, type, color, outline, position }) {
    const weight = type === 'title' ? 'bold' : 'normal';
    const outlineOffset = outline ? (outline.thickness || 2) / 2 : 0;
    // 수평 정렬
    let textAlign = 'left';
    let left = '20px', right = 'auto', width = 'calc(100% - 40px)';
    if (position && position.horizontal === 'center') {
      textAlign = 'center';
      left = '50%';
      right = 'auto';
      width = '100%';
    } else if (position && position.horizontal === 'right') {
      textAlign = 'right';
      left = 'auto';
      right = '20px';
      width = 'calc(100% - 40px)';
    }
    const verticalPos = {
      top: `${20 + outlineOffset}px`,
      middle: '50%',
      bottom: 'auto'
    }[position.vertical];
    const bottomPos = position.vertical === 'bottom' ? `${20 + outlineOffset}px` : 'auto';
    const transform = position.vertical === 'middle'
      ? (position && position.horizontal === 'center' ? 'translate(-50%,-50%)' : 'translateY(-50%)')
      : (position && position.horizontal === 'center' ? 'translateX(-50%)' : '');
    return `
      position: absolute;
      left: ${left};
      right: ${right};
      top: ${verticalPos};
      bottom: ${bottomPos};
      transform: ${transform};
      width: ${width};
      font-family: '${font.name}';
      font-size: ${fontSize}px;
      font-weight: ${weight};
      color: ${color};
      text-align: ${textAlign};
      ${outline ? `text-shadow: ${buildOutlineCss(outline.color, outline.thickness)};` : ''}
      line-height: 1.1;
      white-space: pre-wrap;
    `;
  }

  // 환경별 이미지 로딩 (브라우저/Node.js 모두 지원)
  async function loadImageUniversal(url) {
    if (typeof window !== 'undefined' && window.Image) {
      // 브라우저 환경: fetch + Blob + Image
      const res = await fetch(url);
      if (!res.ok) throw new Error('이미지 다운로드 실패');
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      return new Promise((resolve, reject) => {
        const img = new window.Image();
        img.src = blobUrl;
        img.onload = () => {
          resolve(img);
          // URL.revokeObjectURL(blobUrl); // 필요시 메모리 해제
        };
        img.onerror = reject;
      });
    } else {
      // Node.js 환경: canvas의 loadImage
      const { loadImage } = require('canvas');
      return await loadImage(url);
    }
  }

  class ThumbnailRenderer {
    static getResolution(value) {
      return RESOLUTIONS[value] || RESOLUTIONS['16:9'];
    }

    static buildFontCss(texts) {
      let fontCss = '';
      texts.forEach(txt => {
        if (!Array.isArray(txt.font.faces)) return;
        txt.font.faces.forEach(f => {
          fontCss += buildFontFace(f);
        });
      });
      return fontCss;
    }

    static buildBackgroundStyle(bg) {
      if (bg.type === 'solid') {
        return `background-color: ${bg.color};`;
      } else if (bg.type === 'gradient') {
        const stops = bg.colors.map((c, i) =>
          `${c} ${(i / (bg.colors.length - 1)) * 100}%`
        ).join(', ');
        return `background: linear-gradient(90deg, ${stops});`;
      } else if (bg.type === 'image') {
        return `background-image: url('${bg.imagePath}');
        background-size: cover;
        background-position: center;`;
      }
      return '';
    }

    static buildTextLayers(texts) {
      // HTML 렌더링도 캔버스와 동일한 좌표계, cover 방식에 맞춰서
      let html = '';
      const [w, h] = [480, 270]; // 기본값, 실제 buildHtml에서 override됨
      const M = 20;
      texts.forEach(txt => {
        if (!txt.enabled) return;
        // outline thickness 기본값 보정
        if (txt.outline && (!txt.outline.thickness || isNaN(txt.outline.thickness))) txt.outline.thickness = 4;
        const lines = splitLines(txt.content);
        const size = txt.fontSize;
        const weight = txt.type === 'title' ? 'bold' : 'normal';
        const lh = size * 1.1;
        let y = txt.position.vertical === 'top' ? M
          : txt.position.vertical === 'middle' ? (h - lines.length * lh) / 2
            : h - lines.length * lh - M;
        lines.forEach(line => {
          let x = txt.position.horizontal === 'left' ? M
            : txt.position.horizontal === 'center' ? w / 2
              : w - M;
          let align = txt.position.horizontal || 'left';
          let style = `position:absolute; top:${y}px; font-family:'${txt.font.name}'; font-size:${size}px; font-weight:${weight}; color:${txt.color}; line-height:1.1; white-space:pre;`;
          if (align === 'center') {
            style += ` left:${x}px; transform:translateX(-50%); text-align:center;`;
          } else if (align === 'right') {
            style += ` left:${x}px; transform:translateX(-100%); text-align:right;`;
          } else {
            style += ` left:${x}px; text-align:left;`;
          }
          if (txt.outline) {
            style += ` text-shadow:${buildOutlineCss(txt.outline.color, txt.outline.thickness)};`;
          }
          html += `<div style="${style}">${line}</div>`;
          y += lh;
        });
      });
      return html;
    }

    static buildHtml(dsl) {
      const { Resolution, Background, Texts } = dsl.Thumbnail;
      const [w, h] = this.getResolution(Resolution.value);
      const fontCss = this.buildFontCss(Texts);
      const bgStyle = this.buildBackgroundStyle(Background);
      const textHtml = this.buildTextLayers(Texts.map(t => ({ ...t, _w: w, _h: h })));

      return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
${fontCss}
    body, html { margin:0; padding:0; }
    #thumb {
      position: relative;
      width: ${w}px;
      height: ${h}px;
      overflow: hidden;
      ${bgStyle}
    }
    #thumb div { display: block; }
  </style>
</head>
<body>
  <div id="thumb">
    ${textHtml}
  </div>
</body>
</html>`;
    }

    static async drawOnCanvas(ctx, dsl) {
      const { Resolution, Background, Texts } = dsl.Thumbnail;
      const [w, h] = this.getResolution(Resolution.value);
      ctx.canvas.width = w;
      ctx.canvas.height = h;
      // 배경
      if (Background.type === 'solid') {
        ctx.fillStyle = Background.color;
        ctx.fillRect(0, 0, w, h);
      } else if (Background.type === 'image') {
        try {
          const img = await loadImageUniversal(Background.imagePath);
          // cover 알고리즘
          const iw = img.width, ih = img.height;
          const ir = iw / ih, cr = w / h;
          let sx, sy, sw, sh;
          if (ir > cr) {
            // 이미지가 더 넓음: 좌우 잘라냄
            sh = ih;
            sw = ih * cr;
            sx = (iw - sw) / 2;
            sy = 0;
          } else {
            // 이미지가 더 높음: 상하 잘라냄
            sw = iw;
            sh = iw / cr;
            sx = 0;
            sy = (ih - sh) / 2;
          }
          ctx.drawImage(img, sx, sy, sw, sh, 0, 0, w, h);
        } catch (e) {
          ctx.fillStyle = '#ccc';
          ctx.fillRect(0, 0, w, h);
        }
      } else if (Background.type === 'gradient') {
        const grad = ctx.createLinearGradient(0, 0, w, 0);
        const stops = Background.colors;
        stops.forEach((c, i) => grad.addColorStop(i / (stops.length - 1), c));
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
      }
      // 텍스트
      const M = 20;
      Texts.forEach(txt => {
        if (!txt.enabled) return;
        // outline thickness 기본값 보정
        if (txt.outline && (!txt.outline.thickness || isNaN(txt.outline.thickness))) txt.outline.thickness = 4;
        const lines = splitLines(txt.content);
        const size = txt.fontSize;
        const weight = txt.type === 'title' ? 'bold' : 'normal';
        ctx.font = `${weight} ${size}px ${txt.font.name}`;
        ctx.textBaseline = 'top';
        if (txt.outline) { ctx.lineWidth = txt.outline.thickness; ctx.strokeStyle = txt.outline.color; }
        const lh = size * 1.1;
        let y = txt.position.vertical === 'top' ? M
          : txt.position.vertical === 'middle' ? (h - lines.length * lh) / 2
            : h - lines.length * lh - M;
        lines.forEach(line => {
          const textWidth = ctx.measureText(line).width;
          let x = txt.position.horizontal === 'left' ? M
            : txt.position.horizontal === 'center' ? (w - textWidth) / 2
              : w - textWidth - M;
          if (txt.outline) ctx.strokeText(line, x, y);
          ctx.fillStyle = txt.color;
          ctx.fillText(line, x, y);
          y += lh;
        });
      });
    }
  }

  return {
    ThumbnailRenderer,
    buildThumbnailHtml: ThumbnailRenderer.buildHtml,
    drawThumbnailOnCanvas: ThumbnailRenderer.drawOnCanvas,
    loadImageUniversal
  };
}));
