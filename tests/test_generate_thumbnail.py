#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate-thumbnail 명령어 파라미터 테스트
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from thumbnail_maker.cli import override_dsl_with_args, generate_thumbnail_from_args
from thumbnail_maker.renderer import ThumbnailRenderer


@pytest.fixture
def sample_dsl():
    """기본 DSL 샘플"""
    return {
        "Thumbnail": {
            "Resolution": {
                "type": "preset",
                "value": "16:9"
            },
            "Background": {
                "type": "solid",
                "color": "#a3e635"
            },
            "Texts": [
                {
                    "type": "title",
                    "content": "기본 제목",
                    "gridPosition": "tl",
                    "font": {
                        "name": "SBAggroB",
                        "faces": [{
                            "name": "SBAggroB",
                            "url": "https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff",
                            "weight": "bold",
                            "style": "normal"
                        }]
                    },
                    "fontSize": 48,
                    "color": "#4ade80",
                    "fontWeight": "bold",
                    "fontStyle": "normal",
                    "lineHeight": 1.1,
                    "wordWrap": False,
                    "outline": {
                        "thickness": 7,
                        "color": "#000000"
                    },
                    "enabled": True
                },
                {
                    "type": "subtitle",
                    "content": "기본 부제목",
                    "gridPosition": "bl",
                    "font": {
                        "name": "SBAggroB",
                        "faces": [{
                            "name": "SBAggroB",
                            "url": "https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff",
                            "weight": "normal",
                            "style": "normal"
                        }]
                    },
                    "fontSize": 24,
                    "color": "#ffffff",
                    "fontWeight": "normal",
                    "fontStyle": "normal",
                    "lineHeight": 1.1,
                    "wordWrap": False,
                    "outline": None,
                    "enabled": True
                }
            ]
        },
        "TemplateMeta": {
            "name": "",
            "shareable": False
        }
    }


@pytest.fixture
def temp_dsl_file(sample_dsl):
    """임시 DSL 파일 생성"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(sample_dsl, f, ensure_ascii=False, indent=2)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_output_file():
    """임시 출력 파일 경로"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestResolutionParameters:
    """해상도 관련 파라미터 테스트"""
    
    def test_resolution_mode_preset(self, sample_dsl):
        """preset 모드 테스트"""
        args = MagicMock()
        args.resolution_mode = 'preset'
        args.aspect_ratio = '9:16'
        args.width = None
        args.height = None
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        assert result['Thumbnail']['Resolution']['type'] == 'preset'
        assert result['Thumbnail']['Resolution']['value'] == '9:16'
    
    def test_resolution_mode_fixed_ratio(self, sample_dsl):
        """fixedRatio 모드 테스트"""
        args = MagicMock()
        args.resolution_mode = 'fixedRatio'
        args.aspect_ratio = '4:3'
        args.width = 800
        args.height = None
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        assert result['Thumbnail']['Resolution']['type'] == 'fixedRatio'
        assert result['Thumbnail']['Resolution']['ratioValue'] == '4:3'
        assert result['Thumbnail']['Resolution']['width'] == 800
    
    def test_resolution_mode_custom(self, sample_dsl):
        """custom 모드 테스트"""
        args = MagicMock()
        args.resolution_mode = 'custom'
        args.aspect_ratio = None
        args.width = 1920
        args.height = 1080
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        assert result['Thumbnail']['Resolution']['type'] == 'custom'
        assert result['Thumbnail']['Resolution']['width'] == 1920
        assert result['Thumbnail']['Resolution']['height'] == 1080
    
    def test_aspect_ratio_only(self, sample_dsl):
        """aspect_ratio만 지정한 경우"""
        args = MagicMock()
        args.resolution_mode = None
        args.aspect_ratio = '1:1'
        args.width = None
        args.height = None
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        # 기존 preset 모드의 value가 업데이트되어야 함
        assert result['Thumbnail']['Resolution']['value'] == '1:1'


