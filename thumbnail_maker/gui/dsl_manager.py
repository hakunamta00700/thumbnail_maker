#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSL 생성, 로드, 저장 관리 모듈
"""

import json
import os
import base64
import tempfile
import zipfile
import shutil
from typing import Dict

from ..renderer import ThumbnailRenderer, sanitize


class DSLManager:
    """DSL 관리 클래스"""
    
    @staticmethod
    def generate_dsl(gui) -> Dict:
        """GUI 위젯에서 DSL 생성"""
        # 해상도 결정
        res_mode = gui.res_mode.currentText()
        if res_mode == 'preset':
            resolution = {
                'type': 'preset',
                'value': gui.aspect_ratio.currentText()
            }
        elif res_mode == 'fixedRatio':
            resolution = {
                'type': 'fixedRatio',
                'ratioValue': gui.aspect_ratio.currentText(),
                'width': gui.width_spin.value()
            }
        else:  # custom
            resolution = {
                'type': 'custom',
                'width': gui.width_spin.value(),
                'height': gui.height_spin.value()
            }
        
        # 배경 결정
        bg_type = gui.bg_type.currentText()
        if bg_type == 'image' and gui.bg_image_path.text():
            # 이미지를 base64로 변환
            with open(gui.bg_image_path.text(), 'rb') as f:
                image_data = f.read()
                base64_str = base64.b64encode(image_data).decode('utf-8')
                data_url = f"data:image/png;base64,{base64_str}"
                
            background = {
                'type': 'image',
                'imagePath': data_url,
                'imageOpacity': gui.bg_opacity.value() / 100.0,
                'imageBlur': gui.bg_blur.value()
            }
        elif bg_type == 'gradient':
            background = {
                'type': 'gradient',
                'colors': [gui.bg_color, '#000000']
            }
        else:  # solid
            background = {
                'type': 'solid',
                'color': gui.bg_color
            }
        
        # 텍스트 설정
        # 제목 폰트 소스 분기
        title_use_local = gui.title_font_source.currentText() == '로컬 폰트 파일'
        title_face_url = gui.title_font_file.text() if title_use_local and gui.title_font_file.text() else (gui.title_font_url.text() or 'https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff')
        # 부제목 폰트 소스 분기
        subtitle_use_local = gui.subtitle_font_source.currentText() == '로컬 폰트 파일'
        subtitle_face_url = gui.subtitle_font_file.text() if subtitle_use_local and gui.subtitle_font_file.text() else (gui.subtitle_font_url.text() or 'https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff')

        texts = [
            {
                'type': 'title',
                'content': gui.title_text.toPlainText(),
                'gridPosition': gui.title_position.currentText(),
                'font': {
                    'name': gui.title_font_name.text() or 'SBAggroB',
                    'faces': [{
                        'name': gui.title_font_name.text() or 'SBAggroB',
                        'url': title_face_url,
                        'weight': gui.title_font_weight.currentText() or 'bold',
                        'style': gui.title_font_style.currentText() or 'normal'
                    }]
                },
                'fontSize': gui.title_font_size.value(),
                'color': gui.title_color,
                'fontWeight': gui.title_font_weight.currentText() or 'bold',
                'fontStyle': gui.title_font_style.currentText() or 'normal',
                'lineHeight': 1.1,
                'wordWrap': gui.title_word_wrap.isChecked(),
                'outline': {
                    'thickness': gui.title_outline_thickness.value(),
                    'color': '#000000'
                } if gui.title_outline_check.isChecked() else None,
                'enabled': True
            }
        ]
        
        # 부제목 추가 (체크 여부와 관계없이 항상 추가하되, enabled 필드로 제어)
        texts.append({
            'type': 'subtitle',
            'content': gui.subtitle_text.toPlainText(),
            'gridPosition': gui.subtitle_position.currentText(),
            'font': {
                'name': gui.subtitle_font_name.text() or 'SBAggroB',
                'faces': [{
                    'name': gui.subtitle_font_name.text() or 'SBAggroB',
                    'url': subtitle_face_url,
                    'weight': gui.subtitle_font_weight.currentText() or 'normal',
                    'style': gui.subtitle_font_style.currentText() or 'normal'
                }]
            },
            'fontSize': gui.subtitle_font_size.value(),
            'color': gui.subtitle_color,
            'fontWeight': gui.subtitle_font_weight.currentText() or 'normal',
            'fontStyle': gui.subtitle_font_style.currentText() or 'normal',
            'lineHeight': 1.1,
            'wordWrap': gui.subtitle_word_wrap.isChecked(),
            'outline': None,
            'enabled': gui.subtitle_visible.isChecked()
        })
        
        dsl = {
            'Thumbnail': {
                'Resolution': resolution,
                'Background': background,
                'Texts': texts
            },
            'TemplateMeta': {
                'name': '',
                'shareable': False
            }
        }
        
        return dsl
    
    @staticmethod
    def load_dsl_to_gui(gui, dsl: Dict):
        """DSL 데이터를 GUI 위젯에 로드"""
        thumbnail = dsl.get('Thumbnail', {})
        
        # 해상도 설정
        resolution = thumbnail.get('Resolution', {})
        res_type = resolution.get('type', 'preset')
        gui.res_mode.setCurrentText(res_type)
        
        if res_type == 'preset':
            gui.aspect_ratio.setCurrentText(resolution.get('value', '16:9'))
        elif res_type == 'fixedRatio':
            gui.aspect_ratio.setCurrentText(resolution.get('ratioValue', '16:9'))
            gui.width_spin.setValue(resolution.get('width', 480))
        else:  # custom
            gui.width_spin.setValue(resolution.get('width', 480))
            gui.height_spin.setValue(resolution.get('height', 270))
        
        # 배경 설정
        background = thumbnail.get('Background', {})
        bg_type = background.get('type', 'solid')
        gui.bg_type.setCurrentText(bg_type)
        
        if bg_type == 'solid':
            gui.bg_color = background.get('color', '#a3e635')
        elif bg_type == 'gradient':
            colors = background.get('colors', [])
            if colors:
                gui.bg_color = colors[0]
        elif bg_type == 'image':
            img_path = background.get('imagePath', '')
            if img_path.startswith('data:image'):
                # base64 이미지는 임시 파일로 저장
                header, encoded = img_path.split(',', 1)
                image_data = base64.b64decode(encoded)
                temp_path = os.path.join(tempfile.gettempdir(), 'thl_temp_bg.png')
                with open(temp_path, 'wb') as f:
                    f.write(image_data)
                gui.bg_image_path.setText(temp_path)
            else:
                gui.bg_image_path.setText(img_path)
            gui.bg_opacity.setValue(int(background.get('imageOpacity', 1.0) * 100))
            gui.bg_blur.setValue(background.get('imageBlur', 0))
        
        # 텍스트 설정
        texts = thumbnail.get('Texts', [])
        subtitle_found = False
        for txt in texts:
            txt_type = txt.get('type')
            if txt_type == 'title':
                gui.title_text.setPlainText(txt.get('content', ''))
                gui.title_position.setCurrentText(txt.get('gridPosition', 'tl'))
                gui.title_font_size.setValue(txt.get('fontSize', 48))
                gui.title_color = txt.get('color', '#4ade80')
                
                font = txt.get('font', {})
                font_name = font.get('name', 'SBAggroB')
                gui.title_font_name.setText(font_name)
                
                faces = font.get('faces', [])
                if faces:
                    face = faces[0]
                    url = face.get('url', '')
                    if url and os.path.exists(url):
                        # 로컬 파일
                        gui.title_font_source.setCurrentText('로컬 폰트 파일')
                        gui.title_font_file.setText(url)
                    else:
                        # 웹 URL
                        gui.title_font_source.setCurrentText('웹 폰트 URL')
                        gui.title_font_url.setText(url)
                    
                    gui.title_font_weight.setCurrentText(face.get('weight', 'bold'))
                    gui.title_font_style.setCurrentText(face.get('style', 'normal'))
                
                outline = txt.get('outline')
                if outline:
                    gui.title_outline_check.setChecked(True)
                    gui.title_outline_thickness.setValue(outline.get('thickness', 7))
                else:
                    gui.title_outline_check.setChecked(False)
                
                gui.title_word_wrap.setChecked(txt.get('wordWrap', False))
                
            elif txt_type == 'subtitle':
                subtitle_found = True
                # enabled 필드를 확인하여 체크박스 상태 설정
                enabled = txt.get('enabled', True)
                gui.subtitle_visible.setChecked(enabled)
                gui.subtitle_text.setPlainText(txt.get('content', ''))
                gui.subtitle_position.setCurrentText(txt.get('gridPosition', 'bl'))
                gui.subtitle_font_size.setValue(txt.get('fontSize', 24))
                gui.subtitle_color = txt.get('color', '#ffffff')
                
                font = txt.get('font', {})
                font_name = font.get('name', 'SBAggroB')
                gui.subtitle_font_name.setText(font_name)
                
                faces = font.get('faces', [])
                if faces:
                    face = faces[0]
                    url = face.get('url', '')
                    if url and os.path.exists(url):
                        # 로컬 파일
                        gui.subtitle_font_source.setCurrentText('로컬 폰트 파일')
                        gui.subtitle_font_file.setText(url)
                    else:
                        # 웹 URL
                        gui.subtitle_font_source.setCurrentText('웹 폰트 URL')
                        gui.subtitle_font_url.setText(url)
                    
                    gui.subtitle_font_weight.setCurrentText(face.get('weight', 'normal'))
                    gui.subtitle_font_style.setCurrentText(face.get('style', 'normal'))
                
                gui.subtitle_word_wrap.setChecked(txt.get('wordWrap', False))
        
        # 부제목이 DSL에 없으면 체크 해제
        if not subtitle_found:
            gui.subtitle_visible.setChecked(False)
        
        # 미리보기 업데이트
        gui.update_preview()
    
    @staticmethod
    def save_thl_package(gui, file_path: str):
        """현재 DSL과 사용 폰트를 묶어 .thl 패키지로 저장"""
        if not hasattr(gui, 'current_dsl'):
            gui.update_preview()
        dsl = getattr(gui, 'current_dsl', DSLManager.generate_dsl(gui))
        
        staging = None
        try:
            # 스테이징 디렉토리 구성
            staging = tempfile.mkdtemp(prefix='thl_pkg_')
            fonts_dir = os.path.join(staging, 'fonts')
            os.makedirs(fonts_dir, exist_ok=True)

            # 폰트 확보 및 복사
            texts = dsl.get('Thumbnail', {}).get('Texts', [])
            try:
                # 프로젝트/fonts에 TTF 생성/보장
                ThumbnailRenderer.ensure_fonts(texts)
            except Exception as e:
                print(f"폰트 확보 경고: {e}")

            # faces를 순회하여 예상 파일명으로 복사
            faces = ThumbnailRenderer.parse_font_faces(texts)
            for face in faces:
                ttf_name = f"{sanitize(face.get('name','Font'))}-{sanitize(str(face.get('weight','normal')))}-{sanitize(str(face.get('style','normal')))}.ttf"
                src_path = os.path.join(ThumbnailRenderer._fonts_dir(), ttf_name)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, os.path.join(fonts_dir, ttf_name))

            # thumbnail.json 저장 (원본 DSL 그대로)
            with open(os.path.join(staging, 'thumbnail.json'), 'w', encoding='utf-8') as f:
                json.dump(dsl, f, ensure_ascii=False, indent=2)

            # zip -> .thl
            with zipfile.ZipFile(file_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                # 루트에 thumbnail.json
                zf.write(os.path.join(staging, 'thumbnail.json'), arcname='thumbnail.json')
                # fonts 폴더
                if os.path.isdir(fonts_dir):
                    for name in os.listdir(fonts_dir):
                        zf.write(os.path.join(fonts_dir, name), arcname=os.path.join('fonts', name))
        finally:
            if staging:
                shutil.rmtree(staging, ignore_errors=True)
    
    @staticmethod
    def load_thl_package(gui, file_path: str) -> Dict:
        """.thl 패키지를 로드하여 DSL 반환"""
        staging = None
        cwd_backup = os.getcwd()
        try:
            # .thl 파일을 임시 디렉토리에 압축 해제
            staging = tempfile.mkdtemp(prefix='thl_load_')
            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(staging)
            
            # thumbnail.json 읽기
            dsl_path = os.path.join(staging, 'thumbnail.json')
            if not os.path.exists(dsl_path):
                raise FileNotFoundError('패키지에 thumbnail.json이 없습니다.')
            
            with open(dsl_path, 'r', encoding='utf-8') as f:
                dsl = json.load(f)
            
            # 폰트 파일을 프로젝트 fonts 디렉토리로 복사
            fonts_src_dir = os.path.join(staging, 'fonts')
            if os.path.isdir(fonts_src_dir):
                fonts_dst_dir = ThumbnailRenderer._fonts_dir()
                os.makedirs(fonts_dst_dir, exist_ok=True)
                for font_file in os.listdir(fonts_src_dir):
                    src_path = os.path.join(fonts_src_dir, font_file)
                    dst_path = os.path.join(fonts_dst_dir, font_file)
                    shutil.copy2(src_path, dst_path)
            
            return dsl
        finally:
            try:
                os.chdir(cwd_backup)
            except Exception:
                pass
            if staging:
                shutil.rmtree(staging, ignore_errors=True)

