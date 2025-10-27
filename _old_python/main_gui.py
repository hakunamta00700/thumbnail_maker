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
from thumbnailRenderer import ThumbnailRenderer


class PreviewThread(QThread):
    """미리보기 생성 스레드"""
    preview_ready = Signal(str)  # preview file path
    
    def __init__(self, dsl):
        super().__init__()
        self.dsl = dsl
    
    def run(self):
        preview_path = 'preview_temp.png'
        ThumbnailRenderer.render_thumbnail(self.dsl, preview_path)
        self.preview_ready.emit(preview_path)


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
        
        btn_layout.addWidget(self.preview_btn)
        btn_layout.addWidget(self.save_btn)
        
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
        texts = [
            {
                'type': 'title',
                'content': self.title_text.toPlainText(),
                'gridPosition': self.title_position.currentText(),
                'font': {
                    'name': 'SBAggroB',
                    'faces': [{
                        'name': 'SBAggroB',
                        'url': 'https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff',
                        'weight': 'normal',
                        'style': 'normal'
                    }]
                },
                'fontSize': self.title_font_size.value(),
                'color': self.title_color,
                'fontWeight': 'bold',
                'fontStyle': 'normal',
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
                    'name': 'SBAggroB',
                    'faces': [{
                        'name': 'SBAggroB',
                        'url': 'https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2108@1.1/SBAggroB.woff',
                        'weight': 'normal',
                        'style': 'normal'
                    }]
                },
                'fontSize': self.subtitle_font_size.value(),
                'color': self.subtitle_color,
                'fontWeight': 'normal',
                'fontStyle': 'normal',
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
        dsl = self.generate_dsl()
        self.current_dsl = dsl
    
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
        pixmap = QPixmap(file_path)
        self.preview_label.setPixmap(pixmap.scaled(
            480, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        
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
            ThumbnailRenderer.render_thumbnail(self.current_dsl, file_path)
            QMessageBox.information(self, '완료', f'저장 완료: {file_path}')


def main():
    app = QApplication(sys.argv)
    window = ThumbnailGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

