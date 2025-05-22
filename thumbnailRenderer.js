// thumbnailRenderer.js
// DSL 기반 썸네일 렌더링 공통 모듈

// Node.js/브라우저 모두 지원 (UMD 패턴)
(function (root, factory) {
  if (typeof module === 'object' && typeof module.exports === 'object') {
    module.exports = factory();
  } else {
    root.thumbnailRenderer = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {

  function buildThumbnailHtml(dsl) {
    const { Resolution, Background, Texts } = dsl.Thumbnail;
    const [w, h] = (() => {
      switch (Resolution.value) {
        case '16:9': return [480, 270];
        case '9:16': return [270, 480];
        case '4:3':  return [480, 360];
        case '1:1':  return [360, 360];
        default: throw new Error(`Unknown resolution: ${Resolution.value}`);
      }
    })();

    // font-face CSS
    let fontCss = '';
    Texts.forEach(txt => {
      if (!Array.isArray(txt.font.faces)) return;
      txt.font.faces.forEach(f => {
        fontCss += `@font-face {\n  font-family: '${f.name}';\n  src: url('${f.url}') format('woff2');\n  font-weight: ${f.weight};\n  font-style: ${f.style};\n}\n`;
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
      bgStyle = `background-image: url('${Background.imagePath}');\n        background-size: cover;\n        background-position: center;`;
    }

    // text layers
    let textHtml = '';
    Texts.forEach(txt => {
      if (!txt.enabled) return;
      const lines = txt.content.split(/\\n|\r\n|\r|\n/);
      const weight = txt.type === 'title' ? 'bold' : 'normal';
      const size = txt.fontSize;
      // outline shadows: use defined offsets
      let outlineCss = '';
      if (txt.outline) {
        const offsets = [[-1,0],[0,1],[1,0],[0,-1]];
        outlineCss = offsets.map(o => `${o[0]}px ${o[1]}px 0 ${txt.outline.color}`).join(', ');
      }

      const verticalPos = {
        top: '10px',
        middle: '50%',
        bottom: 'auto'
      }[txt.position.vertical];
      const bottomPos = txt.position.vertical === 'bottom' ? '10px' : 'auto';
      const transform = txt.position.vertical === 'middle' ? 'translateY(-50%)' : '';

      textHtml += `\n<div style="\n  position: absolute;\n  left: 10px;\n  top: ${verticalPos};\n  bottom: ${bottomPos};\n  transform: ${transform};\n  width: calc(100% - 20px);\n  font-family: '${txt.font.name}';\n  font-size: ${size}px;\n  font-weight: ${weight};\n  color: ${txt.color};\n  ${outlineCss ? `text-shadow: ${outlineCss};` : ''}\n  line-height: 1.1;\n  white-space: pre-wrap;\n">${
        lines.map(line => `<div>${line}</div>`).join('')
      }</div>`;
    });

    return `<!DOCTYPE html>\n<html>\n<head>\n  <meta charset=\"UTF-8\">\n  <style>\n${fontCss}
    body, html { margin:0; padding:0; }\n    #thumb {\n      position: relative;\n      width: ${w}px;\n      height: ${h}px;\n      overflow: hidden;\n      ${bgStyle}\n    }\n    #thumb div { display: block; }\n  </style>\n</head>\n<body>\n  <div id=\"thumb\">\n    ${textHtml}\n  </div>\n</body>\n</html>`;
  }

  // Canvas 렌더링 함수 (브라우저에서만 동작)
  function drawThumbnailOnCanvas(ctx, dsl) {
    const { Resolution, Background, Texts } = dsl.Thumbnail;
    const sizeMap = { '16:9':[480,270], '9:16':[270,480], '4:3':[480,360], '1:1':[360,360] };
    const [w, h] = sizeMap[Resolution.value] || [480, 270];
    ctx.canvas.width = w;
    ctx.canvas.height = h;
    // 배경
    if (Background.type === 'solid') {
      ctx.fillStyle = Background.color;
      ctx.fillRect(0, 0, w, h);
    } else if (Background.type === 'image') {
      // 이미지는 비동기 로딩 필요, 여기선 동기화 불가. (index.html에서 따로 처리 필요)
      ctx.fillStyle = '#ccc';
      ctx.fillRect(0, 0, w, h);
    } else if (Background.type === 'gradient') {
      const grad = ctx.createLinearGradient(0, 0, w, 0);
      const stops = Background.colors;
      stops.forEach((c, i) => grad.addColorStop(i/(stops.length-1), c));
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
    }
    // 텍스트
    Texts.forEach(txt => {
      if (!txt.enabled) return;
      const lines = txt.content.split(/\\n|\r\n|\r|\n/);
      const size = txt.fontSize;
      const weight = txt.type === 'title' ? 'bold' : 'normal';
      ctx.font = `${weight} ${size}px ${txt.font.name}`;
      ctx.textBaseline = 'top';
      ctx.textAlign = 'left';
      let x = 10, y = 10;
      if (txt.position.vertical === 'bottom') {
        y = h - (lines.length * size * 1.1) - 10;
      } else if (txt.position.vertical === 'middle') {
        y = h/2 - (lines.length * size * 1.1)/2;
      }
      lines.forEach(line => {
        if (txt.outline) {
          ctx.save();
          ctx.lineWidth = txt.outline.thickness || 2;
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

  return {
    buildThumbnailHtml,
    drawThumbnailOnCanvas
  };

})); 