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

  // ==== 상수 정의 ====
  const MARGIN = 20; // 텍스트/캔버스 여백(px)
  const LINE_HEIGHT = 1.1; // 텍스트 줄간격 배수
  const DEFAULT_OUTLINE_THICKNESS = 4; // 외곽선 기본 두께(px)

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
    thickness = thickness || DEFAULT_OUTLINE_THICKNESS;
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

  // 텍스트 한 줄의 스타일 문자열을 생성하는 헬퍼 함수
  function buildTextDivStyle({ fontFamily, fontSize, fontWeight, fontStyle, color, effectiveTextAlign, lineHeight, outline }) {
    let style = `font-family:'${fontFamily}'; font-size:${fontSize}px; font-weight:${fontWeight || 'normal'}; font-style:${fontStyle || 'normal'}; color:${color}; line-height:${lineHeight || LINE_HEIGHT}; white-space:pre; text-align:${effectiveTextAlign || 'left'};`;
    // outline은 text-shadow로 구현
    if (outline && outline.color && outline.thickness > 0) {
      style += ` text-shadow:${buildOutlineCss(outline.color, outline.thickness)};`;
    }
    return style;
  }

  class ThumbnailRenderer {
    static getResolution(dslResolutionObject) {
      // Default/Error Handling
      if (!dslResolutionObject || !dslResolutionObject.type) {
        return RESOLUTIONS['16:9']; // Default resolution
      }

      const type = dslResolutionObject.type;

      if (type === 'preset') {
        return RESOLUTIONS[dslResolutionObject.value] || RESOLUTIONS['16:9'];
      } else if (type === 'custom') {
        const w = parseInt(dslResolutionObject.width, 10);
        const h = parseInt(dslResolutionObject.height, 10);
        if (!isNaN(w) && w > 0 && !isNaN(h) && h > 0) {
          return [w, h];
        }
        return RESOLUTIONS['16:9']; // Fallback for invalid custom dimensions
      } else if (type === 'fixedRatio') {
        const ratioString = dslResolutionObject.ratioValue;
        if (!ratioString || typeof ratioString !== 'string') {
          return RESOLUTIONS['16:9']; // Fallback
        }
        const parts = ratioString.split(':');
        if (parts.length !== 2) {
          return RESOLUTIONS['16:9']; // Fallback
        }
        const rW = parseFloat(parts[0]);
        const rH = parseFloat(parts[1]);
        if (isNaN(rW) || isNaN(rH) || rW <= 0 || rH <= 0) {
          return RESOLUTIONS['16:9']; // Fallback
        }
        const numericRatio = rW / rH;
        let calcWidth, calcHeight;

        if (dslResolutionObject.width != null) {
          calcWidth = parseInt(dslResolutionObject.width, 10);
          if (isNaN(calcWidth) || calcWidth <= 0) {
            return RESOLUTIONS['16:9']; // Fallback
          }
          calcHeight = Math.round(calcWidth / numericRatio);
        } else if (dslResolutionObject.height != null) {
          calcHeight = parseInt(dslResolutionObject.height, 10);
          if (isNaN(calcHeight) || calcHeight <= 0) {
            return RESOLUTIONS['16:9']; // Fallback
          }
          calcWidth = Math.round(calcHeight * numericRatio);
        } else {
          return RESOLUTIONS['16:9']; // Fallback if neither width nor height provided
        }

        if (calcWidth > 0 && calcHeight > 0) {
          return [calcWidth, calcHeight];
        }
        return RESOLUTIONS['16:9']; // Fallback for invalid calculated dimensions
      }

      // Final fallback for unknown type or other issues
      return RESOLUTIONS['16:9'];
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
        // Styles for the dedicated background image div
        return `width:100%; height:100%; background-image: url('${bg.imagePath}'); background-size: cover; background-position: center; opacity: ${typeof bg.imageOpacity === 'number' ? bg.imageOpacity : 1.0}; filter: blur(${bg.imageBlur || 0}px);`;
      }
      return '';
    }

    static buildTextLayers(texts) {
      // HTML 렌더링도 캔버스와 동일한 좌표계, cover 방식에 맞춰서
      let html = '';
      const [w, h] = [480, 270]; // 기본값, 실제 buildHtml에서 override됨
      const M = MARGIN;
      texts.forEach(txt => {
        if (!txt.enabled) return;
        // outline thickness 기본값 보정
        if (txt.outline && (!txt.outline.thickness || isNaN(txt.outline.thickness))) txt.outline.thickness = DEFAULT_OUTLINE_THICKNESS;
        const lines = splitLines(txt.content);
        const fontSize = txt.fontSize;
        const fontFamily = txt.font.name;
        const currentLineHeight = txt.lineHeight || LINE_HEIGHT;
        // const lineHeightPx = fontSize * currentLineHeight; // Not directly used here for y positioning of block

        const gridPosition = txt.gridPosition || 'tl'; // Default to top-left
        const row = gridPosition[0]; // t, m, b
        const col = gridPosition[1]; // l, c, r

        let blockStyle = 'position: absolute;';
        let effectiveTextAlign = 'left';

        // Determine block horizontal position and text-align
        if (col === 'l') {
          blockStyle += `left: ${M}px;`;
          effectiveTextAlign = 'left';
        } else if (col === 'c') {
          blockStyle += `left: 50%;`; // translateX will be added
          effectiveTextAlign = 'center';
        } else { // col === 'r'
          blockStyle += `right: ${M}px;`;
          effectiveTextAlign = 'right';
        }

        // Determine block vertical position
        if (row === 't') {
          blockStyle += `top: ${M}px;`;
        } else if (row === 'm') {
          blockStyle += `top: 50%;`; // translateY will be added
        } else { // row === 'b'
          blockStyle += `bottom: ${M}px;`;
        }
        
        // Add transforms for centering
        let transformValue = '';
        if (row === 'm' && col === 'c') {
            transformValue = 'translate(-50%, -50%)';
        } else if (row === 'm') {
            transformValue = 'translateY(-50%)';
        } else if (col === 'c') {
            transformValue = 'translateX(-50%)';
        }
        if (transformValue) {
            blockStyle += `transform: ${transformValue};`;
        }
        
        html += `<div style="${blockStyle}">`;
        lines.forEach(line => {
          const lineStyle = buildTextDivStyle({
            fontFamily: fontFamily,
            fontSize,
            fontWeight: txt.fontWeight,
            fontStyle: txt.fontStyle,
            color: txt.color,
            effectiveTextAlign: effectiveTextAlign,
            lineHeight: currentLineHeight,
            outline: txt.outline
          });
          html += `<div style="${lineStyle}">${line}</div>`;
        });
        html += `</div>`;
      });
      return html;
    }

    static buildHtml(dsl) {
      const { Resolution, Background, Texts } = dsl.Thumbnail;
      const [w, h] = this.getResolution(Resolution); // Updated call
      const fontCss = this.buildFontCss(Texts);
      const bgStyle = this.buildBackgroundStyle(Background); // This now returns specific styles based on type
      const textHtml = this.buildTextLayers(Texts.map(t => ({ ...t, _w: w, _h: h })));

      let bgImageHtml = '';
      if (Background.type === 'image') {
        bgImageHtml = `
    <div id="thumb-bg-image-container" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:0;">
      <div id="thumb-bg-image" style="${bgStyle}"></div>
    </div>`;
      }

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
      ${Background.type !== 'image' ? bgStyle : ''}
    }
    /* Text layers will be direct children of #thumb or within a container that is a direct child.
       If they are direct children, they will stack on top of #thumb-bg-image-container due to z-index:0 on the container.
       If text layers are wrapped, ensure that wrapper also has a z-index or is positioned.
       The current buildTextLayers creates divs that are direct children, so this should be fine. */
    #thumb div { display: block; } /* This might need adjustment if text layers need explicit stacking context */
  </style>
