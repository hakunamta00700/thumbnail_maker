# -*- coding: utf-8 -*-
"""
이미지 업로드 모듈
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Awaitable, Callable, Dict, Optional

import httpx
from loguru import logger


def get_img_ext(img: bytes) -> str:
    """이미지 바이너리에서 확장자 추출"""
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
    """에러 로깅"""
    logger.error(f"Request failed: [{response.status_code}] {response.request.method} {response.url}")
    try:
        logger.debug(f"Response Body: {response.text[:500]}...")
    except Exception as e:
        logger.warning(f"Could not log response body: {e}")


# --- 개별 업로드 함수들 --- #

@logger.catch(message="Error in anhmoe_upload", default=None)
async def anhmoe_upload(client: httpx.AsyncClient, img: bytes) -> Optional[str]:
    """anhmoe 업로드"""
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
    """beeimg 업로드"""
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
    """fastpic 업로드"""
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
    """imagebin 업로드"""
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
    """pixhost 업로드"""
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
    """sxcu 업로드"""
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


async def upload_file_async(file_path: str) -> Optional[str]:
    """
    파일을 업로드하고 URL을 반환합니다.
    
    Args:
        file_path: 업로드할 파일 경로
        
    Returns:
        업로드된 URL 또는 None (실패 시)
    """
    if not os.path.exists(file_path):
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        return None
    
    # 파일 읽기
    try:
        with open(file_path, "rb") as f:
            img_data = f.read()
    except Exception as e:
        logger.error(f"파일 읽기 실패: {file_path}, {e}")
        return None
    
    if not img_data:
        logger.error(f"파일이 비어있습니다: {file_path}")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "image/*,*/*;q=0.8",
    }
    
    # 각 서비스를 순차적으로 시도
    async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=headers) as client:
        for service_name, upload_func in UPLOAD_TARGETS.items():
            try:
                logger.info(f"[{service_name}] 업로드 시도 중...")
                result_url = await upload_func(client, img_data)
                if result_url:
                    logger.success(f"[{service_name}] 업로드 성공: {result_url}")
                    return result_url
                else:
                    logger.warning(f"[{service_name}] 업로드 실패, 다음 서비스 시도...")
            except Exception as e:
                logger.error(f"[{service_name}] 업로드 중 오류: {e}")
                continue
    
    logger.error("모든 업로드 서비스 실패")
    return None


def upload_file(file_path: str) -> Optional[str]:
    """
    파일을 업로드하고 URL을 반환합니다 (동기 함수).
    
    Args:
        file_path: 업로드할 파일 경로
        
    Returns:
        업로드된 URL 또는 None (실패 시)
    """
    return asyncio.run(upload_file_async(file_path))

