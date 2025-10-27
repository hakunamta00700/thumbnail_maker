# -*- coding: utf-8 -*- # Add encoding declaration

import asyncio
import itertools
import re
import tempfile
import time
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import httpx
from loguru import logger

# --- 기본 설정 --- #


SAVE_DIR = Path(tempfile.gettempdir()) / "downloaded_images"
SAVE_DIR.mkdir(exist_ok=True)
MAX_CONCURRENT_DOWNLOADS = 5
MAX_CONCURRENT_UPLOADS = 5
# --- 유틸리티 함수들 (이전과 동일) --- #


def get_filename_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    path = Path(parsed_url.path)
    filename = path.name
    if (not filename or "." not in filename) and parsed_url.query:
        query_params = parse_qs(parsed_url.query)
        for key in ["fname", "filename", "file"]:
            if key in query_params:
                potential_filename = Path(query_params[key][-1]).name
                if potential_filename and "." in potential_filename:
                    filename = potential_filename
                    break
    if not filename or filename == "." or "/" in filename:
        timestamp = str(time.time()).replace(".", "")
        ext = path.suffix or ".jpg"
        filename = f"image_{timestamp}{ext}"
        logger.warning(f"Could not determine filename for {url}, using default: {filename}")
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    max_len = 200
    if len(filename) > max_len:
        name_part, ext_part = Path(filename).stem, Path(filename).suffix
        allowed_len = max_len - len(ext_part)
        filename = name_part[:allowed_len] + ext_part
        logger.warning(f"Filename truncated for {url} -> {filename}")
    return filename


