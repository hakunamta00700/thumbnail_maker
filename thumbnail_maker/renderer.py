#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
썸네일 렌더러 - DSL 기반 이미지 생성
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json
import re
import io
from typing import Dict, List, Tuple, Optional
import os
import pathlib

import requests
from fontTools.ttLib import TTFont
try:
    import woff2  # from pywoff2
except Exception:
    woff2 = None
try:
    # Optional: WOFF -> OTF 변환기
    from woff2otf import woff2otf
except Exception:
    woff2otf = None


def sanitize(name: str) -> str:
    """파일명 안전화"""
    return re.sub(r'[^a-zA-Z0-9\-_]', '_', name)


class ThumbnailRenderer:
    """썸네일 렌더러 클래스"""
    
    # 해상도 프리셋 매핑
    RESOLUTIONS = {
        '16:9': (480, 270),
        '9:16': (270, 480),
        '4:3': (480, 360),
        '1:1': (360, 360)
    }
    
    MARGIN = 20  # 여백
    LINE_HEIGHT = 1.1  # 줄간격 배수
    DEFAULT_OUTLINE_THICKNESS = 4  # 기본 외곽선 두께
    
    @staticmethod
    def get_resolution(dsl_resolution: Dict) -> Tuple[int, int]:
        """해상도 계산"""
        if not dsl_resolution or 'type' not in dsl_resolution:
            return ThumbnailRenderer.RESOLUTIONS['16:9']
        
        res_type = dsl_resolution['type']
        
        if res_type == 'preset':
            value = dsl_resolution.get('value', '16:9')
            return ThumbnailRenderer.RESOLUTIONS.get(value, ThumbnailRenderer.RESOLUTIONS['16:9'])
        
        elif res_type == 'custom':
            w = int(dsl_resolution.get('width', 480))
            h = int(dsl_resolution.get('height', 270))
            return (w, h) if w > 0 and h > 0 else ThumbnailRenderer.RESOLUTIONS['16:9']
        
        elif res_type == 'fixedRatio':
            ratio_str = dsl_resolution.get('ratioValue', '16:9')
            parts = ratio_str.split(':')
            if len(parts) != 2:
                return ThumbnailRenderer.RESOLUTIONS['16:9']
            
            try:
                rw, rh = float(parts[0]), float(parts[1])
                if rw <= 0 or rh <= 0:
                    return ThumbnailRenderer.RESOLUTIONS['16:9']
                
                aspect_ratio = rw / rh
                
                if 'width' in dsl_resolution and dsl_resolution['width'] is not None:
                    width = int(dsl_resolution['width'])
                    if width > 0:
                        height = int(width / aspect_ratio)
                        return (width, height)
                
                if 'height' in dsl_resolution and dsl_resolution['height'] is not None:
                    height = int(dsl_resolution['height'])
                    if height > 0:
                        width = int(height * aspect_ratio)
                        return (width, height)
            except ValueError:
                pass
            
            return ThumbnailRenderer.RESOLUTIONS['16:9']
        
        return ThumbnailRenderer.RESOLUTIONS['16:9']
    
    @staticmethod
    def parse_font_faces(texts: List[Dict]) -> List[Dict]:
        """텍스트에서 폰트 페이스 추출"""
        font_faces = []
        seen = set()
        
        for txt in texts:
            if 'font' in txt and 'faces' in txt['font']:
                for face in txt['font']['faces']:
                    key = f"{face.get('name')}|{face.get('url')}|{face.get('weight')}|{face.get('style')}"
                    if key not in seen:
                        seen.add(key)
                        font_faces.append(face)
        
        return font_faces

    # ---------- 폰트 유틸 ----------
    @staticmethod
    def _fonts_dir() -> str:
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')
        return os.path.normpath(d)

    @staticmethod
    def _font_safe_filename(face: Dict) -> str:
        url_path = ''
        try:
            # url의 경로 확장자 추출 시 실패 대비
            from urllib.parse import urlparse
            url_path = urlparse(face.get('url', '')).path
        except Exception:
            pass
        ext = os.path.splitext(url_path)[1].lower() or '.ttf'
        name = sanitize(face.get('name', 'Font'))
        weight = sanitize(str(face.get('weight', 'normal')))
        style = sanitize(str(face.get('style', 'normal')))
        return f"{name}-{weight}-{style}{ext}"

    @staticmethod
    def _font_ttf_filename(face: Dict) -> str:
        name = sanitize(face.get('name', 'Font'))
        weight = sanitize(str(face.get('weight', 'normal')))
        style = sanitize(str(face.get('style', 'normal')))
        return f"{name}-{weight}-{style}.ttf"

    @staticmethod
    def _download(url: str, dest_path: str) -> None:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(r.content)

    @staticmethod
    def _convert_woff_to_ttf(woff_path: str, ttf_path: str) -> None:
        # 우선 woff -> otf 변환이 가능하면 사용
        if woff2otf is not None:
            otf_path = os.path.splitext(ttf_path)[0] + '.otf'
            with open(woff_path, 'rb') as rf:
                woff_bytes = rf.read()
            otf_bytes = woff2otf(woff_bytes)
            with open(otf_path, 'wb') as wf:
                wf.write(otf_bytes)
            return
        # 폴백: fontTools를 사용한 시도 (환경에 따라 실패할 수 있음)
        font = TTFont(woff_path)
        font.flavor = None
        font.save(ttf_path)

    @staticmethod
    def _convert_woff2_to_ttf(woff2_path: str, ttf_path: str) -> None:
        if woff2 is None:
            raise RuntimeError("pywoff2 모듈이 필요합니다 (requirements.txt 참고)")
        # pywoff2는 파일 경로 기반 변환 지원
        # 파일 내용을 직접 디코딩해서 저장하는 방식으로 처리
        with open(woff2_path, 'rb') as f:
            data = f.read()
        decompressed = woff2.decompress(data)
        with open(ttf_path, 'wb') as f:
            f.write(decompressed)

    @staticmethod
    def ensure_fonts(texts: List[Dict]) -> None:
        """DSL 내 faces를 다운로드/변환하여 Pillow가 읽을 수 있는 TTF로 보장"""
        faces = ThumbnailRenderer.parse_font_faces(texts)
        if not faces:
            return
        fonts_dir = ThumbnailRenderer._fonts_dir()
        os.makedirs(fonts_dir, exist_ok=True)

        for face in faces:
            url = face.get('url')
            if not url:
                continue
            original_name = ThumbnailRenderer._font_safe_filename(face)
            original_path = os.path.join(fonts_dir, original_name)
            ttf_name = ThumbnailRenderer._font_ttf_filename(face)
            ttf_path = os.path.join(fonts_dir, ttf_name)
            otf_path = os.path.splitext(ttf_path)[0] + '.otf'

            # 이미 TTF가 있으면 스킵
            if os.path.exists(ttf_path) or os.path.exists(otf_path):
                continue

            # 로컬 파일 또는 원격 URL 구분
            from urllib.parse import urlparse
            parsed = urlparse(url)
            is_local = False
            local_path = ''
            if parsed.scheme == 'file':
                is_local = True
                local_path = os.path.abspath(parsed.path)
            elif os.path.isabs(url) and os.path.exists(url):
                is_local = True
                local_path = os.path.abspath(url)

            if is_local:
                source_path = local_path
                ext = pathlib.Path(source_path).suffix.lower()
            else:
                # 원격: 원본 없으면 다운로드
                ext = pathlib.Path(original_name).suffix.lower()
                if not os.path.exists(original_path):
                    try:
                        ThumbnailRenderer._download(url, original_path)
                    except Exception as e:
                        print(f"폰트 다운로드 실패: {url} -> {e}")
                        continue
                source_path = original_path

            # 확장자별 변환/복사
            try:
                if ext == '.ttf' or ext == '.otf':
                    if source_path != ttf_path:
                        # 확장자 유지 복사
                        target = ttf_path if ext == '.ttf' else otf_path
                        with open(source_path, 'rb') as rf, open(target, 'wb') as wf:
                            wf.write(rf.read())
                elif ext == '.woff2':
                    ThumbnailRenderer._convert_woff2_to_ttf(source_path, ttf_path)
                elif ext == '.woff':
                    ThumbnailRenderer._convert_woff_to_ttf(source_path, ttf_path)
                else:
                    # 미지원 확장자는 시도만 해보고 실패시 스킵
                    try:
                        ThumbnailRenderer._convert_woff_to_ttf(source_path, ttf_path)
                    except Exception:
                        pass
            except Exception as e:
                print(f"폰트 변환 실패: {source_path} -> {ttf_path}, {e}")
    
    @staticmethod
    def split_lines(text: str) -> List[str]:
        """텍스트를 줄 단위로 분리"""
        return text.split('\n')

    @staticmethod
    def wrap_line_by_words(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int
    ) -> List[str]:
        """단어 단위로 한 줄을 주어진 최대 폭에 맞게 개행한다.

        - 공백으로 단어를 나눈 뒤, 누적 폭이 넘어가면 이전까지를 한 줄로 확정한다.
        - 단어 하나가 max_width보다 커도 단어 단위 래핑 원칙상 강제 분할은 하지 않는다.
        - 입력이 빈 문자열이면 ['']을 반환한다.
        """
        if text is None or text == '':
            return ['']

        words = text.split(' ')
        lines: List[str] = []
        current = ''

        for word in words:
            candidate = word if current == '' else current + ' ' + word
            bbox = draw.textbbox((0, 0), candidate, font=font)
            candidate_width = bbox[2] - bbox[0]
            if candidate_width > max_width and current != '':
                lines.append(current)
                current = word
            else:
                current = candidate

        if current != '':
            lines.append(current)

        return lines if lines else ['']
    
    @staticmethod
    def load_font(font_path: str, size: int, weight: str = 'normal', style: str = 'normal') -> ImageFont.FreeTypeFont:
        """폰트 로드"""
        try:
            font = ImageFont.truetype(font_path, size)
            return font
        except Exception as e:
            print(f"폰트 로드 실패: {font_path}, {e}")
            try:
                return ImageFont.load_default()
            except:
                return ImageFont.load_default()
    
    @staticmethod
    def get_text_dimensions(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
        """텍스트 크기 측정"""
        bbox = draw.textbbox((0, 0), text, font=font)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])
    
    @staticmethod
    def draw_text_with_outline(
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        fill: str,
        outline: Optional[Dict] = None
    ):
        """외곽선과 함께 텍스트 그리기"""
        x, y = position
        
        # 외곽선 그리기
        if outline and outline.get('color') and outline.get('thickness', 0) > 0:
            thickness = outline['thickness']
            outline_color = outline['color']
            
            # text-shadow 효과를 위/아래/좌/우로 여러 번 그리기
            for dx in range(-thickness, thickness + 1):
                for dy in range(-thickness, thickness + 1):
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        
        # 메인 텍스트 그리기
        draw.text((x, y), text, font=font, fill=fill)
    
    @staticmethod
    def render_background(
        img: Image.Image,
        bg_config: Dict,
        width: int,
        height: int
    ):
        """배경 렌더링"""
        bg_type = bg_config.get('type', 'solid')
        
        if bg_type == 'solid':
            color = bg_config.get('color', '#ffffff')
            fill = Image.new('RGB', (width, height), color)
            img.paste(fill)
        
        elif bg_type == 'gradient':
            colors = bg_config.get('colors', ['#ffffff', '#000000'])
            gradient = Image.new('RGB', (width, height), colors[0])
            
            # 간단한 수평 그라디언트
            for i in range(width):
                ratio = i / width
                r1, g1, b1 = [int(c) for c in (colors[0][1:3], colors[0][3:5], colors[0][5:7])]
                r2, g2, b2 = [int(c) for c in (colors[-1][1:3], colors[-1][3:5], colors[-1][5:7])]
                
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                
                for j in range(height):
                    gradient.putpixel((i, j), (r, g, b))
            
            img.paste(gradient)
        
        elif bg_type == 'image':
            img_path = bg_config.get('imagePath', '')
            
            # base64 데이터 URL 처리
            if img_path.startswith('data:image'):
                # base64 디코딩 처리
                import base64
                header, encoded = img_path.split(',', 1)
                image_data = base64.b64decode(encoded)
                bg_img = Image.open(io.BytesIO(image_data))
            else:
                if not os.path.exists(img_path):
                    print(f"배경 이미지를 찾을 수 없음: {img_path}")
                    return
                
                bg_img = Image.open(img_path)
            
            # cover 알고리즘으로 리사이즈
            img_ratio = bg_img.width / bg_img.height
            canvas_ratio = width / height
            
            if img_ratio > canvas_ratio:
                # 이미지가 더 넓음: 높이 기준으로 맞춤
                new_height = height
                new_width = int(height * img_ratio)
                bg_img = bg_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                left = (new_width - width) // 2
                bg_img = bg_img.crop((left, 0, left + width, height))
            else:
                # 이미지가 더 높음: 너비 기준으로 맞춤
                new_width = width
                new_height = int(width / img_ratio)
                bg_img = bg_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                top = (new_height - height) // 2
                bg_img = bg_img.crop((0, top, width, top + height))
            
            # 블러 효과 적용
            image_blur = bg_config.get('imageBlur', 0)
            if image_blur > 0:
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=image_blur))
            
            # 투명도 적용
            image_opacity = bg_config.get('imageOpacity', 1.0)
            if image_opacity < 1.0 and bg_img.mode in ('RGBA', 'LA'):
                alpha = bg_img.split()[-1]
                alpha = alpha.point(lambda p: int(p * image_opacity))
                bg_img.putalpha(alpha)
            elif image_opacity < 1.0:
                bg_img = bg_img.convert('RGBA')
                alpha = bg_img.split()[-1]
                alpha = alpha.point(lambda p: int(p * image_opacity))
                bg_img.putalpha(alpha)
            
            # 배경 위에 붙이기
            if bg_img.mode == 'RGBA':
                img.paste(bg_img, (0, 0), bg_img)
            else:
                img.paste(bg_img, (0, 0))
    
    @staticmethod
    def render_thumbnail(dsl: Dict, output_path: str):
        """DSL을 읽어서 썸네일 생성"""
        thumbnail_config = dsl.get('Thumbnail', {})
        
        # 해상도 결정
        resolution = ThumbnailRenderer.get_resolution(thumbnail_config.get('Resolution', {}))
        width, height = resolution
        
        # 이미지 생성
        img = Image.new('RGB', (width, height), '#ffffff')
        
        # 배경 렌더링
        if 'Background' in thumbnail_config:
            ThumbnailRenderer.render_background(img, thumbnail_config['Background'], width, height)
        
        # 텍스트 렌더링
        if 'Texts' in thumbnail_config:
            draw = ImageDraw.Draw(img)
            
            for txt_config in thumbnail_config['Texts']:
                if not txt_config.get('enabled', True):
                    continue
                
                # 기본값 설정
                content = txt_config.get('content', '')
                fontSize = txt_config.get('fontSize', 48)
                fontFamily = txt_config.get('font', {}).get('name', 'Arial')
                color = txt_config.get('color', '#000000')
                gridPosition = txt_config.get('gridPosition', 'tl')
                fontWeight = txt_config.get('fontWeight', 'normal')
                fontStyle = txt_config.get('fontStyle', 'normal')
                lineHeight = txt_config.get('lineHeight', ThumbnailRenderer.LINE_HEIGHT)
                wordWrap = txt_config.get('wordWrap', False)
                outline = txt_config.get('outline')
                
                # 외곽선 기본값
                if outline and (not outline.get('thickness') or outline.get('thickness') < 0):
                    outline['thickness'] = ThumbnailRenderer.DEFAULT_OUTLINE_THICKNESS
                
                # faces 기반 폰트 확보 (필요 시 다운로드/변환)
                try:
                    ThumbnailRenderer.ensure_fonts(thumbnail_config.get('Texts', []))
                except Exception as e:
                    print(f"폰트 확보 과정 경고: {e}")

                # 확보된 TTF 경로 우선 시도
                fonts_dir = ThumbnailRenderer._fonts_dir()
                base_name = f"{sanitize(fontFamily)}-{sanitize(str(fontWeight))}-{sanitize(str(fontStyle))}"
                ttf_candidate = os.path.join(fonts_dir, base_name + '.ttf')
                otf_candidate = os.path.join(fonts_dir, base_name + '.otf')

                # 로컬 정적 폰트 폴더(프로젝트 루트/fonts)도 탐색
                legacy_ttf = os.path.join('fonts', f"{sanitize(fontFamily)}-{fontWeight}-{fontStyle}.ttf")
                legacy_woff = os.path.join('fonts', f"{sanitize(fontFamily)}-{fontWeight}-{fontStyle}.woff")
                font_path = None
                if os.path.exists(ttf_candidate):
                    font_path = ttf_candidate
                elif os.path.exists(otf_candidate):
                    font_path = otf_candidate
                elif os.path.exists(legacy_ttf):
                    font_path = legacy_ttf
                elif os.path.exists(legacy_woff):
                    # 가능한 경우 변환 시도 후 사용
                    try:
                        os.makedirs(fonts_dir, exist_ok=True)
                        conv_target_ttf = os.path.join(fonts_dir, base_name + '.ttf')
                        conv_target_otf = os.path.join(fonts_dir, base_name + '.otf')
                        if os.path.splitext(legacy_woff)[1].lower() == '.woff':
                            ThumbnailRenderer._convert_woff_to_ttf(legacy_woff, conv_target_ttf)
                        font_path = (
                            conv_target_ttf if os.path.exists(conv_target_ttf)
                            else (conv_target_otf if os.path.exists(conv_target_otf) else None)
                        )
                    except Exception:
                        font_path = None
                
                # 폰트 로드 + 한글 폴백
                font = None
                if font_path and os.path.exists(font_path):
                    font = ThumbnailRenderer.load_font(font_path, fontSize)
                if font is None:
                    # Windows 한글 폴백 (맑은 고딕)
                    for fallback in [
                        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'malgun.ttf'),
                        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'malgunsl.ttf'),
                    ]:
                        try:
                            if os.path.exists(fallback):
                                font = ImageFont.truetype(fallback, fontSize)
                                break
                        except Exception:
                            pass
                if font is None:
                    try:
                        font = ImageFont.truetype("arial.ttf", fontSize)
                    except Exception:
                        font = ImageFont.load_default()
                
                # 줄 분리 및 단어 단위 줄바꿈 처리
                initial_lines = ThumbnailRenderer.split_lines(content)
                effective_max_width = width - 2 * ThumbnailRenderer.MARGIN

                if wordWrap:
                    processed_lines: List[str] = []
                    for init_line in initial_lines:
                        if init_line == '':
                            processed_lines.append('')
                        else:
                            wrapped = ThumbnailRenderer.wrap_line_by_words(
                                draw=draw,
                                text=init_line,
                                font=font,
                                max_width=effective_max_width,
                            )
                            processed_lines.extend(wrapped)
                    lines = processed_lines
                else:
                    lines = initial_lines
                
                # 라인 높이 계산
                lh = int(fontSize * lineHeight)
                totalTextHeight = len(lines) * lh
                
                # 그리드 위치 결정
                row = gridPosition[0] if len(gridPosition) > 0 else 't'  # t, m, b
                col = gridPosition[1] if len(gridPosition) > 1 else 'l'  # l, c, r
                
                # X 위치 결정
                if col == 'l':
                    targetX = ThumbnailRenderer.MARGIN
                    textAlign = 'left'
                elif col == 'c':
                    targetX = width // 2
                    textAlign = 'center'
                else:  # 'r'
                    targetX = width - ThumbnailRenderer.MARGIN
                    textAlign = 'right'
                
                # Y 위치 결정
                if row == 't':
                    baseY = ThumbnailRenderer.MARGIN
                elif row == 'm':
                    baseY = (height // 2) - (totalTextHeight // 2)
                else:  # 'b'
                    baseY = height - ThumbnailRenderer.MARGIN - totalTextHeight
                
                # 텍스트 그리기
                for line_idx, line in enumerate(lines):
                    currentY = baseY + (line_idx * lh)
                    
                    # 텍스트 크기 측정
                    bbox = draw.textbbox((0, 0), line, font=font)
                    textWidth = bbox[2] - bbox[0]
                    
                    # 정렬에 따른 X 위치 조정
                    x = targetX
                    if textAlign == 'center':
                        x = targetX - textWidth // 2
                    elif textAlign == 'right':
                        x = targetX - textWidth
                    
                    # 텍스트 그리기
                    if outline and outline.get('color') and outline.get('thickness', 0) > 0:
                        ThumbnailRenderer.draw_text_with_outline(
                            draw, line, (x, currentY), font, color, outline
                        )
                    else:
                        draw.text((x, currentY), line, font=font, fill=color)
        
        # 저장
        img.save(output_path, 'PNG')
        print(f"[OK] 썸네일 생성 완료: {output_path}")


