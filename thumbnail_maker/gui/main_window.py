#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메인 GUI 윈도우 클래스
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget

from .widgets import WidgetFactory
from .handlers import EventHandlers
from .dsl_manager import DSLManager


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
        preview_widget = WidgetFactory.create_preview_widget(self)
        main_layout.addWidget(preview_widget, 2)
        
        # 오른쪽: 설정 패널
        settings_widget = self.create_settings_widget()
        main_layout.addWidget(settings_widget, 1)
        
        # 기본값 초기화
        self.init_default_values()
    
    def create_settings_widget(self):
        """설정 위젯 생성"""
        scroll = QWidget()
        layout = QVBoxLayout()
        
        # 탭 위젯
        tabs = QTabWidget()
        
        # 해상도 탭
        res_tab = WidgetFactory.create_resolution_tab(self)
        tabs.addTab(res_tab, '해상도')
        
        # 배경 탭
        bg_tab = WidgetFactory.create_background_tab(self)
        tabs.addTab(bg_tab, '배경')
        
        # 제목 탭
        title_tab = WidgetFactory.create_title_tab(self)
        tabs.addTab(title_tab, '제목')
        
        # 부제목 탭
        subtitle_tab = WidgetFactory.create_subtitle_tab(self)
        tabs.addTab(subtitle_tab, '부제목')
        
        layout.addWidget(tabs)
        scroll.setLayout(layout)
        
        return scroll
    
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
    
    # 이벤트 핸들러 위임
    def on_resolution_mode_changed(self, mode):
        EventHandlers.on_resolution_mode_changed(self, mode)
    
    def on_width_changed(self, value):
        EventHandlers.on_width_changed(self, value)
    
    def on_height_changed(self, value):
        EventHandlers.on_height_changed(self, value)
    
    def on_aspect_ratio_changed(self, ratio):
        EventHandlers.on_aspect_ratio_changed(self, ratio)
    
    def select_bg_color(self):
        EventHandlers.select_bg_color(self)
    
    def select_title_color(self):
        EventHandlers.select_title_color(self)
    
    def select_subtitle_color(self):
        EventHandlers.select_subtitle_color(self)
    
    def select_background_image(self):
        EventHandlers.select_background_image(self)
    
    def set_title_font_name_from_path(self, path: str):
        EventHandlers.set_title_font_name_from_path(self, path)
    
    def set_subtitle_font_name_from_path(self, path: str):
        EventHandlers.set_subtitle_font_name_from_path(self, path)
    
    def on_title_font_file_changed(self):
        EventHandlers.on_title_font_file_changed(self)
    
    def on_subtitle_font_file_changed(self):
        EventHandlers.on_subtitle_font_file_changed(self)
    
    def generate_preview(self):
        EventHandlers.generate_preview(self)
    
    def save_thumbnail(self):
        EventHandlers.save_thumbnail(self)
    
    def show_dsl_dialog(self):
        EventHandlers.show_dsl_dialog(self)
    
    def save_dsl(self):
        EventHandlers.save_dsl(self)
    
    def load_thl_package(self):
        EventHandlers.load_thl_package(self)
    
    def save_thl_package(self):
        EventHandlers.save_thl_package(self)
    
    # DSL 관련 메서드
    def generate_dsl(self):
        return DSLManager.generate_dsl(self)
    
    def load_dsl_to_gui(self, dsl: dict):
        DSLManager.load_dsl_to_gui(self, dsl)
    
    def update_preview(self):
        """미리보기 업데이트"""
        # URL/로컬 입력 영역 가시성 토글
        is_title_local = self.title_font_source.currentText() == '로컬 폰트 파일'
        self.label_title_font_url.setVisible(not is_title_local)
        self.title_font_url.setVisible(not is_title_local)
        self.label_title_font_file.setVisible(is_title_local)
        self.title_font_file.setVisible(is_title_local)

        is_sub_local = self.subtitle_font_source.currentText() == '로컬 폰트 파일'
        self.label_subtitle_font_url.setVisible(not is_sub_local)
        self.subtitle_font_url.setVisible(not is_sub_local)
        self.label_subtitle_font_file.setVisible(is_sub_local)
        self.subtitle_font_file.setVisible(is_sub_local)

        dsl = self.generate_dsl()
        self.current_dsl = dsl


def main():
    """GUI 메인 함수"""
    app = QApplication(sys.argv)
    window = ThumbnailGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

