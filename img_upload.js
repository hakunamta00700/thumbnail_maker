#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');
const axios = require('axios');
const FormData = require('form-data');

// --- 기본 설정 --- //

const SAVE_DIR = path.join(os.tmpdir(), 'downloaded_images');
if (!fs.existsSync(SAVE_DIR)) {
  fs.mkdirSync(SAVE_DIR, { recursive: true });
}
const MAX_CONCURRENT_DOWNLOADS = 5;
const MAX_CONCURRENT_UPLOADS = 5;

// --- 유틸리티 함수들 --- //

function getFilenameFromUrl(url) {
  const urlObj = new URL(url);
  let filename = path.basename(urlObj.pathname);
  if ((!filename || !filename.includes('.')) && urlObj.search) {
    const params = new URLSearchParams(urlObj.search);
    for (const key of ['fname', 'filename', 'file']) {
      if (params.has(key)) {
        const potential = path.basename(params.get(key));
        if (potential && potential.includes('.')) {
          filename = potential;
          break;
        }
      }
    }
  }
  if (!filename || filename === '.' || filename.includes('/')) {
    const timestamp = Date.now().toString();
    const ext = path.extname(urlObj.pathname) || '.jpg';
    filename = `image_${timestamp}${ext}`;
    console.warn(`Could not determine filename for ${url}, using default: ${filename}`);
  }
  filename = filename.replace(/[<>:"\/\\|?*]/g, '_');
  const maxLen = 200;
  if (filename.length > maxLen) {
    const namePart = path.basename(filename, path.extname(filename));
    const extPart = path.extname(filename);
    const allowedLen = maxLen - extPart.length;
    filename = namePart.substring(0, allowedLen) + extPart;
    console.warn(`Filename truncated for ${url} -> ${filename}`);
  }
  return filename;
}

function getImgExt(img) {
  if (!img || img.length === 0) return 'bin';
  if (img.slice(0, 2).equals(Buffer.from([0xFF, 0xD8]))) return 'jpg';
  if (img.slice(0, 8).equals(Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]))) return 'png';
  if (img.slice(0, 6).equals(Buffer.from('GIF87a')) || img.slice(0, 6).equals(Buffer.from('GIF89a'))) return 'gif';
  if (img.length > 12 && img.slice(0, 4).equals(Buffer.from('RIFF')) && img.slice(8, 12).equals(Buffer.from('WEBP'))) return 'webp';
  if (img.slice(0, 2).equals(Buffer.from([0x42, 0x4D]))) return 'bmp';
  if (img.slice(0, 4).equals(Buffer.from([0x49, 0x49, 0x2A, 0x00])) || img.slice(0, 4).equals(Buffer.from([0x4D, 0x4D, 0x00, 0x2A]))) return 'tiff';
  return 'bin';
}

function logOnError(response) {
  console.error(`Request failed: [${response.status}] ${response.config.method.toUpperCase()} ${response.config.url}`);
  try {
    console.debug(`Response Body: ${response.data.substring(0, 500)}...`);
  } catch (e) {
    console.warn(`Could not log response body: ${e.message}`);
  }
}

// --- 개별 업로드 함수들 --- //

async function anhmoeUpload(img) {
  try {
    const form = new FormData();
    form.append('key', 'anh.moe_public_api');
    form.append('source', img, { filename: 'image.jpg' });
    const response = await axios.post('https://anh.moe/api/1/upload', form, {
      headers: form.getHeaders(),
      timeout: 60000,
    });
    return response.data.image.url;
  } catch (e) {
    if (e.response) logOnError(e.response);
    return null;
  }
}

async function beeimgUpload(img) {
  const ext = getImgExt(img);
  if (ext === 'bin') {
    console.warn('Beeimg: Skip unknown ext');
    return null;
  }
  const name = `image.${ext}`;
  const contentType = `image/${ext}`;
  console.debug(`Beeimg: Uploading ${name} type: ${contentType}`);
  try {
    const form = new FormData();
    form.append('file', img, { filename: name, contentType });
    const response = await axios.post('https://beeimg.com/api/upload/file/json/', form, {
      headers: form.getHeaders(),
      timeout: 60000,
    });
    const relativeUrl = response.data.files?.url;
    if (relativeUrl) {
      return relativeUrl.startsWith('//') ? `https:${relativeUrl}` : relativeUrl;
    } else {
      console.error(`beeimg missing URL: ${response.data}`);
      return null;
    }
  } catch (e) {
    if (e.response) logOnError(e.response);
    return null;
  }
}