class TestBackgroundParameters:
    """배경 관련 파라미터 테스트"""
    
    def test_background_type_solid(self, sample_dsl):
        """solid 배경 타입 테스트"""
        args = MagicMock()
        args.background_type = 'solid'
        args.background_color = '#ff0000'
        args.background_image = None
        args.background_opacity = None
        args.background_blur = None
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        assert result['Thumbnail']['Background']['type'] == 'solid'
        assert result['Thumbnail']['Background']['color'] == '#ff0000'
    
    def test_background_type_gradient(self, sample_dsl):
        """gradient 배경 타입 테스트"""
        args = MagicMock()
        args.background_type = 'gradient'
        args.background_color = '#00ff00'
        args.background_image = None
        args.background_opacity = None
        args.background_blur = None
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        assert result['Thumbnail']['Background']['type'] == 'gradient'
        assert result['Thumbnail']['Background']['colors'][0] == '#00ff00'
    
    def test_background_type_image(self, sample_dsl, temp_output_file):
        """image 배경 타입 테스트"""
        # 테스트용 이미지 파일 생성 (실제로는 존재하는 파일이어야 함)
        # 여기서는 mock을 사용하여 파일 존재 여부를 시뮬레이션
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_file.read.return_value = b'fake_image_data'
                mock_open.return_value.__enter__.return_value = mock_file
                
                args = MagicMock()
                args.background_type = 'image'
                args.background_color = None
                args.background_image = '/path/to/image.png'
                args.background_opacity = 80
                args.background_blur = 5
                
                result = override_dsl_with_args(sample_dsl.copy(), args)
                
                assert result['Thumbnail']['Background']['type'] == 'image'
                assert result['Thumbnail']['Background']['imagePath'].startswith('data:image')
                assert result['Thumbnail']['Background']['imageOpacity'] == 0.8
                assert result['Thumbnail']['Background']['imageBlur'] == 5
    
    def test_background_color_only(self, sample_dsl):
        """background_color만 지정한 경우"""
        args = MagicMock()
        args.background_type = None
        args.background_color = '#0000ff'
        args.background_image = None
        args.background_opacity = None
        args.background_blur = None
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        # 기존 solid 타입의 color가 업데이트되어야 함
        assert result['Thumbnail']['Background']['color'] == '#0000ff'
    
    def test_background_opacity_only(self, sample_dsl):
        """background_opacity만 지정한 경우"""
        args = MagicMock()
        args.background_type = None
        args.background_color = None
        args.background_image = None
        args.background_opacity = 50
        args.background_blur = None
        
        # 기존 배경이 image 타입이 아니면 opacity는 적용되지 않음
        # image 타입으로 변경 후 테스트
        sample_dsl['Thumbnail']['Background'] = {
            'type': 'image',
            'imagePath': 'data:image/png;base64,test',
            'imageOpacity': 1.0,
            'imageBlur': 0
        }
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        assert result['Thumbnail']['Background']['imageOpacity'] == 0.5