</head>
<body>
  <div id="thumb">
    ${bgImageHtml}
    ${textHtml}
  </div>
</body>
</html>`;
    }

    static async drawOnCanvas(ctx, dsl) {
      const { Resolution, Background, Texts } = dsl.Thumbnail;
      const [w, h] = this.getResolution(Resolution); // Updated call
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
          const originalAlpha = ctx.globalAlpha;
          const originalFilter = ctx.filter;
          ctx.globalAlpha = typeof Background.imageOpacity === 'number' ? Background.imageOpacity : 1.0;
          ctx.filter = Background.imageBlur ? `blur(${Background.imageBlur}px)` : 'none';
          
          ctx.drawImage(img, sx, sy, sw, sh, 0, 0, w, h);
          
          ctx.globalAlpha = originalAlpha;
          ctx.filter = originalFilter;
        } catch (e) {
          console.error("Error loading or drawing background image:", e);
          ctx.fillStyle = '#ccc'; // Fallback color
          ctx.fillRect(0, 0, w, h);
          // Ensure context is reset even if image loading fails and we draw fallback
          if (typeof originalAlpha !== 'undefined') ctx.globalAlpha = originalAlpha;
          if (typeof originalFilter !== 'undefined') ctx.filter = originalFilter;
        }
      } else if (Background.type === 'gradient') {
        const grad = ctx.createLinearGradient(0, 0, w, 0);
        const stops = Background.colors;
        stops.forEach((c, i) => grad.addColorStop(i / (stops.length - 1), c));
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
      }
      // 텍스트
      const M = MARGIN;
      Texts.forEach(txt => {
        if (!txt.enabled) return;
        // outline thickness 기본값 보정
        if (txt.outline && (!txt.outline.thickness || isNaN(txt.outline.thickness))) txt.outline.thickness = DEFAULT_OUTLINE_THICKNESS;
        const lines = splitLines(txt.content);
        const size = txt.fontSize;
        const currentFontWeight = txt.fontWeight || 'normal';
        const currentFontStyle = txt.fontStyle || 'normal';
        // textAlign is now derived from gridPosition
        const currentLineHeight = txt.lineHeight || LINE_HEIGHT;

        ctx.font = `${currentFontStyle} ${currentFontWeight} ${size}px ${txt.font.name}`;
        ctx.textBaseline = 'top'; // Set for all cases

        if (txt.outline && txt.outline.color && txt.outline.thickness > 0) {
             ctx.lineWidth = txt.outline.thickness;
             ctx.strokeStyle = txt.outline.color;
        } else {
            ctx.lineWidth = 0;
            ctx.strokeStyle = 'transparent';
        }

        const lh = size * currentLineHeight;
        const totalTextHeight = lines.length * lh;
        
        const gridPosition = txt.gridPosition || 'tl'; // Default to top-left
        const row = gridPosition[0]; // t, m, b
        const col = gridPosition[1]; // l, c, r

        let targetX;
        let canvasTextAlign;

        if (col === 'l') {
          canvasTextAlign = 'left';
          targetX = M;
        } else if (col === 'c') {
          canvasTextAlign = 'center';
          targetX = w / 2;
        } else { // col === 'r'
          canvasTextAlign = 'right';
          targetX = w - M;
        }
        ctx.textAlign = canvasTextAlign;

        let baseY;
        if (row === 't') {
          baseY = M;
        } else if (row === 'm') {
          baseY = (h / 2) - (totalTextHeight / 2);
        } else { // row === 'b'
          baseY = h - M - totalTextHeight;
        }

        lines.forEach((line, lineIndex) => {
          const currentY = baseY + (lineIndex * lh);
          if (txt.outline && txt.outline.color && txt.outline.thickness > 0) {
            ctx.strokeText(line, targetX, currentY);
          }
          ctx.fillStyle = txt.color;
          ctx.fillText(line, targetX, currentY);
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