async function fastpicUpload(img) {
  try {
    const form = new FormData();
    form.append('method', 'file');
    form.append('check_thumb', 'no');
    form.append('uploading', '1');
    form.append('file1', img, { filename: 'image.jpg' });
    const response = await axios.post('https://fastpic.org/upload?api=1', form, {
      headers: form.getHeaders(),
      timeout: 60000,
    });
    const match = response.data.match(/<imagepath>(.+?)<\/imagepath>/);
    if (match) {
      return match[1].trim();
    } else {
      console.error(`fastpic missing imagepath: ${response.data}`);
      return null;
    }
  } catch (e) {
    if (e.response) logOnError(e.response);
    return null;
  }
}

async function imagebinUpload(img) {
  try {
    const form = new FormData();
    form.append('file', img, { filename: 'image.jpg' });
    const response = await axios.post('https://imagebin.ca/upload.php', form, {
      headers: form.getHeaders(),
      timeout: 60000,
    });
    const match = response.data.match(/url:\s*(.+?)$/m);
    if (match) {
      return match[1].trim();
    } else {
      console.error(`imagebin missing URL pattern: ${response.data}`);
      return null;
    }
  } catch (e) {
    if (e.response) logOnError(e.response);
    return null;
  }
}

async function pixhostUpload(img) {
  try {
    const form = new FormData();
    form.append('content_type', '0');
    form.append('img', img, { filename: 'image.jpg' });
    const response = await axios.post('https://api.pixhost.to/images', form, {
      headers: form.getHeaders(),
      timeout: 60000,
    });
    const jsonResponse = response.data;
    const showUrl = jsonResponse.show_url;
    const directImageUrl = jsonResponse.url;
    const result = directImageUrl || showUrl;
    if (result) {
      return result;
    } else {
      console.error(`pixhost missing URL/show_url: ${JSON.stringify(jsonResponse)}`);
      return null;
    }
  } catch (e) {
    if (e.response) {
      if (e.response.status === 414) {
        console.error(`Pixhost 414 type: ${getImgExt(img)}`);
      }
      logOnError(e.response);
    } else {
      console.error(`Pixhost request failed: ${e.message}`);
    }
    return null;
  }
}

async function sxcuUpload(img, retryDelay = 5) {
  const headers = { 'User-Agent': 'Mozilla/5.0' };
  try {
    let response = await axios.post('https://sxcu.net/api/files/create', img, {
      headers: { ...headers, 'Content-Type': 'application/octet-stream' },
      timeout: 60000,
    });
    if (response.status === 429) {
      console.warn(`Sxcu rate limit (429). Wait ${retryDelay}s...`);
      await new Promise(resolve => setTimeout(resolve, retryDelay * 1000));
      console.info('Retrying sxcu upload...');
      response = await axios.post('https://sxcu.net/api/files/create', img, {
        headers: { ...headers, 'Content-Type': 'application/octet-stream' },
        timeout: 60000,
      });
    }
    const baseUrl = response.data.url;
    if (baseUrl) {
      return baseUrl;
    } else {
      console.error(`sxcu missing URL/error: ${response.data.error || 'Unknown'} - Resp: ${response.data}`);
      return null;
    }
  } catch (e) {
    if (e.response) logOnError(e.response);
    else console.error(`sxcu request failed: ${e.message}`);
    return null;
  }
}

// --- 업로드 대상 서비스 모음 --- //

const UPLOAD_TARGETS = {
  anhmoe: anhmoeUpload,
  beeimg: beeimgUpload,
  fastpic: fastpicUpload,
  imagebin: imagebinUpload,
  pixhost: pixhostUpload,
  sxcu: sxcuUpload,
};

// --- 새로운 파이프라인 구조 --- //

async function downloadImageTask(semaphore, url, downloadCompleteQueue, resultsDict, resultsLock) {
  let filepath = null;
  await semaphore.acquire();
  try {
    const filename = getFilenameFromUrl(url);
    filepath = path.join(SAVE_DIR, filename);
    console.info(`Attempting download: ${url} -> ${filepath}`);
    const response = await axios.get(url, { responseType: 'arraybuffer', timeout: 60000 });
    fs.writeFileSync(filepath, Buffer.from(response.data));
    console.log(`[✓] Downloaded: ${url} -> ${filepath}`);
    await downloadCompleteQueue.put({ url, filepath });
  } catch (e) {
    console.error(`[✗] Failed dl/save ${url}: ${e.message}`);
    await resultsLock.acquire();
    resultsDict[url] = null;
    resultsLock.release();
    if (filepath) {
      try { fs.unlinkSync(filepath); } catch {}
    }
  } finally {
    semaphore.release();
  }
}

