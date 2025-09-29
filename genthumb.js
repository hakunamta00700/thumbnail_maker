#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ThumbnailRenderer } = require('./thumbnailRenderer');

async function main() {
    // 인자 파싱
    const args = process.argv.slice(2);
    let dslPath = 'thumbnail.json', outPath = 'thumbnail.png', title = null, subtitle = null, bgImg = null, upload = false;

    // 도움말 메시지
    const helpMessage = `
Usage: node genthumb.js [options] [dslPath] [outPath]

Generate thumbnail from DSL file using Playwright.

Arguments:
  dslPath    Path to DSL JSON file (default: thumbnail.json)
  outPath    Output PNG file path (default: thumbnail.png)

Options:
  --title <text>       Override title text in DSL
  --subtitle <text>    Override subtitle text in DSL
  --bgImg <path>       Set background image path (base64 encoded)
  --upload             Upload the generated thumbnail to a random hosting service
  --help               Show this help message

Examples:
  node genthumb.js
  node genthumb.js mydsl.json output.png
  node genthumb.js --title "New Title" --bgImg bg.png --upload
`;

    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--help') {
            console.log(helpMessage);
            process.exit(0);
        }
        if (args[i] === '--title' && args[i + 1]) { title = args[i + 1]; i++; continue; }
        if (args[i] === '--subtitle' && args[i + 1]) { subtitle = args[i + 1]; i++; continue; }
        if (args[i] === '--bgImg' && args[i + 1]) { bgImg = args[i + 1]; i++; continue; }
        if (args[i] === '--upload') { upload = true; continue; }
        if (!dslPath || dslPath === 'thumbnail.json') { dslPath = args[i]; continue; }
        if (!outPath || outPath === 'thumbnail.png') { outPath = args[i]; continue; }
    }
    if (!fs.existsSync(dslPath)) throw new Error(`DSL 파일 없음: ${dslPath}`);
    const dsl = JSON.parse(fs.readFileSync(dslPath, 'utf-8'));
    // 배경이미지의 base64 인코딩   
    if (bgImg) {
        const base64 = fs.readFileSync(bgImg, 'base64');
        bgImg = `data:image/png;base64,${base64}`;
        dsl.Thumbnail.Background.type = 'image';
        dsl.Thumbnail.Background.imagePath = bgImg;
    }

    // 제목/부제목 덮어쓰기
    if (title || subtitle) {
        if (Array.isArray(dsl.Thumbnail.Texts)) {
            dsl.Thumbnail.Texts.forEach(t => {
                if (title && t.type === 'title') t.content = title;
                if (subtitle && t.type === 'subtitle') t.content = subtitle;
            });
        }
    }
    const html = ThumbnailRenderer.buildHtml(dsl);
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: null });
    await page.setContent(html, { waitUntil: 'networkidle' });
    const thumb = await page.$('#thumb');
    await thumb.screenshot({ path: outPath });
    await browser.close();
    console.log(`✅ 생성됨: ${outPath}`);

    if (upload) {
        const fs = require('fs');
        const { uploadSingleImage } = require('./img_upload.js');
        const imgBuffer = fs.readFileSync(outPath);
        const uploadUrl = await uploadSingleImage(imgBuffer);
        if (uploadUrl) {
            console.log(`📤 업로드됨: ${uploadUrl}`);
        } else {
            console.error('업로드 실패');
        }
    }
}

main().catch(e => { console.error(e); process.exit(1); });