def get_img_ext(img: bytes) -> str:
    if not img:
        return "bin"
    if img[:2] == b"\xff\xd8":
        return "jpg"
    if img[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if img[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if len(img) > 12 and img[:4] == b"RIFF" and img[8:12] == b"WEBP":
        return "webp"
    if img[:2] == b"BM":
        return "bmp"
    if img[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    return "bin"


def log_on_error(response: httpx.Response):
    logger.error(f"Request failed: [{response.status_code}] {response.request.method} {response.url}")
    try:
        logger.debug(f"Response Body: {response.text[:500]}...")
    except Exception as e:
        logger.warning(f"Could not log response body: {e}")


# --- 개별 업로드 함수들 (반환값을 str 또는 None 으로 통일) --- #
# 각 함수는 성공 시 URL(str), 실패 시 None을 반환하도록 수정/확인


@logger.catch(message="Error in anhmoe_upload", default=None)  # 실패 시 None 반환
async def anhmoe_upload(client: httpx.AsyncClient, img: bytes) -> Optional[str]:
    response = await client.post(
        "https://anh.moe/api/1/upload",
        data={"key": "anh.moe_public_api"},
        files={"source": img},
        timeout=60,
    )
    if response.is_error:
        log_on_error(response)
        return None
    try:
        return response.json()["image"]["url"]
    except Exception as e:
        logger.error(f"anhmoe parse error: {e} - Resp: {response.text}")
        return None


@logger.catch(message="Error in beeimg_upload", default=None)
async def beeimg_upload(client: httpx.AsyncClient, img: bytes) -> Optional[str]:
    ext = get_img_ext(img)
    if ext == "bin":
        logger.warning("Beeimg: Skip unknown ext")
        return None
    name = f"image.{ext}"
    content_type = f"image/{ext}"
    logger.debug(f"Beeimg: Uploading {name} type: {content_type}")
    response = await client.post(
        "https://beeimg.com/api/upload/file/json/",
        files={"file": (name, img, content_type)},
        timeout=60,
    )
    if response.is_error:
        log_on_error(response)
        try:
            logger.error(f"Beeimg API Error: {response.json()}")
        except Exception:
            pass
        return None
    try:
        relative_url = response.json().get("files", {}).get("url")
        if relative_url:
            return f"https:{relative_url}" if relative_url.startswith("//") else relative_url
        else:
            logger.error(f"beeimg missing URL: {response.text}")
            return None
    except Exception as e:
        logger.error(f"beeimg parse error: {e} - Resp: {response.text}")
        return None


@logger.catch(message="Error in fastpic_upload", default=None)
async def fastpic_upload(client: httpx.AsyncClient, img: bytes) -> Optional[str]:
    response = await client.post(
        "https://fastpic.org/upload?api=1",
        data={"method": "file", "check_thumb": "no", "uploading": "1"},
        files={"file1": img},
        timeout=60,
    )
    if response.is_error:
        log_on_error(response)
        return None
    match = re.search(r"<imagepath>(.+?)</imagepath>", response.text)
    if match:
        return match[1].strip()
    else:
        logger.error(f"fastpic missing imagepath: {response.text}")
        return None


@logger.catch(message="Error in imagebin_upload", default=None)
async def imagebin_upload(client: httpx.AsyncClient, img: bytes) -> Optional[str]:
    response = await client.post(url="https://imagebin.ca/upload.php", files={"file": img}, timeout=60)
    if response.is_error:
        log_on_error(response)
        return None
    match = re.search(r"url:\s*(.+?)$", response.text, flags=re.MULTILINE)
    if match:
        return match[1].strip()
    else:
        logger.error(f"imagebin missing URL pattern: {response.text}")
        return None


@logger.catch(message="Error in pixhost_upload", default=None)
async def pixhost_upload(client: httpx.AsyncClient, img: bytes) -> Optional[str]:
    try:
        response = await client.post(
            "https://api.pixhost.to/images",
            data={"content_type": 0},
            files={"img": img},
            timeout=60,
        )
        response.raise_for_status()
        json_response = response.json()
        show_url = json_response.get("show_url")
        # pixhost는 show_url을 반환하는 경우가 많으므로, 이를 성공으로 간주
        direct_image_url = json_response.get("url")
        result = direct_image_url if direct_image_url else show_url
        if result:
            return result
        else:
            logger.error(f"pixhost missing URL/show_url: {json_response}")
            return None
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 414:
            logger.error(f"Pixhost 414 type: {get_img_ext(img)}")
        log_on_error(e.response)
        return None
    except httpx.RequestError as e:
        logger.error(f"Pixhost request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Pixhost general error: {e} - Resp: {getattr(response, 'text', 'N/A')}")
        return None


@logger.catch(message="Error in sxcu_upload", default=None)
async def sxcu_upload(client: httpx.AsyncClient, img: bytes, retry_delay=5) -> Optional[str]:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = await client.post(
            "https://sxcu.net/api/files/create",
            headers=headers,
            files={"file": img},
            timeout=60,
        )
        if response.status_code == 429:
            logger.warning(f"Sxcu rate limit (429). Wait {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            logger.info("Retrying sxcu upload...")
            response = await client.post(
                "https://sxcu.net/api/files/create",
                headers=headers,
                files={"file": img},
                timeout=60,
            )
        if response.is_error:
            log_on_error(response)
            return None
        json_data = response.json()
        base_url = json_data.get("url")
        if base_url:
            return base_url
        else:
            logger.error(f"sxcu missing URL/error: {json_data.get('error', 'Unknown')} - Resp: {response.text}")
            return None
    except httpx.RequestError as e:
        logger.error(f"sxcu request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"sxcu general error: {e} - Resp: {getattr(response, 'text', 'N/A')}")
        return None


# --- 업로드 대상 서비스 모음 --- #

UPLOAD_TARGETS: Dict[str, Callable[[httpx.AsyncClient, bytes], Awaitable[Optional[str]]]] = {
    "anhmoe": anhmoe_upload,
    "beeimg": beeimg_upload,
    "fastpic": fastpic_upload,
    "imagebin": imagebin_upload,
    "pixhost": pixhost_upload,
    "sxcu": sxcu_upload,
}

# --- 새로운 파이프라인 구조 --- #


async def download_image_task(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,  # 원본 URL 추가
    download_complete_queue: asyncio.Queue,
    results_dict: Dict[str, Optional[str]],  # 결과 저장용 딕셔너리
    results_lock: asyncio.Lock,  # 딕셔너리 접근 제어용 Lock
):
    """개별 이미지 다운로드, 성공 시 큐에 (원본 URL, 경로) 추가, 실패 시 결과 딕셔너리에 None 기록"""
    filepath = None
    async with semaphore:
        try:
            filename = get_filename_from_url(url)
            filepath = SAVE_DIR / filename
            logger.info(f"Attempting download: {url} -> {filepath}")
            response = await client.get(url, timeout=60, follow_redirects=True)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                f.write(response.content)

            logger.success(f"[✓] Downloaded: {url} -> {filepath}")
            # 성공 시 큐에 (원본 URL, 파일 경로) 튜플 추가
            await download_complete_queue.put((url, filepath))  # 원본 URL 함께 전달

        except Exception as e:  # 포괄적인 예외 처리
            if isinstance(e, httpx.HTTPStatusError):
                logger.error(f"[✗] HTTP Error dl {url}: {e.response.status_code}")
            elif isinstance(e, httpx.RequestError):
                logger.error(f"[✗] Request Error dl {url}: {e}")
            else:
                logger.error(f"[✗] Failed dl/save {url}: {e}")

            # 다운로드 실패 시 결과 딕셔너리에 None 기록 (Lock 사용)
            async with results_lock:
                results_dict[url] = None
            logger.warning(f"Recorded download failure for {url} in results.")

            if filepath:
                try:
                    filepath.unlink(missing_ok=True)
                except OSError:
                    pass


async def upload_dispatcher_task(
    download_complete_queue: asyncio.Queue,  # (url, filepath) 튜플 수신
    upload_job_queue: asyncio.Queue,  # (url, filepath, service_name, upload_func) 튜플 발신
    targets: Dict[str, Callable],
):
    """다운로드 완료된 (원본 URL, 파일 경로)를 받아, 서비스 할당 후 업로드 큐에 넣음"""
    logger.info("Upload Dispatcher started.")
    service_cycler = itertools.cycle(targets.items())

    while True:
        item = await download_complete_queue.get()
        if item is None:  # 종료 신호
            logger.info("Dispatcher received None from download queue. Signaling workers to terminate.")
            for _ in range(MAX_CONCURRENT_UPLOADS):
                await upload_job_queue.put(None)
            download_complete_queue.task_done()
            break

        original_url, filepath = item  # 튜플 언패킹

        if not isinstance(filepath, Path) or not filepath.exists():
            logger.error(f"Dispatcher received invalid/missing file: {filepath} for url {original_url}. Skipping.")
            # 실패 기록 필요? 다운로드 태스크에서 이미 실패 기록했을 가능성 높음
            download_complete_queue.task_done()
            continue

        service_name, upload_func = next(service_cycler)
        logger.info(f"Dispatcher assigning {filepath.name} (from {original_url}) to service [{service_name}]")

        # 업로드 작업 큐에 원본 URL 포함하여 작업 추가
        await upload_job_queue.put((original_url, filepath, service_name, upload_func))
        download_complete_queue.task_done()

    logger.info("Upload Dispatcher finished.")


async def upload_worker_task(
    worker_id: int,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    upload_job_queue: asyncio.Queue,  # (url, filepath, service_name, func) 튜플 수신
    results_dict: Dict[str, Optional[str]],  # 결과 저장용 딕셔너리
    results_lock: asyncio.Lock,  # 딕셔너리 접근 제어용 Lock
):
    """업로드 작업 큐에서 작업을 받아 특정 서비스에 업로드하고 결과 딕셔너리 업데이트"""
    logger.info(f"Upload Worker-{worker_id} started.")
    while True:
        job = await upload_job_queue.get()
        if job is None:  # 종료 신호
            logger.info(f"Upload Worker-{worker_id} received None, terminating.")
            upload_job_queue.task_done()
            await asyncio.sleep(1)
            break
        # await upload_job_queue.put((original_url, filepath, service_name, upload_func))
        original_url, filepath, service_name, upload_func = job  # 원본 URL 포함 언패킹
        logger.info(
            f"Worker-{worker_id}: Processing {filepath.name} (from {original_url}) for service [{service_name}]"
        )

        result_url: Optional[str] = None  # 결과 URL 초기화
        async with semaphore:
            try:
                if not filepath.exists():
                    logger.error(f"Worker-{worker_id}: File not found for upload: {filepath}. Skipping.")
                    result_url = None  # 실패로 간주
                else:
                    with open(filepath, "rb") as f:
                        img_data = f.read()
                    if not img_data:
                        logger.warning(f"Worker-{worker_id}: File is empty: {filepath}. Skipping.")
                        result_url = None  # 실패로 간주
                    else:
                        logger.debug(f"Worker-{worker_id}: Calling {upload_func.__name__} for {filepath.name}")
                        # 업로드 함수는 성공 시 URL(str), 실패 시 None 반환 가정
                        result_url = await upload_func(client, img_data)

                # 결과 기록 (Lock 사용)

                if result_url:
                    async with results_lock:
                        results_dict[original_url] = result_url  # 성공 시 URL, 실패 시 None 저장
                    logger.success(
                        f"[✓] Uploaded [{filepath.name}] to [{service_name}]: {result_url} (Orig: {original_url})"
                    )
                else:
                    await upload_job_queue.put((original_url, filepath, service_name, upload_func))
                    logger.warning(
                        f"[✗] Upload failed for {filepath.name} to [{service_name}] (Orig: {original_url}). Recorded failure."
                    )
                    upload_job_queue.task_done()
                    continue

            except Exception as e:
                logger.error(f"Worker-{worker_id}: Unexpected error processing {filepath} for {service_name}: {e}")
                # 예외 발생 시에도 실패 기록
                async with results_lock:
                    if original_url not in results_dict:  # 아직 기록 안된 경우만
                        results_dict[original_url] = None
            finally:
                upload_job_queue.task_done()  # 작업 처리 완료

    logger.info(f"Upload Worker-{worker_id} finished.")


async def download_and_upload_pipeline(
    urls: List[str],
) -> Dict[str, Optional[str]]:  # 반환 타입 명시
    """다운로드와 라운드 로빈 업로드를 실행하고, 원본 URL과 새 URL 매핑 딕셔너리 반환"""
    if not urls:
        logger.warning("No URLs provided.")
        return {}
    if not UPLOAD_TARGETS:
        logger.error("No upload targets defined.")
        return {}

    download_complete_queue = asyncio.Queue()
    upload_job_queue = asyncio.Queue()
    download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
    upload_semaphore = asyncio.Semaphore(MAX_CONCURRENT_UPLOADS)

    # --- 결과 저장을 위한 공유 상태 ---
    results_dict: Dict[str, Optional[str]] = {}
    results_lock = asyncio.Lock()
    # ---------------------------------

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "image/*,*/*;q=0.8",
    }
    async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=headers) as client:

        asyncio.create_task(
            upload_dispatcher_task(download_complete_queue, upload_job_queue, UPLOAD_TARGETS)
        )

        [
            asyncio.create_task(
                # 결과를 저장할 dict와 lock 전달
                upload_worker_task(
                    i,
                    client,
                    upload_semaphore,
                    upload_job_queue,
                    results_dict,
                    results_lock,
                )
            )
            for i in range(MAX_CONCURRENT_UPLOADS)
        ]

        download_tasks = [
            asyncio.create_task(
                # 결과를 저장할 dict와 lock 전달
                download_image_task(
                    client,
                    download_semaphore,
                    url,
                    download_complete_queue,
                    results_dict,
                    results_lock,
                )
            )
            for url in urls
            if isinstance(url, str) and url.startswith(("http://", "https://"))
        ]

        if not download_tasks:
            logger.warning("No valid URLs found to download.")
            await download_complete_queue.put(None)
        else:
            logger.info(f"Starting {len(download_tasks)} download tasks...")
            # 모든 다운로드 작업 완료 대기 (성공/실패 기록 포함)
            await asyncio.gather(*download_tasks)
            logger.info("All download tasks have been processed (including failures).")
            logger.info("Signaling end of downloads to dispatcher...")
            await download_complete_queue.put(None)

        logger.info("Waiting for dispatcher to process all successfully downloaded files...")
        await download_complete_queue.join()

        logger.info("Waiting for all assigned upload jobs to complete...")
        await upload_job_queue.join()

    logger.info("Download and Round-Robin Upload Pipeline finished.")
    # 최종 결과 딕셔너리 반환
    return results_dict


# --- 외부 호출용 함수 --- #
def run_pipeline(urls: List[str]) -> Dict[str, Optional[str]]:  # 반환 타입 명시
    """주어진 URL 리스트에 대해 파이프라인 실행 후 결과 딕셔너리 반환"""
    logger.info("====>>>>>>> urls:", urls)
    results: Dict[str, Optional[str]] = {}
    if not urls:
        print("No URLs provided.")
        return results
    valid_urls = [url for url in urls if isinstance(url, str) and url.strip()]
    logger.info("====================================== valid_urls:", valid_urls)
    if not valid_urls:
        print("No valid URLs provided.")
        return results
    if not UPLOAD_TARGETS:
        print("Error: No upload targets configured.")
        return results

    print(f"Configured upload services (in order): {list(UPLOAD_TARGETS.keys())}")
    print(f"Processing {len(valid_urls)} valid URLs...")
    results = asyncio.run(download_and_upload_pipeline(valid_urls))
    print("Pipeline finished.")
    # 결과 출력 (선택적)
    print("\n--- Upload Results ---")
    for original_url, new_url in results.items():
        status = f"-> {new_url}" if new_url else "-> FAILED"
        print(f"{original_url} {status}")
    print("--------------------")
    return results


# --- 테스트용 실행 --- #
if __name__ == "__main__":
    sample_urls = [
        "https://img.sbs.co.kr/newsnet/etv/upload/2020/11/13/30000655653_1280.jpg",
        "https://cdn.newscj.com/news/photo/201604/287322_233347_2016.jpg",
        "http://www.dizzotv.com/site/data/img_dir/2023/08/31/2023083180227_0.jpg",
        "https://pimg.mk.co.kr/news/cms/202404/29/news-p.v1.20240429.97f2ad0ad83e4be2b3e3377504a061a2_P1.jpg",
        "https://img2.daumcdn.net/thumb/R658x0.q70/?fname=https://t1.daumcdn.net/news/202502/19/wydthesedays/20250219090002434bteb.jpg",
    ]

    final_results = run_pipeline(sample_urls)
    # 이제 final_results 변수에 {'원본URL': '새URL' or None, ...} 형태의 결과가 담겨 있음
    print("\nFinal dictionary returned:", final_results)