async function uploadDispatcherTask(downloadCompleteQueue, uploadJobQueue, targets) {
  console.info('Upload Dispatcher started.');
  const serviceNames = Object.keys(targets);
  let serviceIndex = 0;
  while (true) {
    const item = await downloadCompleteQueue.take();
    if (item === null) {
      console.info('Dispatcher received null from download queue. Signaling workers to terminate.');
      for (let i = 0; i < MAX_CONCURRENT_UPLOADS; i++) {
        await uploadJobQueue.put(null);
      }
      break;
    }
    const { url, filepath } = item;
    if (!fs.existsSync(filepath)) {
      console.error(`Dispatcher received invalid/missing file: ${filepath} for url ${url}. Skipping.`);
      continue;
    }
    const serviceName = serviceNames[serviceIndex % serviceNames.length];
    serviceIndex++;
    console.info(`Dispatcher assigning ${path.basename(filepath)} (from ${url}) to service [${serviceName}]`);
    await uploadJobQueue.put({ url, filepath, serviceName, uploadFunc: targets[serviceName] });
  }
  console.info('Upload Dispatcher finished.');
}

async function uploadWorkerTask(workerId, semaphore, uploadJobQueue, resultsDict, resultsLock) {
  console.info(`Upload Worker-${workerId} started.`);
  while (true) {
    const job = await uploadJobQueue.take();
    if (job === null) {
      console.info(`Upload Worker-${workerId} received null, terminating.`);
      break;
    }
    const { url, filepath, serviceName, uploadFunc } = job;
    console.info(`Worker-${workerId}: Processing ${path.basename(filepath)} (from ${url}) for service [${serviceName}]`);
    let resultUrl = null;
    await semaphore.acquire();
    try {
      if (!fs.existsSync(filepath)) {
        console.error(`Worker-${workerId}: File not found for upload: ${filepath}. Skipping.`);
      } else {
        const imgData = fs.readFileSync(filepath);
        if (!imgData.length) {
          console.warn(`Worker-${workerId}: File is empty: ${filepath}. Skipping.`);
        } else {
          console.debug(`Worker-${workerId}: Calling ${uploadFunc.name} for ${path.basename(filepath)}`);
          resultUrl = await uploadFunc(imgData);
        }
      }
      if (resultUrl) {
        await resultsLock.acquire();
        resultsDict[url] = resultUrl;
        resultsLock.release();
        console.log(`[✓] Uploaded [${path.basename(filepath)}] to [${serviceName}]: ${resultUrl} (Orig: ${url})`);
      } else {
        console.warn(`[✗] Upload failed for ${path.basename(filepath)} to [${serviceName}] (Orig: ${url}).`);
      }
    } catch (e) {
      console.error(`Worker-${workerId}: Unexpected error processing ${filepath} for ${serviceName}: ${e.message}`);
    } finally {
      semaphore.release();
    }
  }
  console.info(`Upload Worker-${workerId} finished.`);
}

