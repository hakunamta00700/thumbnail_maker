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
  function buildTextDivStyle({ x, y, fontFamily, fontSize, fontWeight, fontStyle, color, textAlign, lineHeight, outline }) {
    let style = `position:absolute; top:${y}px; left:${x}px; font-family:'${fontFamily}'; font-size:${fontSize}px; font-weight:${fontWeight || 'normal'}; font-style:${fontStyle || 'normal'}; color:${color}; line-height:${lineHeight || LINE_HEIGHT}; white-space:pre; text-align:${textAlign || 'left'};`;
    if (textAlign === 'center') {
      style += `transform:translateX(-50%);`;
    } else if (textAlign === 'right') {
      style += `transform:translateX(-100%);`;
    }
    // outline은 text-shadow로 구현
    if (outline && outline.color && outline.thickness > 0) {
      style += ` text-shadow:${buildOutlineCss(outline.color, outline.thickness)};`;
    }
    return style;
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
      const M = MARGIN;
      texts.forEach(txt => {
        if (!txt.enabled) return;
        // outline thickness 기본값 보정
        if (txt.outline && (!txt.outline.thickness || isNaN(txt.outline.thickness))) txt.outline.thickness = DEFAULT_OUTLINE_THICKNESS;
        const lines = splitLines(txt.content);
        const fontSize = txt.fontSize;
        const fontFamily = txt.font.name;
        // fontWeight는 DSL에서 직접 받아옴, 기본값 'normal'
        // const fontWeight = txt.type === 'title' ? 'bold' : 'normal'; // 기존 로직 제거
        const currentLineHeight = txt.lineHeight || LINE_HEIGHT;
        const lineHeightPx = fontSize * currentLineHeight;
        const currentTextAlign = txt.textAlign || 'left';

        let y = txt.position.vertical === 'top' ? M
          : txt.position.vertical === 'middle' ? (txt._h - lines.length * lineHeightPx) / 2 // _h 사용
            : txt._h - lines.length * lineHeightPx - M; // _h 사용

        lines.forEach(line => {
          // x 좌표 계산: DSL의 textAlign 속성 사용
          let x = currentTextAlign === 'left' ? M
            : currentTextAlign === 'center' ? txt._w / 2 // _w 사용
              : txt._w - M; // _w 사용

          const style = buildTextDivStyle({
            x,
            y,
            fontFamily: fontFamily, // 변경: font -> fontFamily
            fontSize,
            fontWeight: txt.fontWeight, // DSL에서 직접 전달
            fontStyle: txt.fontStyle,   // DSL에서 직접 전달
            color: txt.color,
            textAlign: currentTextAlign, // 변경: align -> textAlign
            lineHeight: currentLineHeight, // DSL에서 직접 전달
            outline: txt.outline
          });
          html += `<div style="${style}">${line}</div>`;
          y += lineHeightPx;
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
      const M = MARGIN;
      Texts.forEach(txt => {
        if (!txt.enabled) return;
        // outline thickness 기본값 보정
        if (txt.outline && (!txt.outline.thickness || isNaN(txt.outline.thickness))) txt.outline.thickness = DEFAULT_OUTLINE_THICKNESS;
        const lines = splitLines(txt.content);
        const size = txt.fontSize;
        // fontWeight, fontStyle, textAlign, lineHeight는 DSL에서 직접 받아옴
        const currentFontWeight = txt.fontWeight || 'normal';
        const currentFontStyle = txt.fontStyle || 'normal';
        const currentTextAlign = txt.textAlign || 'left';
        const currentLineHeight = txt.lineHeight || LINE_HEIGHT;

        ctx.font = `${currentFontStyle} ${currentFontWeight} ${size}px ${txt.font.name}`;
        ctx.textAlign = currentTextAlign;
        ctx.textBaseline = 'top';

        if (txt.outline && txt.outline.color && txt.outline.thickness > 0) {
             ctx.lineWidth = txt.outline.thickness;
             ctx.strokeStyle = txt.outline.color;
        } else {
            // Ensure outline is not applied if not specified or thickness is 0
            ctx.lineWidth = 0;
            ctx.strokeStyle = 'transparent';
        }

        const lh = size * currentLineHeight;
        let y = txt.position.vertical === 'top' ? M
          : txt.position.vertical === 'middle' ? (h - lines.length * lh) / 2
            : h - lines.length * lh - M;

        lines.forEach(line => {
          // x 좌표 계산: ctx.textAlign을 활용
          let x;
          if (currentTextAlign === 'left') {
            x = M;
          } else if (currentTextAlign === 'center') {
            x = w / 2;
          } else { // right
            x = w - M;
          }

          if (txt.outline && txt.outline.color && txt.outline.thickness > 0) {
            ctx.strokeText(line, x, y);
          }
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
