#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 위젯 생성 모듈
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QSpinBox, QTextEdit, QCheckBox, 
                               QComboBox, QGroupBox, QLineEdit, QSlider, QFileDialog)
from PySide6.QtCore import Qt


class WidgetFactory:
    """위젯 생성 팩토리 클래스"""
    
    @staticmethod
    def create_preview_widget(parent):
        """미리보기 위젯 생성"""
        group = QGroupBox('미리보기')
        layout = QVBoxLayout()
        
        parent.preview_label = QLabel('미리보기가 여기에 표시됩니다')
        parent.preview_label.setMinimumSize(480, 270)
        parent.preview_label.setStyleSheet('border: 2px solid gray; background: white;')
        parent.preview_label.setAlignment(Qt.AlignCenter)
        
        btn_layout = QHBoxLayout()
        
        parent.preview_btn = QPushButton('미리보기 생성')
        parent.preview_btn.clicked.connect(parent.generate_preview)
        
        parent.save_btn = QPushButton('저장')
        parent.save_btn.clicked.connect(parent.save_thumbnail)

        parent.show_dsl_btn = QPushButton('DSL 보기')
        parent.show_dsl_btn.clicked.connect(parent.show_dsl_dialog)

        parent.save_dsl_btn = QPushButton('DSL 저장')
        parent.save_dsl_btn.clicked.connect(parent.save_dsl)

        parent.save_thl_btn = QPushButton('패키지 저장(.thl)')
        parent.save_thl_btn.clicked.connect(parent.save_thl_package)
        
        parent.load_thl_btn = QPushButton('패키지 로드(.thl)')
        parent.load_thl_btn.clicked.connect(parent.load_thl_package)
        
        btn_layout.addWidget(parent.preview_btn)
        btn_layout.addWidget(parent.save_btn)
        btn_layout.addWidget(parent.show_dsl_btn)
        btn_layout.addWidget(parent.save_dsl_btn)
        btn_layout.addWidget(parent.load_thl_btn)
        btn_layout.addWidget(parent.save_thl_btn)
        
        layout.addWidget(parent.preview_label)
        layout.addLayout(btn_layout)
        group.setLayout(layout)
        
        return group
    
    @staticmethod
    def create_resolution_tab(parent):
        """해상도 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 모드 선택
        parent.res_mode = QComboBox()
        parent.res_mode.addItems(['preset', 'fixedRatio', 'custom'])
        parent.res_mode.currentTextChanged.connect(parent.on_resolution_mode_changed)
        
        layout.addWidget(QLabel('크기 모드:'))
        layout.addWidget(parent.res_mode)
        
        # 비율 선택
        parent.aspect_ratio = QComboBox()
        parent.aspect_ratio.addItems(['16:9', '9:16', '4:3', '1:1'])
        parent.aspect_ratio.currentTextChanged.connect(parent.on_aspect_ratio_changed)
        
        layout.addWidget(QLabel('비율:'))
        layout.addWidget(parent.aspect_ratio)
        
        # 너비/높이
        parent.width_spin = QSpinBox()
        parent.width_spin.setRange(100, 2000)
        parent.width_spin.setValue(480)
        parent.width_spin.valueChanged.connect(parent.on_width_changed)
        
        parent.height_spin = QSpinBox()
        parent.height_spin.setRange(100, 2000)
        parent.height_spin.setValue(270)
        parent.height_spin.valueChanged.connect(parent.on_height_changed)
        
        # fixedRatio 모드에서 무한 루프 방지를 위한 플래그
        parent._updating_dimension = False
        
        layout.addWidget(QLabel('너비:'))
        layout.addWidget(parent.width_spin)
        layout.addWidget(QLabel('높이:'))
        layout.addWidget(parent.height_spin)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    @staticmethod
    def create_background_tab(parent):
        """배경 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 배경 타입
        bg_type = QComboBox()
        bg_type.addItems(['solid', 'gradient', 'image'])
        bg_type.currentTextChanged.connect(parent.update_preview)
        parent.bg_type = bg_type
        
        layout.addWidget(QLabel('배경 타입:'))
        layout.addWidget(bg_type)
        
        # 배경 색상
        parent.bg_color_btn = QPushButton('색상 선택')
        parent.bg_color_btn.clicked.connect(parent.select_bg_color)
        parent.bg_color = '#a3e635'
        
        layout.addWidget(QLabel('배경 색상:'))
        layout.addWidget(parent.bg_color_btn)
        
        # 배경 이미지 경로
        parent.bg_image_path = QLineEdit()
        parent.bg_image_path.setPlaceholderText('이미지 파일 경로')
        
        bg_img_btn = QPushButton('이미지 선택')
        bg_img_btn.clicked.connect(parent.select_background_image)
        
        layout.addWidget(QLabel('배경 이미지:'))
        layout.addWidget(parent.bg_image_path)
        layout.addWidget(bg_img_btn)
        
        # 이미지 투명도
        parent.bg_opacity = QSlider(Qt.Horizontal)
        parent.bg_opacity.setRange(0, 100)
        parent.bg_opacity.setValue(100)
        parent.bg_opacity.valueChanged.connect(parent.update_preview)
        
        layout.addWidget(QLabel('이미지 투명도:'))
        layout.addWidget(parent.bg_opacity)
        
        # 이미지 블러
        parent.bg_blur = QSlider(Qt.Horizontal)
        parent.bg_blur.setRange(0, 20)
        parent.bg_blur.setValue(0)
        parent.bg_blur.valueChanged.connect(parent.update_preview)
        
        layout.addWidget(QLabel('이미지 블러:'))
        layout.addWidget(parent.bg_blur)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    @staticmethod
    def create_title_tab(parent):
        """제목 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 제목 텍스트
        parent.title_text = QTextEdit()
        parent.title_text.setPlaceholderText('제목 텍스트 입력 (여러 줄 가능)')
        parent.title_text.textChanged.connect(parent.update_preview)
        
        layout.addWidget(QLabel('제목 텍스트:'))
        layout.addWidget(parent.title_text)
        
        # 폰트 설정 모드 (웹/로컬)
        parent.title_font_source = QComboBox()
        parent.title_font_source.addItems(['웹 폰트 URL', '로컬 폰트 파일'])
        parent.title_font_source.currentTextChanged.connect(parent.update_preview)

        layout.addWidget(QLabel('폰트 소스:'))
        layout.addWidget(parent.title_font_source)

        # 폰트 설정 (이름/URL/굵기/스타일)
        parent.title_font_name = QLineEdit()
        parent.title_font_name.setPlaceholderText('예: SBAggroB')
        parent.title_font_name.textChanged.connect(parent.update_preview)

        parent.title_font_url = QLineEdit()
        parent.title_font_url.setPlaceholderText('예: https://.../SBAggroB.woff')
        parent.title_font_url.textChanged.connect(parent.update_preview)

        # 로컬 파일 경로 + 선택 버튼
        row_title_local = QHBoxLayout()
        parent.title_font_file = QLineEdit()
        parent.title_font_file.setPlaceholderText('예: C:/Windows/Fonts/malgun.ttf')
        parent.title_font_file.textChanged.connect(parent.on_title_font_file_changed)
        btn_title_font_browse = QPushButton('찾기')
        def _pick_title_font():
            path, _ = QFileDialog.getOpenFileName(parent, '폰트 파일 선택', '', 'Fonts (*.ttf *.otf *.woff *.woff2)')
            if path:
                parent.title_font_file.setText(path)
                parent.set_title_font_name_from_path(path)
        btn_title_font_browse.clicked.connect(_pick_title_font)
        row_title_local.addWidget(parent.title_font_file)
        row_title_local.addWidget(btn_title_font_browse)

        parent.title_font_weight = QComboBox()
        parent.title_font_weight.addItems(['normal', 'bold'])
        parent.title_font_weight.currentTextChanged.connect(parent.update_preview)

        parent.title_font_style = QComboBox()
        parent.title_font_style.addItems(['normal', 'italic'])
        parent.title_font_style.currentTextChanged.connect(parent.update_preview)

        layout.addWidget(QLabel('폰트 이름:'))
        layout.addWidget(parent.title_font_name)
        # URL/로컬 입력 영역
        parent.label_title_font_url = QLabel('폰트 URL (WOFF/WOFF2/TTF):')
        layout.addWidget(parent.label_title_font_url)
        layout.addWidget(parent.title_font_url)
        parent.label_title_font_file = QLabel('로컬 폰트 파일 경로:')
        layout.addWidget(parent.label_title_font_file)
        layout.addLayout(row_title_local)
        layout.addWidget(QLabel('폰트 굵기/스타일:'))
        row_font = QHBoxLayout()
        row_font.addWidget(parent.title_font_weight)
        row_font.addWidget(parent.title_font_style)
        layout.addLayout(row_font)

        # 제목 색상
        parent.title_color_btn = QPushButton('색상 선택')
        parent.title_color_btn.clicked.connect(parent.select_title_color)
        parent.title_color = '#4ade80'
        
        layout.addWidget(QLabel('제목 색상:'))
        layout.addWidget(parent.title_color_btn)
        
        # 폰트 크기
        parent.title_font_size = QSpinBox()
        parent.title_font_size.setRange(8, 200)
        parent.title_font_size.setValue(48)
        parent.title_font_size.valueChanged.connect(parent.update_preview)
        
        layout.addWidget(QLabel('폰트 크기:'))
        layout.addWidget(parent.title_font_size)
        
        # 외곽선
        parent.title_outline_check = QCheckBox('외곽선 사용')
        parent.title_outline_check.stateChanged.connect(parent.update_preview)
        
        parent.title_outline_thickness = QSpinBox()
        parent.title_outline_thickness.setRange(1, 20)
        parent.title_outline_thickness.setValue(7)
        parent.title_outline_thickness.valueChanged.connect(parent.update_preview)
        
        layout.addWidget(parent.title_outline_check)
        layout.addWidget(QLabel('외곽선 두께:'))
        layout.addWidget(parent.title_outline_thickness)

        # 워드 랩
        parent.title_word_wrap = QCheckBox('단어 단위 줄바꿈')
        parent.title_word_wrap.stateChanged.connect(parent.update_preview)
        layout.addWidget(parent.title_word_wrap)
        
        # 위치 (9 그리드)
        parent.title_position = QComboBox()
        parent.title_position.addItems(['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br'])
        parent.title_position.currentTextChanged.connect(parent.update_preview)
        
        layout.addWidget(QLabel('위치:'))
        layout.addWidget(parent.title_position)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    @staticmethod
    def create_subtitle_tab(parent):
        """부제목 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 부제목 표시 여부
        parent.subtitle_visible = QCheckBox('부제목 표시')
        parent.subtitle_visible.setChecked(True)
        parent.subtitle_visible.stateChanged.connect(parent.update_preview)
        
        layout.addWidget(parent.subtitle_visible)
        
        # 부제목 텍스트
        parent.subtitle_text = QTextEdit()
        parent.subtitle_text.setPlaceholderText('부제목 텍스트 입력 (여러 줄 가능)')
        parent.subtitle_text.textChanged.connect(parent.update_preview)
        
        layout.addWidget(QLabel('부제목 텍스트:'))
        layout.addWidget(parent.subtitle_text)
        
        # 폰트 설정 모드 (웹/로컬)
        parent.subtitle_font_source = QComboBox()
        parent.subtitle_font_source.addItems(['웹 폰트 URL', '로컬 폰트 파일'])
        parent.subtitle_font_source.currentTextChanged.connect(parent.update_preview)

        layout.addWidget(QLabel('폰트 소스:'))
        layout.addWidget(parent.subtitle_font_source)

        # 폰트 설정 (이름/URL/굵기/스타일)
        parent.subtitle_font_name = QLineEdit()
        parent.subtitle_font_name.setPlaceholderText('예: SBAggroB')
        parent.subtitle_font_name.textChanged.connect(parent.update_preview)

        parent.subtitle_font_url = QLineEdit()
        parent.subtitle_font_url.setPlaceholderText('예: https://.../SBAggroB.woff')
        parent.subtitle_font_url.textChanged.connect(parent.update_preview)

        # 로컬 파일 경로 + 선택 버튼
        row_sub_local = QHBoxLayout()
        parent.subtitle_font_file = QLineEdit()
        parent.subtitle_font_file.setPlaceholderText('예: C:/Windows/Fonts/malgun.ttf')
        parent.subtitle_font_file.textChanged.connect(parent.on_subtitle_font_file_changed)
        btn_sub_font_browse = QPushButton('찾기')
        def _pick_sub_font():
            path, _ = QFileDialog.getOpenFileName(parent, '폰트 파일 선택', '', 'Fonts (*.ttf *.otf *.woff *.woff2)')
            if path:
                parent.subtitle_font_file.setText(path)
                parent.set_subtitle_font_name_from_path(path)
        btn_sub_font_browse.clicked.connect(_pick_sub_font)
        row_sub_local.addWidget(parent.subtitle_font_file)
        row_sub_local.addWidget(btn_sub_font_browse)

        parent.subtitle_font_weight = QComboBox()
        parent.subtitle_font_weight.addItems(['normal', 'bold'])
        parent.subtitle_font_weight.currentTextChanged.connect(parent.update_preview)

        parent.subtitle_font_style = QComboBox()
        parent.subtitle_font_style.addItems(['normal', 'italic'])
        parent.subtitle_font_style.currentTextChanged.connect(parent.update_preview)

        layout.addWidget(QLabel('폰트 이름:'))
        layout.addWidget(parent.subtitle_font_name)
        parent.label_subtitle_font_url = QLabel('폰트 URL (WOFF/WOFF2/TTF):')
        layout.addWidget(parent.label_subtitle_font_url)
        layout.addWidget(parent.subtitle_font_url)
        parent.label_subtitle_font_file = QLabel('로컬 폰트 파일 경로:')
        layout.addWidget(parent.label_subtitle_font_file)
        layout.addLayout(row_sub_local)
        layout.addWidget(QLabel('폰트 굵기/스타일:'))
        row_sub_font = QHBoxLayout()
        row_sub_font.addWidget(parent.subtitle_font_weight)
        row_sub_font.addWidget(parent.subtitle_font_style)
        layout.addLayout(row_sub_font)
        
        # 부제목 색상
        parent.subtitle_color_btn = QPushButton('색상 선택')
        parent.subtitle_color_btn.clicked.connect(parent.select_subtitle_color)
        parent.subtitle_color = '#ffffff'
        
        layout.addWidget(QLabel('부제목 색상:'))
        layout.addWidget(parent.subtitle_color_btn)
        
        # 폰트 크기
        parent.subtitle_font_size = QSpinBox()
        parent.subtitle_font_size.setRange(8, 200)
        parent.subtitle_font_size.setValue(24)
        parent.subtitle_font_size.valueChanged.connect(parent.update_preview)
        
        layout.addWidget(QLabel('폰트 크기:'))
        layout.addWidget(parent.subtitle_font_size)
        
        # 위치 (9 그리드)
        parent.subtitle_position = QComboBox()
        parent.subtitle_position.addItems(['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br'])
        parent.subtitle_position.setCurrentText('bl')
        parent.subtitle_position.currentTextChanged.connect(parent.update_preview)

        # 워드 랩
        parent.subtitle_word_wrap = QCheckBox('단어 단위 줄바꿈')
        parent.subtitle_word_wrap.stateChanged.connect(parent.update_preview)
        
        layout.addWidget(QLabel('위치:'))
        layout.addWidget(parent.subtitle_position)
        layout.addWidget(parent.subtitle_word_wrap)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