async function downloadAndUploadPipeline(urls) {
  if (!urls || !urls.length) {
    console.warn('No URLs provided.');
    return {};
  }
  if (!Object.keys(UPLOAD_TARGETS).length) {
    console.error('No upload targets defined.');
    return {};
  }

  // 간단한 큐 구현 (배열 사용)
  class Queue {
    constructor() { this.items = []; this.waiting = []; }
    async put(item) { this.items.push(item); if (this.waiting.length) this.waiting.shift()(); }
    async take() { if (!this.items.length) await new Promise(resolve => this.waiting.push(resolve)); return this.items.shift(); }
  }

  class Semaphore {
    constructor(count) { this.count = count; this.waiting = []; }
    async acquire() { if (this.count > 0) this.count--; else await new Promise(resolve => this.waiting.push(resolve)); }
    release() { this.count++; if (this.waiting.length) this.waiting.shift()(); }
  }

  class Lock {
    constructor() { this.locked = false; this.waiting = []; }
    async acquire() { if (this.locked) await new Promise(resolve => this.waiting.push(resolve)); this.locked = true; }
    release() { this.locked = false; if (this.waiting.length) this.waiting.shift()(); }
  }

  const downloadCompleteQueue = new Queue();
  const uploadJobQueue = new Queue();
  const downloadSemaphore = new Semaphore(MAX_CONCURRENT_DOWNLOADS);
  const uploadSemaphore = new Semaphore(MAX_CONCURRENT_UPLOADS);
  const resultsDict = {};
  const resultsLock = new Lock();

  // 디스패처 시작
  uploadDispatcherTask(downloadCompleteQueue, uploadJobQueue, UPLOAD_TARGETS);

  // 워커 시작
  for (let i = 0; i < MAX_CONCURRENT_UPLOADS; i++) {
    uploadWorkerTask(i, uploadSemaphore, uploadJobQueue, resultsDict, resultsLock);
  }

  // 다운로드 태스크
  const downloadPromises = urls.filter(url => typeof url === 'string' && url.startsWith('http')).map(url =>
    downloadImageTask(downloadSemaphore, url, downloadCompleteQueue, resultsDict, resultsLock)
  );

  if (!downloadPromises.length) {
    console.warn('No valid URLs found to download.');
    await downloadCompleteQueue.put(null);
  } else {
    console.info(`Starting ${downloadPromises.length} download tasks...`);
    await Promise.all(downloadPromises);
    console.info('All download tasks have been processed.');
    await downloadCompleteQueue.put(null);
  }

  // 모든 작업 완료 대기 (간단히 타임아웃)
  await new Promise(resolve => setTimeout(resolve, 1000));

  console.info('Download and Round-Robin Upload Pipeline finished.');
  return resultsDict;
}

// --- 외부 호출용 함수 --- //
async function runPipeline(urls) {
  console.info('====>>>>>>> urls:', urls);
  if (!urls || !urls.length) {
    console.log('No URLs provided.');
    return {};
  }
  const validUrls = urls.filter(url => typeof url === 'string' && url.trim());
  console.info('====================================== valid_urls:', validUrls);
  if (!validUrls.length) {
    console.log('No valid URLs provided.');
    return {};
  }
  if (!Object.keys(UPLOAD_TARGETS).length) {
    console.log('Error: No upload targets configured.');
    return {};
  }

  console.log(`Configured upload services (in order): ${Object.keys(UPLOAD_TARGETS)}`);
  console.log(`Processing ${validUrls.length} valid URLs...`);

  const results = await downloadAndUploadPipeline(validUrls);
  console.log('Pipeline finished.');
  console.log('\n--- Upload Results ---');
  for (const [originalUrl, newUrl] of Object.entries(results)) {
    const status = newUrl ? `-> ${newUrl}` : '-> FAILED';
    console.log(`${originalUrl} ${status}`);
  }
  console.log('--------------------');
  return results;
}

// --- 테스트용 실행 --- //
if (require.main === module) {
  const sampleUrls = [
    'https://img.sbs.co.kr/newsnet/etv/upload/2020/11/13/30000655653_1280.jpg',
    'https://cdn.newscj.com/news/photo/201604/287322_233347_2016.jpg',
    'http://www.dizzotv.com/site/data/img_dir/2023/08/31/2023083180227_0.jpg',
    'https://pimg.mk.co.kr/news/cms/202404/29/news-p.v1.20240429.97f2ad0ad83e4be2b3e3377504a061a2_P1.jpg',
    'https://img2.daumcdn.net/thumb/R658x0.q70/?fname=https://t1.daumcdn.net/news/202502/19/wydthesedays/20250219090002434bteb.jpg',
  ];

  runPipeline(sampleUrls).then(finalResults => {
    console.log('\nFinal dictionary returned:', finalResults);
  });
}

async function uploadSingleImage(imgBuffer) {
  const services = Object.keys(UPLOAD_TARGETS);
  // 랜덤 셔플
  for (let i = services.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [services[i], services[j]] = [services[j], services[i]];
  }
  console.info(`Trying services in random order: ${services.join(', ')}`);
  for (const serviceName of services) {
    const uploadFunc = UPLOAD_TARGETS[serviceName];
    console.info(`Attempting upload to ${serviceName}...`);
    try {
      const result = await uploadFunc(imgBuffer);
      if (result) {
        console.log(`✅ Uploaded to ${serviceName}: ${result}`);
        return result;
      } else {
        console.warn(`❌ Upload to ${serviceName} failed, trying next...`);
      }
    } catch (e) {
      console.error(`❌ Error uploading to ${serviceName}: ${e.message}, trying next...`);
    }
  }
  console.error('❌ All upload attempts failed');
  return null;
}

module.exports = { runPipeline, uploadSingleImage };