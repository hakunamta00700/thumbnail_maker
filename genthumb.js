#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ThumbnailRenderer } = require('./thumbnailRenderer');

async function main() {
    const [, , dslPath = 'thumbnail.json', outPath = 'thumbnail.png'] = process.argv;
    if (!fs.existsSync(dslPath)) throw new Error(`DSL 파일 없음: ${dslPath}`);
    const dsl = JSON.parse(fs.readFileSync(dslPath, 'utf-8'));

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
