#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 기반 썸네일 생성 GUI
"""

import sys
import json
import os
import base64
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QColorDialog,
                               QSpinBox, QTextEdit, QCheckBox, QComboBox,
                               QGroupBox, QTabWidget, QLineEdit, QSlider,
                               QFileDialog, QMessageBox, QGridLayout)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor, QFont
from .renderer import ThumbnailRenderer, sanitize
try:
    from fontTools.ttLib import TTFont
except Exception:
    TTFont = None
import tempfile
import zipfile
import shutil


class PreviewThread(QThread):
    """미리보기 생성 스레드"""
    preview_ready = Signal(str)  # preview file path
    
    def __init__(self, dsl):
        super().__init__()
        self.dsl = dsl
        self.error_message = None
    
    def run(self):
        preview_path = 'preview_temp.png'
        try:
            ThumbnailRenderer.render_thumbnail(self.dsl, preview_path)
            self.preview_ready.emit(preview_path)
        except Exception as e:
            self.error_message = str(e)
            self.preview_ready.emit('')


class ThumbnailGUI(QMainWindow):
    """메인 GUI 클래스"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('썸네일 생성기')
        self.setGeometry(100, 100, 1200, 800)
        
        # 메인 위젯
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout(main_widget)
        
        # 왼쪽: 미리보기
        preview_widget = self.create_preview_widget()
        main_layout.addWidget(preview_widget, 2)
        
        # 오른쪽: 설정 패널
        settings_widget = self.create_settings_widget()
        main_layout.addWidget(settings_widget, 1)
        
        # 기본값 초기화
        self.init_default_values()
    
    def create_preview_widget(self):
        """미리보기 위젯 생성"""
        group = QGroupBox('미리보기')
        layout = QVBoxLayout()
        
        self.preview_label = QLabel('미리보기가 여기에 표시됩니다')
        self.preview_label.setMinimumSize(480, 270)
        self.preview_label.setStyleSheet('border: 2px solid gray; background: white;')
        self.preview_label.setAlignment(Qt.AlignCenter)
        
        btn_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton('미리보기 생성')
        self.preview_btn.clicked.connect(self.generate_preview)
        
        self.save_btn = QPushButton('저장')
        self.save_btn.clicked.connect(self.save_thumbnail)

        self.show_dsl_btn = QPushButton('DSL 보기')
        self.show_dsl_btn.clicked.connect(self.show_dsl_dialog)

        self.save_dsl_btn = QPushButton('DSL 저장')
        self.save_dsl_btn.clicked.connect(self.save_dsl)

        self.save_thl_btn = QPushButton('패키지 저장(.thl)')
        self.save_thl_btn.clicked.connect(self.save_thl_package)
        
        btn_layout.addWidget(self.preview_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.show_dsl_btn)
        btn_layout.addWidget(self.save_dsl_btn)
        btn_layout.addWidget(self.save_thl_btn)
        
        layout.addWidget(self.preview_label)
        layout.addLayout(btn_layout)
        group.setLayout(layout)
        
        return group
    
    def create_settings_widget(self):
        """설정 위젯 생성"""
        scroll = QWidget()
        layout = QVBoxLayout()
        
        # 탭 위젯
        tabs = QTabWidget()
        
        # 해상도 탭
        res_tab = self.create_resolution_tab()
        tabs.addTab(res_tab, '해상도')
        
        # 배경 탭
        bg_tab = self.create_background_tab()
        tabs.addTab(bg_tab, '배경')
        
        # 제목 탭
        title_tab = self.create_title_tab()
        tabs.addTab(title_tab, '제목')
        
        # 부제목 탭
        subtitle_tab = self.create_subtitle_tab()
        tabs.addTab(subtitle_tab, '부제목')
        
        layout.addWidget(tabs)
        scroll.setLayout(layout)
        
        return scroll
    
    def create_resolution_tab(self):
        """해상도 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 모드 선택
        self.res_mode = QComboBox()
        self.res_mode.addItems(['preset', 'fixedRatio', 'custom'])
        self.res_mode.currentTextChanged.connect(self.on_resolution_mode_changed)
        
        layout.addWidget(QLabel('크기 모드:'))
        layout.addWidget(self.res_mode)
        
        # 비율 선택
        self.aspect_ratio = QComboBox()
        self.aspect_ratio.addItems(['16:9', '9:16', '4:3', '1:1'])
        self.aspect_ratio.currentTextChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('비율:'))
        layout.addWidget(self.aspect_ratio)
        
        # 너비/높이
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 2000)
        self.width_spin.setValue(480)
        self.width_spin.valueChanged.connect(self.update_preview)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 2000)
        self.height_spin.setValue(270)
        self.height_spin.valueChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('너비:'))
        layout.addWidget(self.width_spin)
        layout.addWidget(QLabel('높이:'))
        layout.addWidget(self.height_spin)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_background_tab(self):
        """배경 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 배경 타입
        유형 = QComboBox()
        유형.addItems(['solid', 'gradient', 'image'])
        유형.currentTextChanged.connect(self.update_preview)
        self.bg_type = 유형
        
        layout.addWidget(QLabel('배경 타입:'))
        layout.addWidget(유형)
        
        # 배경 색상
        self.bg_color_btn = QPushButton('색상 선택')
        self.bg_color_btn.clicked.connect(self.select_bg_color)
        self.bg_color = '#a3e635'
        
        layout.addWidget(QLabel('배경 색상:'))
        layout.addWidget(self.bg_color_btn)
        
        # 배경 이미지 경로
        self.bg_image_path = QLineEdit()
        self.bg_image_path.setPlaceholderText('이미지 파일 경로')
        
        bg_img_btn = QPushButton('이미지 선택')
        bg_img_btn.clicked.connect(self.select_background_image)
        
        layout.addWidget(QLabel('배경 이미지:'))
        layout.addWidget(self.bg_image_path)
        layout.addWidget(bg_img_btn)
        
        # 이미지 투명도
        self.bg_opacity = QSlider(Qt.Horizontal)
        self.bg_opacity.setRange(0, 100)
        self.bg_opacity.setValue(100)
        self.bg_opacity.valueChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('이미지 투명도:'))
        layout.addWidget(self.bg_opacity)
        
        # 이미지 블러
        self.bg_blur = QSlider(Qt.Horizontal)
        self.bg_blur.setRange(0, 20)
        self.bg_blur.setValue(0)
        self.bg_blur.valueChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('이미지 블러:'))
        layout.addWidget(self.bg_blur)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_title_tab(self):
        """제목 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 제목 텍스트
        self.title_text = QTextEdit()
        self.title_text.setPlaceholderText('제목 텍스트 입력 (여러 줄 가능)')
        self.title_text.textChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('제목 텍스트:'))
        layout.addWidget(self.title_text)
        
        # 폰트 설정 모드 (웹/로컬)
        self.title_font_source = QComboBox()
        self.title_font_source.addItems(['웹 폰트 URL', '로컬 폰트 파일'])
        self.title_font_source.currentTextChanged.connect(self.update_preview)

        layout.addWidget(QLabel('폰트 소스:'))
        layout.addWidget(self.title_font_source)

        # 폰트 설정 (이름/URL/굵기/스타일)
        self.title_font_name = QLineEdit()
        self.title_font_name.setPlaceholderText('예: SBAggroB')
        self.title_font_name.textChanged.connect(self.update_preview)

        self.title_font_url = QLineEdit()
        self.title_font_url.setPlaceholderText('예: https://.../SBAggroB.woff')
        self.title_font_url.textChanged.connect(self.update_preview)

        # 로컬 파일 경로 + 선택 버튼
        row_title_local = QHBoxLayout()
        self.title_font_file = QLineEdit()
        self.title_font_file.setPlaceholderText('예: C:/Windows/Fonts/malgun.ttf')
        self.title_font_file.textChanged.connect(self.on_title_font_file_changed)
        btn_title_font_browse = QPushButton('찾기')
        def _pick_title_font():
            path, _ = QFileDialog.getOpenFileName(self, '폰트 파일 선택', '', 'Fonts (*.ttf *.otf *.woff *.woff2)')
            if path:
                self.title_font_file.setText(path)
                # 파일 선택 시에는 이름을 강제로 세팅
                self.set_title_font_name_from_path(path)
        btn_title_font_browse.clicked.connect(_pick_title_font)
        row_title_local.addWidget(self.title_font_file)
        row_title_local.addWidget(btn_title_font_browse)

        self.title_font_weight = QComboBox()
        self.title_font_weight.addItems(['normal', 'bold'])
        self.title_font_weight.currentTextChanged.connect(self.update_preview)

        self.title_font_style = QComboBox()
        self.title_font_style.addItems(['normal', 'italic'])
        self.title_font_style.currentTextChanged.connect(self.update_preview)

        layout.addWidget(QLabel('폰트 이름:'))
        layout.addWidget(self.title_font_name)
        # URL/로컬 입력 영역
        self.label_title_font_url = QLabel('폰트 URL (WOFF/WOFF2/TTF):')
        layout.addWidget(self.label_title_font_url)
        layout.addWidget(self.title_font_url)
        self.label_title_font_file = QLabel('로컬 폰트 파일 경로:')
        layout.addWidget(self.label_title_font_file)
        layout.addLayout(row_title_local)
        layout.addWidget(QLabel('폰트 굵기/스타일:'))
        row_font = QHBoxLayout()
        row_font.addWidget(self.title_font_weight)
        row_font.addWidget(self.title_font_style)
        layout.addLayout(row_font)

        # 제목 색상
        self.title_color_btn = QPushButton('색상 선택')
        self.title_color_btn.clicked.connect(self.select_title_color)
        self.title_color = '#4ade80'
        
        layout.addWidget(QLabel('제목 색상:'))
        layout.addWidget(self.title_color_btn)
        
        # 폰트 크기
        self.title_font_size = QSpinBox()
        self.title_font_size.setRange(8, 200)
        self.title_font_size.setValue(48)
        self.title_font_size.valueChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('폰트 크기:'))
        layout.addWidget(self.title_font_size)
        
        # 외곽선
        self.title_outline_check = QCheckBox('외곽선 사용')
        self.title_outline_check.stateChanged.connect(self.update_preview)
        
        self.title_outline_thickness = QSpinBox()
        self.title_outline_thickness.setRange(1, 20)
        self.title_outline_thickness.setValue(7)
        self.title_outline_thickness.valueChanged.connect(self.update_preview)
        
        layout.addWidget(self.title_outline_check)
        layout.addWidget(QLabel('외곽선 두께:'))
        layout.addWidget(self.title_outline_thickness)
        
        # 위치 (9 그리드)
        self.title_position = QComboBox()
        self.title_position.addItems(['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br'])
        self.title_position.currentTextChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('위치:'))
        layout.addWidget(self.title_position)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_subtitle_tab(self):
        """부제목 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 부제목 표시 여부
        self.subtitle_visible = QCheckBox('부제목 표시')
        self.subtitle_visible.setChecked(True)
        self.subtitle_visible.stateChanged.connect(self.update_preview)
        
        layout.addWidget(self.subtitle_visible)
        
        # 부제목 텍스트
        self.subtitle_text = QTextEdit()
        self.subtitle_text.setPlaceholderText('부제목 텍스트 입력 (여러 줄 가능)')
        self.subtitle_text.textChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('부제목 텍스트:'))
        layout.addWidget(self.subtitle_text)
        
        # 폰트 설정 모드 (웹/로컬)
        self.subtitle_font_source = QComboBox()
        self.subtitle_font_source.addItems(['웹 폰트 URL', '로컬 폰트 파일'])
        self.subtitle_font_source.currentTextChanged.connect(self.update_preview)

        layout.addWidget(QLabel('폰트 소스:'))
        layout.addWidget(self.subtitle_font_source)

        # 폰트 설정 (이름/URL/굵기/스타일)
        self.subtitle_font_name = QLineEdit()
        self.subtitle_font_name.setPlaceholderText('예: SBAggroB')
        self.subtitle_font_name.textChanged.connect(self.update_preview)

        self.subtitle_font_url = QLineEdit()
        self.subtitle_font_url.setPlaceholderText('예: https://.../SBAggroB.woff')
        self.subtitle_font_url.textChanged.connect(self.update_preview)

        # 로컬 파일 경로 + 선택 버튼
        row_sub_local = QHBoxLayout()
        self.subtitle_font_file = QLineEdit()
        self.subtitle_font_file.setPlaceholderText('예: C:/Windows/Fonts/malgun.ttf')
        self.subtitle_font_file.textChanged.connect(self.on_subtitle_font_file_changed)
        btn_sub_font_browse = QPushButton('찾기')
        def _pick_sub_font():
            path, _ = QFileDialog.getOpenFileName(self, '폰트 파일 선택', '', 'Fonts (*.ttf *.otf *.woff *.woff2)')
            if path:
                self.subtitle_font_file.setText(path)
                # 파일 선택 시에는 이름을 강제로 세팅
                self.set_subtitle_font_name_from_path(path)
        btn_sub_font_browse.clicked.connect(_pick_sub_font)
        row_sub_local.addWidget(self.subtitle_font_file)
        row_sub_local.addWidget(btn_sub_font_browse)

        self.subtitle_font_weight = QComboBox()
        self.subtitle_font_weight.addItems(['normal', 'bold'])
        self.subtitle_font_weight.currentTextChanged.connect(self.update_preview)

        self.subtitle_font_style = QComboBox()
        self.subtitle_font_style.addItems(['normal', 'italic'])
        self.subtitle_font_style.currentTextChanged.connect(self.update_preview)

        layout.addWidget(QLabel('폰트 이름:'))
        layout.addWidget(self.subtitle_font_name)
        self.label_subtitle_font_url = QLabel('폰트 URL (WOFF/WOFF2/TTF):')
        layout.addWidget(self.label_subtitle_font_url)
        layout.addWidget(self.subtitle_font_url)
        self.label_subtitle_font_file = QLabel('로컬 폰트 파일 경로:')
        layout.addWidget(self.label_subtitle_font_file)
        layout.addLayout(row_sub_local)
        layout.addWidget(QLabel('폰트 굵기/스타일:'))
        row_sub_font = QHBoxLayout()
        row_sub_font.addWidget(self.subtitle_font_weight)
        row_sub_font.addWidget(self.subtitle_font_style)
        layout.addLayout(row_sub_font)
        
        # 부제목 색상
        self.subtitle_color_btn = QPushButton('색상 선택')
        self.subtitle_color_btn.clicked.connect(self.select_subtitle_color)
        self.subtitle_color = '#ffffff'
        
        layout.addWidget(QLabel('부제목 색상:'))
        layout.addWidget(self.subtitle_color_btn)
        
        # 폰트 크기
        self.subtitle_font_size = QSpinBox()
        self.subtitle_font_size.setRange(8, 200)
        self.subtitle_font_size.setValue(24)
        self.subtitle_font_size.valueChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('폰트 크기:'))
        layout.addWidget(self.subtitle_font_size)
        
        # 위치 (9 그리드)
        self.subtitle_position = QComboBox()
        self.subtitle_position.addItems(['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br'])
        self.subtitle_position.setCurrentText('bl')
        self.subtitle_position.currentTextChanged.connect(self.update_preview)
        
        layout.addWidget(QLabel('위치:'))
        layout.addWidget(self.subtitle_position)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def init_default_values(self):
        """기본값 초기화"""
        self.title_text.setPlainText('10초만에\n썸네일 만드는 법')
        self.subtitle_text.setPlainText('쉽고 빠르게 썸네일을 만드는 법\n= 퀵썸네일 쓰기')
        # 기본 폰트 값 (노느늘 SBAggroB)
        self.title_font_name.setText('SBAggroB')
        self.title_font_url.setText('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff')
        self.title_font_weight.setCurrentText('bold')
        self.title_font_style.setCurrentText('normal')

        self.subtitle_font_name.setText('SBAggroB')
        self.subtitle_font_url.setText('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff')
        self.subtitle_font_weight.setCurrentText('normal')
        self.subtitle_font_style.setCurrentText('normal')
        self.update_preview()
    
    def on_resolution_mode_changed(self, mode):
        """해상도 모드 변경 시 처리"""
        if mode == 'preset':
            self.aspect_ratio.setEnabled(True)
        elif mode == 'fixedRatio':
            self.aspect_ratio.setEnabled(True)
        else:  # custom
            self.aspect_ratio.setEnabled(False)
        self.update_preview()
    
    def select_bg_color(self):
        """배경 색상 선택"""
        color = QColorDialog.getColor(QColor(self.bg_color))
        if color.isValid():
            self.bg_color = color.name()
            self.update_preview()
    
    def select_title_color(self):
        """제목 색상 선택"""
        color = QColorDialog.getColor(QColor(self.title_color))
        if color.isValid():
            self.title_color = color.name()
            self.update_preview()
    
    def select_subtitle_color(self):
        """부제목 색상 선택"""
        color = QColorDialog.getColor(QColor(self.subtitle_color))
        if color.isValid():
            self.subtitle_color = color.name()
            self.update_preview()
    
    def select_background_image(self):
        """배경 이미지 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '배경 이미지 선택', '', 'Images (*.png *.jpg *.jpeg *.gif *.bmp)'
        )
        if file_path:
            self.bg_image_path.setText(file_path)
            self.update_preview()
    
    def generate_dsl(self):
        """DSL 생성"""
        # 해상도 결정
        res_mode = self.res_mode.currentText()
        if res_mode == 'preset':
            resolution = {
                'type': 'preset',
                'value': self.aspect_ratio.currentText()
            }
        elif res_mode == 'fixedRatio':
            resolution = {
                'type': 'fixedRatio',
                'ratioValue': self.aspect_ratio.currentText(),
                'width': self.width_spin.value()
            }
        else:  # custom
            resolution = {
                'type': 'custom',
                'width': self.width_spin.value(),
                'height': self.height_spin.value()
            }
        
        # 배경 결정
        bg_type = self.bg_type.currentText()
        if bg_type == 'image' and self.bg_image_path.text():
            # 이미지를 base64로 변환
            with open(self.bg_image_path.text(), 'rb') as f:
                image_data = f.read()
                base64_str = base64.b64encode(image_data).decode('utf-8')
                data_url = f"data:image/png;base64,{base64_str}"
                
            background = {
                'type': 'image',
                'imagePath': data_url,
                'imageOpacity': self.bg_opacity.value() / 100.0,
                'imageBlur': self.bg_blur.value()
            }
        elif bg_type == 'gradient':
            background = {
                'type': 'gradient',
                'colors': [self.bg_color, '#000000']
            }
        else:  # solid
            background = {
                'type': 'solid',
                'color': self.bg_color
            }
        
        # 텍스트 설정
        # 제목 폰트 소스 분기
        title_use_local = self.title_font_source.currentText() == '로컬 폰트 파일'
        title_face_url = self.title_font_file.text() if title_use_local and self.title_font_file.text() else (self.title_font_url.text() or 'https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff')
        # 부제목 폰트 소스 분기
        subtitle_use_local = self.subtitle_font_source.currentText() == '로컬 폰트 파일'
        subtitle_face_url = self.subtitle_font_file.text() if subtitle_use_local and self.subtitle_font_file.text() else (self.subtitle_font_url.text() or 'https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff')

        texts = [
            {
                'type': 'title',
                'content': self.title_text.toPlainText(),
                'gridPosition': self.title_position.currentText(),
                'font': {
                    'name': self.title_font_name.text() or 'SBAggroB',
                    'faces': [{
                        'name': self.title_font_name.text() or 'SBAggroB',
                        'url': title_face_url,
                        'weight': self.title_font_weight.currentText() or 'bold',
                        'style': self.title_font_style.currentText() or 'normal'
                    }]
                },
                'fontSize': self.title_font_size.value(),
                'color': self.title_color,
                'fontWeight': self.title_font_weight.currentText() or 'bold',
                'fontStyle': self.title_font_style.currentText() or 'normal',
                'lineHeight': 1.1,
                'wordWrap': False,
                'outline': {
                    'thickness': self.title_outline_thickness.value(),
                    'color': '#000000'
                } if self.title_outline_check.isChecked() else None,
                'enabled': True
            }
        ]
        
        # 부제목 추가
        if self.subtitle_visible.isChecked():
            texts.append({
                'type': 'subtitle',
                'content': self.subtitle_text.toPlainText(),
                'gridPosition': self.subtitle_position.currentText(),
                'font': {
                    'name': self.subtitle_font_name.text() or 'SBAggroB',
                    'faces': [{
                        'name': self.subtitle_font_name.text() or 'SBAggroB',
                        'url': subtitle_face_url,
                        'weight': self.subtitle_font_weight.currentText() or 'normal',
                        'style': self.subtitle_font_style.currentText() or 'normal'
                    }]
                },
                'fontSize': self.subtitle_font_size.value(),
                'color': self.subtitle_color,
                'fontWeight': self.subtitle_font_weight.currentText() or 'normal',
                'fontStyle': self.subtitle_font_style.currentText() or 'normal',
                'lineHeight': 1.1,
                'wordWrap': False,
                'outline': None,
                'enabled': True
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
    
    def update_preview(self):
        """미리보기 업데이트"""
        # URL/로컬 입력 영역 가시성 토글
        is_title_local = self.title_font_source.currentText() == '로컬 폰트 파일'
        self.label_title_font_url.setVisible(not is_title_local)
        self.title_font_url.setVisible(not is_title_local)
        self.label_title_font_file.setVisible(is_title_local)
        self.title_font_file.setVisible(is_title_local)
        # 파일 찾기 버튼은 레이아웃에 포함되어 있어 개별 위젯 접근 불가하므로 입력창 표시로 충분

        is_sub_local = self.subtitle_font_source.currentText() == '로컬 폰트 파일'
        self.label_subtitle_font_url.setVisible(not is_sub_local)
        self.subtitle_font_url.setVisible(not is_sub_local)
        self.label_subtitle_font_file.setVisible(is_sub_local)
        self.subtitle_font_file.setVisible(is_sub_local)

        dsl = self.generate_dsl()
        self.current_dsl = dsl

    # ---------- 폰트 이름 자동 추출 ----------
    @staticmethod
    def _infer_font_name_from_file(file_path: str) -> str:
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if TTFont and ext in ('.ttf', '.otf') and os.path.exists(file_path):
                tt = TTFont(file_path)
                # Prefer full font name (nameID=4), fallback to font family (nameID=1)
                name = None
                for rec in tt['name'].names:
                    if rec.nameID in (4, 1):
                        try:
                            val = rec.toUnicode()
                        except Exception:
                            val = rec.string.decode(rec.getEncoding(), errors='ignore')
                        if val:
                            name = val
                            if rec.nameID == 4:
                                break
                if name:
                    return name
        except Exception:
            pass
        # Fallback: 파일명(확장자 제외)
        return os.path.splitext(os.path.basename(file_path))[0]

    def set_title_font_name_from_path(self, path: str) -> None:
        inferred = self._infer_font_name_from_file(path)
        if inferred:
            self.title_font_name.setText(inferred)
        self.update_preview()

    def set_subtitle_font_name_from_path(self, path: str) -> None:
        inferred = self._infer_font_name_from_file(path)
        if inferred:
            self.subtitle_font_name.setText(inferred)
        self.update_preview()

    def on_title_font_file_changed(self):
        # 경로를 직접 입력한 경우: 이름 칸이 비어 있을 때만 채움
        path = self.title_font_file.text().strip()
        if path and not self.title_font_name.text().strip():
            self.set_title_font_name_from_path(path)
        else:
            self.update_preview()

    def on_subtitle_font_file_changed(self):
        # 경로를 직접 입력한 경우: 이름 칸이 비어 있을 때만 채움
        path = self.subtitle_font_file.text().strip()
        if path and not self.subtitle_font_name.text().strip():
            self.set_subtitle_font_name_from_path(path)
        else:
            self.update_preview()
    
    def generate_preview(self):
        """미리보기 생성"""
        if not hasattr(self, 'current_dsl'):
            self.update_preview()
        
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText('생성 중...')
        
        # 스레드에서 생성
        self.preview_thread = PreviewThread(self.current_dsl)
        self.preview_thread.preview_ready.connect(self.on_preview_ready)
        self.preview_thread.start()
    
    def on_preview_ready(self, file_path):
        """미리보기 준비됨"""
        from PySide6.QtGui import QPixmap
        if file_path and os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            self.preview_label.setPixmap(pixmap.scaled(
                480, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            msg = self.preview_thread.error_message or '미리보기 생성 중 오류가 발생했습니다.'
            QMessageBox.critical(self, '에러', msg)
        
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText('미리보기 생성')
    
    def save_thumbnail(self):
        """썸네일 저장"""
        if not hasattr(self, 'current_dsl'):
            QMessageBox.warning(self, '경고', '먼저 미리보기를 생성해주세요.')
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, '썸네일 저장', 'thumbnail.png', 'Images (*.png)'
        )
        
        if file_path:
            try:
                ThumbnailRenderer.render_thumbnail(self.current_dsl, file_path)
                QMessageBox.information(self, '완료', f'저장 완료: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '에러', f'저장 실패: {e}')

    def show_dsl_dialog(self):
        """현재 DSL을 JSON으로 출력하는 다이얼로그"""
        if not hasattr(self, 'current_dsl'):
            self.update_preview()
        dsl = getattr(self, 'current_dsl', self.generate_dsl())
        try:
            text = json.dumps(dsl, ensure_ascii=False, indent=2)
        except Exception:
            text = str(dsl)

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle('현재 DSL 보기')
        v = QVBoxLayout(dlg)
        editor = QPlainTextEdit()
        editor.setPlainText(text)
        editor.setReadOnly(True)
        v.addWidget(editor)
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(dlg.reject)
        btns.accepted.connect(dlg.accept)
        v.addWidget(btns)
        dlg.resize(700, 500)
        dlg.exec()

    def save_dsl(self):
        """현재 DSL을 JSON 파일로 저장"""
        if not hasattr(self, 'current_dsl'):
            self.update_preview()
        dsl = getattr(self, 'current_dsl', self.generate_dsl())

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'DSL 저장', 'thumbnail.json', 'JSON (*.json)'
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dsl, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, '완료', f'DSL 저장 완료: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, '에러', f'DSL 저장 실패: {e}')

    def save_thl_package(self):
        """현재 DSL과 사용 폰트를 묶어 .thl 패키지로 저장"""
        if not hasattr(self, 'current_dsl'):
            self.update_preview()
        dsl = getattr(self, 'current_dsl', self.generate_dsl())

        # 저장 경로 선택
        file_path, _ = QFileDialog.getSaveFileName(
            self, '패키지 저장', 'thumbnail.thl', 'Thumbnail Package (*.thl)'
        )
        if not file_path:
            return
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
            copied = 0
            for face in faces:
                ttf_name = f"{sanitize(face.get('name','Font'))}-{sanitize(str(face.get('weight','normal')))}-{sanitize(str(face.get('style','normal')))}.ttf"
                src_path = os.path.join(ThumbnailRenderer._fonts_dir(), ttf_name)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, os.path.join(fonts_dir, ttf_name))
                    copied += 1

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

            QMessageBox.information(self, '완료', f'패키지 저장 완료: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, '에러', f'패키지 저장 실패: {e}')
        finally:
            try:
                shutil.rmtree(staging, ignore_errors=True)
            except Exception:
                pass


def main():
    app = QApplication(sys.argv)
    window = ThumbnailGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

