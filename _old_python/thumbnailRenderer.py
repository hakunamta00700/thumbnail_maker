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
    
    @staticmethod
    def split_lines(text: str) -> List[str]:
        """텍스트를 줄 단위로 분리"""
        return text.split('\n')
    
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
                
                # 폰트 경로 찾기
                font_path = f"fonts/{sanitize(fontFamily)}-{fontWeight}-{fontStyle}.ttf"
                if not os.path.exists(font_path):
                    font_path = f"fonts/{sanitize(fontFamily)}-{fontWeight}-{fontStyle}.woff"
                if not os.path.exists(font_path):
                    font_path = None
                
                # 폰트 로드
                if font_path and os.path.exists(font_path):
                    font = ThumbnailRenderer.load_font(font_path, fontSize)
                else:
                    try:
                        font = ImageFont.truetype("arial.ttf", fontSize)
                    except:
                        font = ImageFont.load_default()
                
                # 줄 분리
                lines = ThumbnailRenderer.split_lines(content)
                
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
        print(f"✅ 썸네일 생성 완료: {output_path}")


def sanitize(name: str) -> str:
    """파일명 안전화"""
    return re.sub(r'[^a-zA-Z0-9\-_]', '_', name)

