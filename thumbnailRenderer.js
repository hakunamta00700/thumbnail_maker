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
    const offsets = [[-1, 0], [0, 1], [1, 0], [0, -1]];
    return offsets.map(([dx, dy]) => `${dx}px ${dy}px 0 ${color}`).join(', ');
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
      let html = '';
      texts.forEach(txt => {
        if (!txt.enabled) return;
        const lines = splitLines(txt.content);
        const size = txt.fontSize;
        const weight = txt.type === 'title' ? 'bold' : 'normal';
        const outlineOffset = txt.outline ? (txt.outline.thickness || 2) / 2 : 0;
        const w = 480, h = 270;
        let y = 20 + outlineOffset;
        if (txt.position.vertical === 'bottom') {
          y = h - (lines.length * size * 1.1) - 20 - outlineOffset;
        } else if (txt.position.vertical === 'middle') {
          y = h / 2 - (lines.length * size * 1.1) / 2;
        }
        lines.forEach(line => {
          let x;
          if (txt.position && txt.position.horizontal === 'center') {
            x = w / 2;
          } else if (txt.position && txt.position.horizontal === 'right') {
            x = w - 20;
          } else {
            x = 20;
          }
          let textShadow = '';
          if (txt.outline) {
            const offsets = [[-1, 0], [0, 1], [1, 0], [0, -1]];
            textShadow = offsets.map(([dx, dy]) => `${dx}px ${dy}px 0 ${txt.outline.color}`).join(', ');
          }
          html += `<div style="
            position: absolute;
            left: ${x}px;
            top: ${y}px;
            font-family: '${txt.font.name}';
            font-size: ${size}px;
            font-weight: ${weight};
            color: ${txt.color};
            ${txt.position && txt.position.horizontal === 'center' ? 'text-align: center; width: 100%;' : ''}
            ${txt.position && txt.position.horizontal === 'right' ? 'text-align: right; width: 100%;' : ''}
            ${textShadow ? `text-shadow: ${textShadow};` : ''}
            line-height: 1.1;
            white-space: pre;
          ">${line}</div>`;
          y += size * 1.1;
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

    static drawOnCanvas(ctx, dsl) {
      const { Resolution, Background, Texts } = dsl.Thumbnail;
      const [w, h] = this.getResolution(Resolution.value);
      ctx.canvas.width = w;
      ctx.canvas.height = h;
      // 배경
      if (Background.type === 'solid') {
        ctx.fillStyle = Background.color;
        ctx.fillRect(0, 0, w, h);
      } else if (Background.type === 'image') {
        ctx.fillStyle = '#ccc';
        ctx.fillRect(0, 0, w, h);
      } else if (Background.type === 'gradient') {
        const grad = ctx.createLinearGradient(0, 0, w, 0);
        const stops = Background.colors;
        stops.forEach((c, i) => grad.addColorStop(i / (stops.length - 1), c));
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
      }
      // 텍스트
      Texts.forEach(txt => {
        if (!txt.enabled) return;
        const lines = splitLines(txt.content);
        const size = txt.fontSize;
        const weight = txt.type === 'title' ? 'bold' : 'normal';
        const outlineOffset = txt.outline ? (txt.outline.thickness || 2) / 2 : 0;
        ctx.font = `${weight} ${size}px ${txt.font.name}`;
        ctx.textBaseline = 'top';
        // 수평 정렬
        let x;
        ctx.textAlign = 'left';
        if (txt.position && txt.position.horizontal === 'center') {
          ctx.textAlign = 'center';
        } else if (txt.position && txt.position.horizontal === 'right') {
          ctx.textAlign = 'right';
        }
        let y = 20 + outlineOffset;
        if (txt.position.vertical === 'bottom') {
          y = h - (lines.length * size * 1.1) - 20 - outlineOffset;
        } else if (txt.position.vertical === 'middle') {
          y = h / 2 - (lines.length * size * 1.1) / 2;
        }
        lines.forEach(line => {
          if (txt.position && txt.position.horizontal === 'center') {
            x = w / 2;
          } else if (txt.position && txt.position.horizontal === 'right') {
            x = w - 20;
          } else {
            x = 20;
          }
          if (txt.outline) {
            ctx.save();
            ctx.lineWidth = typeof txt.outline.thickness === 'number' ? txt.outline.thickness : 2;
            ctx.strokeStyle = txt.outline.color || '#000';
            ctx.strokeText(line, x, y);
            ctx.restore();
          }
          ctx.fillStyle = txt.color;
          ctx.fillText(line, x, y);
          y += size * 1.1;
        });
      });
    }
  }

  return {
    ThumbnailRenderer,
    buildThumbnailHtml: ThumbnailRenderer.buildHtml,
    drawThumbnailOnCanvas: ThumbnailRenderer.drawOnCanvas
  };
}));
