#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ThumbnailRenderer } = require('./thumbnailRenderer');

async function main() {
    // 인자 파싱
    const args = process.argv.slice(2);
    let dslPath = 'thumbnail.json', outPath = 'thumbnail.png', title = null, subtitle = null;
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--title' && args[i + 1]) { title = args[i + 1]; i++; continue; }
        if (args[i] === '--subtitle' && args[i + 1]) { subtitle = args[i + 1]; i++; continue; }
        if (!dslPath || dslPath === 'thumbnail.json') { dslPath = args[i]; continue; }
        if (!outPath || outPath === 'thumbnail.png') { outPath = args[i]; continue; }
    }
    if (!fs.existsSync(dslPath)) throw new Error(`DSL 파일 없음: ${dslPath}`);
    const dsl = JSON.parse(fs.readFileSync(dslPath, 'utf-8'));
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
}

main().catch(e => { console.error(e); process.exit(1); });
