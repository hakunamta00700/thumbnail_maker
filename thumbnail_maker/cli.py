#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 스크립트
"""

import sys
import os
import json
import argparse
import base64
from .renderer import ThumbnailRenderer
import tempfile
import zipfile
import shutil
from typing import Dict, Optional


def main():
    """메인 CLI 진입점"""
    parser = argparse.ArgumentParser(description='썸네일 생성')
    parser.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로')
    parser.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    
    args = parser.parse_args()
    staging = None
    cwd_backup = os.getcwd()
    # 출력 경로를 절대경로로 확보 (staging 디렉토리 변경 전)
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.abspath(output_path)
    try:
        # .thl 패키지 지원: 임시 폴더에 풀어서 작업
        if args.dsl.lower().endswith('.thl') and os.path.exists(args.dsl):
            staging = tempfile.mkdtemp(prefix='thl_run_')
            with zipfile.ZipFile(args.dsl, 'r') as zf:
                zf.extractall(staging)
            # 작업 디렉토리를 패키지 루트로 변경 (renderer의 'fonts/' 탐색을 위함)
            os.chdir(staging)
            dsl_path = os.path.join(staging, 'thumbnail.json')
        else:
            dsl_path = args.dsl

        # DSL 파일 확인
        if not os.path.exists(dsl_path):
            print(f"오류: DSL 파일을 찾을 수 없습니다: {dsl_path}")
            sys.exit(1)
        
        # DSL 읽기
        with open(dsl_path, 'r', encoding='utf-8') as f:
            dsl = json.load(f)
        
        # 썸네일 생성
        ThumbnailRenderer.render_thumbnail(dsl, output_path)
    finally:
        try:
            os.chdir(cwd_backup)
        except Exception:
            pass
        if staging:
            shutil.rmtree(staging, ignore_errors=True)


def main_cli():
    """간편 CLI 진입점"""
    parser = argparse.ArgumentParser(description='썸네일 생성 (간편 CLI)')
    parser.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로 또는 .thl 파일 경로')
    parser.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    parser.add_argument('-t', '--title', help='제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    parser.add_argument('--subtitle', help='부제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    parser.add_argument('-b', '--background-image', dest='bgImg', help='배경 이미지 경로')
    
    args = parser.parse_args()

    def normalize_text(s: str) -> str:
        """CLI에서 전달된 텍스트의 줄바꿈 시퀀스를 실제 줄바꿈으로 변환"""
        if s is None:
            return s
        # 리터럴 \n, \r\n, \r 처리
        # 먼저 \r\n -> \n 으로 통일, 이후 리터럴 역슬래시-n 치환
        s = s.replace('\r\n', '\n').replace('\r', '\n')
        s = s.replace('\\n', '\n')
        return s
    
    staging = None
    cwd_backup = os.getcwd()
    # 출력 경로를 절대경로로 확보 (staging 디렉토리 변경 전)
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.abspath(output_path)
    try:
        # .thl 패키지 지원
        if args.dsl and args.dsl.lower().endswith('.thl') and os.path.exists(args.dsl):
            staging = tempfile.mkdtemp(prefix='thl_run_')
            with zipfile.ZipFile(args.dsl, 'r') as zf:
                zf.extractall(staging)
            os.chdir(staging)
            dsl_path = os.path.join(staging, 'thumbnail.json')
        else:
            dsl_path = args.dsl

        # DSL 파일 확인
        if not os.path.exists(dsl_path):
            print(f"오류: DSL 파일을 찾을 수 없습니다: {dsl_path}")
            sys.exit(1)

        # DSL 읽기
        with open(dsl_path, 'r', encoding='utf-8') as f:
            dsl = json.load(f)
        
        # 배경 이미지 처리
        if args.bgImg and os.path.exists(args.bgImg):
            with open(args.bgImg, 'rb') as f:
                image_data = f.read()
                base64_str = base64.b64encode(image_data).decode('utf-8')
                data_url = f"data:image/png;base64,{base64_str}"
                
                dsl['Thumbnail']['Background']['type'] = 'image'
                dsl['Thumbnail']['Background']['imagePath'] = data_url
        
        # 제목/부제목 덮어쓰기
        if 'Texts' in dsl.get('Thumbnail', {}):
            for txt in dsl['Thumbnail']['Texts']:
                if args.title and txt.get('type') == 'title':
                    txt['content'] = normalize_text(args.title)
                if args.subtitle and txt.get('type') == 'subtitle':
                    txt['content'] = normalize_text(args.subtitle)
        
        # 썸네일 생성
        ThumbnailRenderer.render_thumbnail(dsl, output_path)
    finally:
        try:
            os.chdir(cwd_backup)
        except Exception:
            pass
        if staging:
            shutil.rmtree(staging, ignore_errors=True)


def override_dsl_with_args(dsl: Dict, args: argparse.Namespace) -> Dict:
    """CLI 파라미터로 DSL 덮어쓰기"""
    thumbnail = dsl.get('Thumbnail', {})
    
    # 해상도 덮어쓰기
    resolution_mode = getattr(args, 'resolution_mode', None)
    aspect_ratio = getattr(args, 'aspect_ratio', None)
    width = getattr(args, 'width', None)
    height = getattr(args, 'height', None)
    
    if resolution_mode:
        if resolution_mode == 'preset':
            thumbnail['Resolution'] = {
                'type': 'preset',
                'value': aspect_ratio or '16:9'
            }
        elif resolution_mode == 'fixedRatio':
            thumbnail['Resolution'] = {
                'type': 'fixedRatio',
                'ratioValue': aspect_ratio or '16:9',
                'width': width or 480
            }
        else:  # custom
            thumbnail['Resolution'] = {
                'type': 'custom',
                'width': width or 480,
                'height': height or 270
            }
    elif aspect_ratio or width or height:
        # resolution_mode가 없어도 다른 파라미터가 있으면 업데이트
        resolution = thumbnail.get('Resolution', {})
        if aspect_ratio:
            if resolution.get('type') == 'preset':
                resolution['value'] = aspect_ratio
            elif resolution.get('type') == 'fixedRatio':
                resolution['ratioValue'] = aspect_ratio
        if width:
            if resolution.get('type') == 'custom':
                resolution['width'] = width
            elif resolution.get('type') == 'fixedRatio':
                resolution['width'] = width
        if height:
            if resolution.get('type') == 'custom':
                resolution['height'] = height
        thumbnail['Resolution'] = resolution
    
    # 배경 덮어쓰기
    background_type = getattr(args, 'background_type', None)
    background_color = getattr(args, 'background_color', None)
    background_image = getattr(args, 'background_image', None)
    background_opacity = getattr(args, 'background_opacity', None)
    background_blur = getattr(args, 'background_blur', None)
    
    if background_type:
        if background_type == 'image' and background_image:
            # 이미지를 base64로 변환
            if os.path.exists(background_image):
                with open(background_image, 'rb') as f:
                    image_data = f.read()
                    base64_str = base64.b64encode(image_data).decode('utf-8')
                    data_url = f"data:image/png;base64,{base64_str}"
                
                thumbnail['Background'] = {
                    'type': 'image',
                    'imagePath': data_url,
                    'imageOpacity': (background_opacity if background_opacity is not None else 100) / 100.0,
                    'imageBlur': background_blur if background_blur is not None else 0
                }
            else:
                print(f"경고: 배경 이미지를 찾을 수 없습니다: {background_image}")
        elif background_type == 'gradient':
            thumbnail['Background'] = {
                'type': 'gradient',
                'colors': [background_color or '#ffffff', '#000000']
            }
        else:  # solid
            thumbnail['Background'] = {
                'type': 'solid',
                'color': background_color or '#ffffff'
            }
    else:
        # background_type이 없어도 다른 배경 파라미터가 있으면 업데이트
        background = thumbnail.get('Background', {})
        if background_color:
            if background.get('type') == 'solid':
                background['color'] = background_color
            elif background.get('type') == 'gradient':
                if 'colors' not in background:
                    background['colors'] = [background_color, '#000000']
                else:
                    background['colors'][0] = background_color
        if background_image:
            if os.path.exists(background_image):
                with open(background_image, 'rb') as f:
                    image_data = f.read()
                    base64_str = base64.b64encode(image_data).decode('utf-8')
                    data_url = f"data:image/png;base64,{base64_str}"
                background['type'] = 'image'
                background['imagePath'] = data_url
            else:
                print(f"경고: 배경 이미지를 찾을 수 없습니다: {background_image}")
        if background_opacity is not None:
            if background.get('type') == 'image':
                background['imageOpacity'] = background_opacity / 100.0
        if background_blur is not None:
            if background.get('type') == 'image':
                background['imageBlur'] = background_blur
        if background:
            thumbnail['Background'] = background
    
    # 텍스트 덮어쓰기
    texts = thumbnail.get('Texts', [])
    
    # 제목 찾기 또는 생성
    title_text = None
    for txt in texts:
        if txt.get('type') == 'title':
            title_text = txt
            break
    
    if title_text is None:
        title_text = {
            'type': 'title',
            'content': '',
            'gridPosition': 'tl',
            'font': {'name': 'SBAggroB', 'faces': []},
            'fontSize': 48,
            'color': '#000000',
            'fontWeight': 'bold',
            'fontStyle': 'normal',
            'lineHeight': 1.1,
            'wordWrap': False,
            'outline': None,
            'enabled': True
        }
        texts.append(title_text)
    
    # 제목 파라미터 적용
    title_text_param = getattr(args, 'title_text', None)
    title_position = getattr(args, 'title_position', None)
    title_font_name = getattr(args, 'title_font_name', None)
    title_font_url = getattr(args, 'title_font_url', None)
    title_font_file = getattr(args, 'title_font_file', None)
    title_font_weight = getattr(args, 'title_font_weight', None)
    title_font_style = getattr(args, 'title_font_style', None)
    title_font_size = getattr(args, 'title_font_size', None)
    title_color = getattr(args, 'title_color', None)
    title_outline = getattr(args, 'title_outline', False)
    title_outline_thickness = getattr(args, 'title_outline_thickness', None)
    title_word_wrap = getattr(args, 'title_word_wrap', False)
    
    if title_text_param is not None:
        title_text['content'] = title_text_param.replace('\\n', '\n')
    if title_position:
        title_text['gridPosition'] = title_position
    if title_font_name:
        title_text['font']['name'] = title_font_name
        if not title_text['font'].get('faces'):
            title_text['font']['faces'] = [{'name': title_font_name, 'url': '', 'weight': 'bold', 'style': 'normal'}]
        else:
            title_text['font']['faces'][0]['name'] = title_font_name
    if title_font_url or title_font_file:
        font_url = title_font_file if title_font_file else title_font_url
        if not title_text['font'].get('faces'):
            title_text['font']['faces'] = [{'name': title_text['font'].get('name', 'SBAggroB'), 'url': font_url, 'weight': 'bold', 'style': 'normal'}]
        else:
            title_text['font']['faces'][0]['url'] = font_url
    if title_font_weight:
        title_text['fontWeight'] = title_font_weight
        if not title_text['font'].get('faces'):
            title_text['font']['faces'] = [{'name': title_text['font'].get('name', 'SBAggroB'), 'url': '', 'weight': title_font_weight, 'style': 'normal'}]
        else:
            title_text['font']['faces'][0]['weight'] = title_font_weight
    if title_font_style:
        title_text['fontStyle'] = title_font_style
        if not title_text['font'].get('faces'):
            title_text['font']['faces'] = [{'name': title_text['font'].get('name', 'SBAggroB'), 'url': '', 'weight': 'bold', 'style': title_font_style}]
        else:
            title_text['font']['faces'][0]['style'] = title_font_style
    if title_font_size:
        title_text['fontSize'] = title_font_size
    if title_color:
        title_text['color'] = title_color
    # 외곽선 처리: --title-outline 플래그가 있거나 thickness가 지정되면 활성화
    if title_outline or title_outline_thickness is not None:
        if not title_text.get('outline'):
            title_text['outline'] = {'thickness': title_outline_thickness if title_outline_thickness is not None else 7, 'color': '#000000'}
        elif title_outline_thickness is not None:
            title_text['outline']['thickness'] = title_outline_thickness
    # title_outline이 명시적으로 False이고 thickness도 없으면 outline 제거 (기본값 유지)
    # 실제로는 파라미터가 없으면 기존 값을 유지하므로 여기서는 처리하지 않음
    if title_word_wrap:
        title_text['wordWrap'] = True
    
    # 부제목 찾기 또는 생성
    subtitle_text = None
    for txt in texts:
        if txt.get('type') == 'subtitle':
            subtitle_text = txt
            break
    
    if subtitle_text is None:
        subtitle_text = {
            'type': 'subtitle',
            'content': '',
            'gridPosition': 'bl',
            'font': {'name': 'SBAggroB', 'faces': []},
            'fontSize': 24,
            'color': '#ffffff',
            'fontWeight': 'normal',
            'fontStyle': 'normal',
            'lineHeight': 1.1,
            'wordWrap': False,
            'outline': None,
            'enabled': True
        }
        texts.append(subtitle_text)
    
    # 부제목 파라미터 적용
    subtitle_visible = getattr(args, 'subtitle_visible', None)
    subtitle_text_param = getattr(args, 'subtitle_text', None)
    subtitle_position = getattr(args, 'subtitle_position', None)
    subtitle_font_name = getattr(args, 'subtitle_font_name', None)
    subtitle_font_url = getattr(args, 'subtitle_font_url', None)
    subtitle_font_file = getattr(args, 'subtitle_font_file', None)
    subtitle_font_weight = getattr(args, 'subtitle_font_weight', None)
    subtitle_font_style = getattr(args, 'subtitle_font_style', None)
    subtitle_font_size = getattr(args, 'subtitle_font_size', None)
    subtitle_color = getattr(args, 'subtitle_color', None)
    subtitle_word_wrap = getattr(args, 'subtitle_word_wrap', False)
    
    if subtitle_visible is not None:
        subtitle_text['enabled'] = subtitle_visible
    if subtitle_text_param is not None:
        subtitle_text['content'] = subtitle_text_param.replace('\\n', '\n')
    if subtitle_position:
        subtitle_text['gridPosition'] = subtitle_position
    if subtitle_font_name:
        subtitle_text['font']['name'] = subtitle_font_name
        if not subtitle_text['font'].get('faces'):
            subtitle_text['font']['faces'] = [{'name': subtitle_font_name, 'url': '', 'weight': 'normal', 'style': 'normal'}]
        else:
            subtitle_text['font']['faces'][0]['name'] = subtitle_font_name
    if subtitle_font_url or subtitle_font_file:
        font_url = subtitle_font_file if subtitle_font_file else subtitle_font_url
        if not subtitle_text['font'].get('faces'):
            subtitle_text['font']['faces'] = [{'name': subtitle_text['font'].get('name', 'SBAggroB'), 'url': font_url, 'weight': 'normal', 'style': 'normal'}]
        else:
            subtitle_text['font']['faces'][0]['url'] = font_url
    if subtitle_font_weight:
        subtitle_text['fontWeight'] = subtitle_font_weight
        if not subtitle_text['font'].get('faces'):
            subtitle_text['font']['faces'] = [{'name': subtitle_text['font'].get('name', 'SBAggroB'), 'url': '', 'weight': subtitle_font_weight, 'style': 'normal'}]
        else:
            subtitle_text['font']['faces'][0]['weight'] = subtitle_font_weight
    if subtitle_font_style:
        subtitle_text['fontStyle'] = subtitle_font_style
        if not subtitle_text['font'].get('faces'):
            subtitle_text['font']['faces'] = [{'name': subtitle_text['font'].get('name', 'SBAggroB'), 'url': '', 'weight': 'normal', 'style': subtitle_font_style}]
        else:
            subtitle_text['font']['faces'][0]['style'] = subtitle_font_style
    if subtitle_font_size:
        subtitle_text['fontSize'] = subtitle_font_size
    if subtitle_color:
        subtitle_text['color'] = subtitle_color
    if subtitle_word_wrap:
        subtitle_text['wordWrap'] = True
    
    thumbnail['Texts'] = texts
    dsl['Thumbnail'] = thumbnail
    
    return dsl


def generate_thumbnail_from_args(args: argparse.Namespace):
    """generate-thumbnail 명령어 처리"""
    staging = None
    cwd_backup = os.getcwd()
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.abspath(output_path)
    
    try:
        # .thl 패키지 지원
        dsl_path = args.dsl or 'thumbnail.json'
        if dsl_path.lower().endswith('.thl') and os.path.exists(dsl_path):
            staging = tempfile.mkdtemp(prefix='thl_run_')
            with zipfile.ZipFile(args.dsl, 'r') as zf:
                zf.extractall(staging)
            os.chdir(staging)
            dsl_path = os.path.join(staging, 'thumbnail.json')
        
        # DSL 파일 확인
        if not os.path.exists(dsl_path):
            print(f"오류: DSL 파일을 찾을 수 없습니다: {dsl_path}")
            sys.exit(1)
        
        # DSL 읽기
        with open(dsl_path, 'r', encoding='utf-8') as f:
            dsl = json.load(f)
        
        # CLI 파라미터로 DSL 덮어쓰기
        dsl = override_dsl_with_args(dsl, args)
        
        # 썸네일 생성
        ThumbnailRenderer.render_thumbnail(dsl, output_path)
    finally:
        try:
            os.chdir(cwd_backup)
        except Exception:
            pass
        if staging:
            shutil.rmtree(staging, ignore_errors=True)


if __name__ == '__main__':
    main()