class TestTitleParameters:
    """제목 관련 파라미터 테스트"""
    
    def test_title_text(self, sample_dsl):
        """제목 텍스트 변경 테스트"""
        args = MagicMock()
        args.title_text = '새로운 제목'
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['content'] == '새로운 제목'
    
    def test_title_text_with_newline(self, sample_dsl):
        """제목 텍스트에 줄바꿈 포함 테스트"""
        args = MagicMock()
        args.title_text = '첫 줄\\n두 번째 줄'
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert '\n' in title_text['content']
        assert '\\n' not in title_text['content']
    
    def test_title_position(self, sample_dsl):
        """제목 위치 변경 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = 'bc'
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['gridPosition'] == 'bc'
    
    def test_title_font_name(self, sample_dsl):
        """제목 폰트 이름 변경 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = 'NewFont'
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['font']['name'] == 'NewFont'
        assert title_text['font']['faces'][0]['name'] == 'NewFont'
    
    def test_title_font_url(self, sample_dsl):
        """제목 폰트 URL 변경 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = 'https://example.com/font.woff'
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['font']['faces'][0]['url'] == 'https://example.com/font.woff'
    
    def test_title_font_file(self, sample_dsl):
        """제목 로컬 폰트 파일 변경 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = '/path/to/local/font.ttf'
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['font']['faces'][0]['url'] == '/path/to/local/font.ttf'
    
    def test_title_font_weight(self, sample_dsl):
        """제목 폰트 굵기 변경 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = 'normal'
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['fontWeight'] == 'normal'
        assert title_text['font']['faces'][0]['weight'] == 'normal'
    
    def test_title_font_style(self, sample_dsl):
        """제목 폰트 스타일 변경 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = 'italic'
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['fontStyle'] == 'italic'
        assert title_text['font']['faces'][0]['style'] == 'italic'
    
    def test_title_font_size(self, sample_dsl):
        """제목 폰트 크기 변경 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = 72
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['fontSize'] == 72
    
    def test_title_color(self, sample_dsl):
        """제목 색상 변경 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = '#ff00ff'
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['color'] == '#ff00ff'
    
    def test_title_outline(self, sample_dsl):
        """제목 외곽선 활성화 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = True
        args.title_outline_thickness = 10
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['outline'] is not None
        assert title_text['outline']['thickness'] == 10
    
    def test_title_outline_thickness_only(self, sample_dsl):
        """제목 외곽선 두께만 지정 테스트"""
        # 기존 outline 제거
        sample_dsl['Thumbnail']['Texts'][0]['outline'] = None
        
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = 5
        args.title_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['outline'] is not None
        assert title_text['outline']['thickness'] == 5
    
    def test_title_word_wrap(self, sample_dsl):
        """제목 단어 단위 줄바꿈 테스트"""
        args = MagicMock()
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = True
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['wordWrap'] is True


class TestSubtitleParameters:
    """부제목 관련 파라미터 테스트"""
    
    def test_subtitle_visible(self, sample_dsl):
        """부제목 표시 여부 테스트"""
        args = MagicMock()
        args.subtitle_visible = False
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['enabled'] is False
    
    def test_subtitle_text(self, sample_dsl):
        """부제목 텍스트 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = '새로운 부제목'
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['content'] == '새로운 부제목'
    
    def test_subtitle_position(self, sample_dsl):
        """부제목 위치 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = 'tr'
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['gridPosition'] == 'tr'
    
    def test_subtitle_font_name(self, sample_dsl):
        """부제목 폰트 이름 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = 'SubFont'
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['font']['name'] == 'SubFont'
        assert subtitle_text['font']['faces'][0]['name'] == 'SubFont'
    
    def test_subtitle_font_url(self, sample_dsl):
        """부제목 폰트 URL 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = 'https://example.com/subfont.woff'
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['font']['faces'][0]['url'] == 'https://example.com/subfont.woff'
    
    def test_subtitle_font_file(self, sample_dsl):
        """부제목 로컬 폰트 파일 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = '/path/to/subfont.ttf'
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['font']['faces'][0]['url'] == '/path/to/subfont.ttf'
    
    def test_subtitle_font_weight(self, sample_dsl):
        """부제목 폰트 굵기 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = 'bold'
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['fontWeight'] == 'bold'
        assert subtitle_text['font']['faces'][0]['weight'] == 'bold'
    
    def test_subtitle_font_style(self, sample_dsl):
        """부제목 폰트 스타일 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = 'italic'
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['fontStyle'] == 'italic'
        assert subtitle_text['font']['faces'][0]['style'] == 'italic'
    
    def test_subtitle_font_size(self, sample_dsl):
        """부제목 폰트 크기 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = 36
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['fontSize'] == 36
    
    def test_subtitle_color(self, sample_dsl):
        """부제목 색상 변경 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = '#00ffff'
        args.subtitle_word_wrap = False
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['color'] == '#00ffff'
    
    def test_subtitle_word_wrap(self, sample_dsl):
        """부제목 단어 단위 줄바꿈 테스트"""
        args = MagicMock()
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = True
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['wordWrap'] is True


class TestCombinedParameters:
    """여러 파라미터 조합 테스트"""
    
    def test_multiple_title_parameters(self, sample_dsl):
        """여러 제목 파라미터 동시 적용 테스트"""
        args = MagicMock()
        args.title_text = '조합 테스트'
        args.title_position = 'mc'
        args.title_font_name = 'TestFont'
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = 'normal'
        args.title_font_style = 'italic'
        args.title_font_size = 60
        args.title_color = '#123456'
        args.title_outline = True
        args.title_outline_thickness = 3
        args.title_word_wrap = True
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['content'] == '조합 테스트'
        assert title_text['gridPosition'] == 'mc'
        assert title_text['font']['name'] == 'TestFont'
        assert title_text['fontWeight'] == 'normal'
        assert title_text['fontStyle'] == 'italic'
        assert title_text['fontSize'] == 60
        assert title_text['color'] == '#123456'
        assert title_text['outline']['thickness'] == 3
        assert title_text['wordWrap'] is True
    
    def test_all_parameters(self, sample_dsl):
        """모든 파라미터 동시 적용 테스트"""
        args = MagicMock()
        # 해상도
        args.resolution_mode = 'custom'
        args.aspect_ratio = None
        args.width = 1920
        args.height = 1080
        # 배경
        args.background_type = 'solid'
        args.background_color = '#abcdef'
        args.background_image = None
        args.background_opacity = None
        args.background_blur = None
        # 제목
        args.title_text = '전체 테스트'
        args.title_position = 'tl'
        args.title_font_name = 'TitleFont'
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = 'bold'
        args.title_font_style = 'normal'
        args.title_font_size = 64
        args.title_color = '#ff0000'
        args.title_outline = True
        args.title_outline_thickness = 5
        args.title_word_wrap = False
        # 부제목
        args.subtitle_visible = True
        args.subtitle_text = '부제목 테스트'
        args.subtitle_position = 'br'
        args.subtitle_font_name = 'SubFont'
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = 'normal'
        args.subtitle_font_style = 'italic'
        args.subtitle_font_size = 32
        args.subtitle_color = '#00ff00'
        args.subtitle_word_wrap = True
        
        result = override_dsl_with_args(sample_dsl.copy(), args)
        
        # 해상도 확인
        assert result['Thumbnail']['Resolution']['type'] == 'custom'
        assert result['Thumbnail']['Resolution']['width'] == 1920
        assert result['Thumbnail']['Resolution']['height'] == 1080
        
        # 배경 확인
        assert result['Thumbnail']['Background']['type'] == 'solid'
        assert result['Thumbnail']['Background']['color'] == '#abcdef'
        
        # 제목 확인
        title_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'title')
        assert title_text['content'] == '전체 테스트'
        assert title_text['gridPosition'] == 'tl'
        assert title_text['fontSize'] == 64
        assert title_text['color'] == '#ff0000'
        
        # 부제목 확인
        subtitle_text = next(t for t in result['Thumbnail']['Texts'] if t['type'] == 'subtitle')
        assert subtitle_text['content'] == '부제목 테스트'
        assert subtitle_text['gridPosition'] == 'br'
        assert subtitle_text['fontSize'] == 32
        assert subtitle_text['color'] == '#00ff00'


class TestGenerateThumbnailFromArgs:
    """generate_thumbnail_from_args 함수 통합 테스트"""
    
    def test_generate_with_dsl_file(self, temp_dsl_file, temp_output_file):
        """DSL 파일로 썸네일 생성 테스트"""
        args = MagicMock()
        args.dsl = temp_dsl_file
        args.output = temp_output_file
        args.resolution_mode = None
        args.aspect_ratio = None
        args.width = None
        args.height = None
        args.background_type = None
        args.background_color = None
        args.background_image = None
        args.background_opacity = None
        args.background_blur = None
        args.title_text = None
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        # 실제 렌더링은 시간이 걸리므로 mock 사용
        with patch('thumbnail_maker.cli.ThumbnailRenderer.render_thumbnail') as mock_render:
            generate_thumbnail_from_args(args)
            mock_render.assert_called_once()
            # DSL이 올바르게 전달되었는지 확인
            call_args = mock_render.call_args
            assert call_args[0][1] == temp_output_file
    
    def test_generate_with_parameters(self, temp_dsl_file, temp_output_file):
        """파라미터와 함께 썸네일 생성 테스트"""
        args = MagicMock()
        args.dsl = temp_dsl_file
        args.output = temp_output_file
        args.resolution_mode = 'preset'
        args.aspect_ratio = '1:1'
        args.width = None
        args.height = None
        args.background_type = 'solid'
        args.background_color = '#ff0000'
        args.background_image = None
        args.background_opacity = None
        args.background_blur = None
        args.title_text = '테스트 제목'
        args.title_position = None
        args.title_font_name = None
        args.title_font_url = None
        args.title_font_file = None
        args.title_font_weight = None
        args.title_font_style = None
        args.title_font_size = None
        args.title_color = None
        args.title_outline = False
        args.title_outline_thickness = None
        args.title_word_wrap = False
        args.subtitle_visible = None
        args.subtitle_text = None
        args.subtitle_position = None
        args.subtitle_font_name = None
        args.subtitle_font_url = None
        args.subtitle_font_file = None
        args.subtitle_font_weight = None
        args.subtitle_font_style = None
        args.subtitle_font_size = None
        args.subtitle_color = None
        args.subtitle_word_wrap = False
        
        with patch('thumbnail_maker.cli.ThumbnailRenderer.render_thumbnail') as mock_render:
            generate_thumbnail_from_args(args)
            mock_render.assert_called_once()
            # DSL이 파라미터로 수정되었는지 확인
            call_args = mock_render.call_args
            dsl = call_args[0][0]
            assert dsl['Thumbnail']['Resolution']['value'] == '1:1'
            assert dsl['Thumbnail']['Background']['color'] == '#ff0000'
            title_text = next(t for t in dsl['Thumbnail']['Texts'] if t['type'] == 'title')
            assert title_text['content'] == '테스트 제목'
