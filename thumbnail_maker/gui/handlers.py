#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이벤트 핸들러 모듈
"""

import os
import json
import tempfile
import base64
from PySide6.QtWidgets import (QColorDialog, QFileDialog, QMessageBox, 
                               QDialog, QVBoxLayout, QPlainTextEdit, QDialogButtonBox)
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtCore import Qt

from ..renderer import ThumbnailRenderer
from .font_utils import infer_font_name_from_file


class EventHandlers:
    """이벤트 핸들러 클래스"""
    
    @staticmethod
    def on_resolution_mode_changed(gui, mode):
        """해상도 모드 변경 시 처리"""
        if mode == 'preset':
            gui.aspect_ratio.setEnabled(True)
        elif mode == 'fixedRatio':
            gui.aspect_ratio.setEnabled(True)
            # fixedRatio 모드로 변경 시 현재 너비를 기준으로 높이 재계산
            EventHandlers.on_aspect_ratio_changed(gui, gui.aspect_ratio.currentText())
        else:  # custom
            gui.aspect_ratio.setEnabled(False)
        gui.update_preview()
    
    @staticmethod
    def on_aspect_ratio_changed(gui, ratio):
        """비율 변경 시 처리"""
        # fixedRatio 모드일 때만 너비를 기준으로 높이 재계산
        if gui.res_mode.currentText() == 'fixedRatio':
            try:
                parts = ratio.split(':')
                if len(parts) == 2:
                    rw, rh = float(parts[0]), float(parts[1])
                    if rw > 0 and rh > 0:
                        aspect_ratio = rw / rh
                        current_width = gui.width_spin.value()
                        new_height = int(current_width / aspect_ratio)
                        if not gui._updating_dimension:
                            gui._updating_dimension = True
                            gui.height_spin.setValue(new_height)
                            gui._updating_dimension = False
            except (ValueError, ZeroDivisionError):
                pass
        
        gui.update_preview()
    
    @staticmethod
    def on_width_changed(gui, value):
        """너비 변경 시 처리"""
        if gui._updating_dimension:
            return
        
        # fixedRatio 모드일 때 비율에 맞게 높이 조정
        if gui.res_mode.currentText() == 'fixedRatio':
            ratio_str = gui.aspect_ratio.currentText()
            try:
                parts = ratio_str.split(':')
                if len(parts) == 2:
                    rw, rh = float(parts[0]), float(parts[1])
                    if rw > 0 and rh > 0:
                        aspect_ratio = rw / rh
                        new_height = int(value / aspect_ratio)
                        gui._updating_dimension = True
                        gui.height_spin.setValue(new_height)
                        gui._updating_dimension = False
            except (ValueError, ZeroDivisionError):
                pass
        
        gui.update_preview()
    
    @staticmethod
    def on_height_changed(gui, value):
        """높이 변경 시 처리"""
        if gui._updating_dimension:
            return
        
        # fixedRatio 모드일 때 비율에 맞게 너비 조정
        if gui.res_mode.currentText() == 'fixedRatio':
            ratio_str = gui.aspect_ratio.currentText()
            try:
                parts = ratio_str.split(':')
                if len(parts) == 2:
                    rw, rh = float(parts[0]), float(parts[1])
                    if rw > 0 and rh > 0:
                        aspect_ratio = rw / rh
                        new_width = int(value * aspect_ratio)
                        gui._updating_dimension = True
                        gui.width_spin.setValue(new_width)
                        gui._updating_dimension = False
            except (ValueError, ZeroDivisionError):
                pass
        
        gui.update_preview()
    
    @staticmethod
    def select_bg_color(gui):
        """배경 색상 선택"""
        color = QColorDialog.getColor(QColor(gui.bg_color))
        if color.isValid():
            gui.bg_color = color.name()
            gui.update_preview()
    
    @staticmethod
    def select_title_color(gui):
        """제목 색상 선택"""
        color = QColorDialog.getColor(QColor(gui.title_color))
        if color.isValid():
            gui.title_color = color.name()
            gui.update_preview()
    
    @staticmethod
    def select_subtitle_color(gui):
        """부제목 색상 선택"""
        color = QColorDialog.getColor(QColor(gui.subtitle_color))
        if color.isValid():
            gui.subtitle_color = color.name()
            gui.update_preview()
    
    @staticmethod
    def select_background_image(gui):
        """배경 이미지 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            gui, '배경 이미지 선택', '', 'Images (*.png *.jpg *.jpeg *.gif *.bmp)'
        )
        if file_path:
            gui.bg_image_path.setText(file_path)
            gui.update_preview()
    
    @staticmethod
    def set_title_font_name_from_path(gui, path: str):
        """제목 폰트 이름을 파일 경로에서 추출하여 설정"""
        inferred = infer_font_name_from_file(path)
        if inferred:
            gui.title_font_name.setText(inferred)
        gui.update_preview()
    
    @staticmethod
    def set_subtitle_font_name_from_path(gui, path: str):
        """부제목 폰트 이름을 파일 경로에서 추출하여 설정"""
        inferred = infer_font_name_from_file(path)
        if inferred:
            gui.subtitle_font_name.setText(inferred)
        gui.update_preview()
    
    @staticmethod
    def on_title_font_file_changed(gui):
        """제목 폰트 파일 경로 변경 시 처리"""
        path = gui.title_font_file.text().strip()
        if path and not gui.title_font_name.text().strip():
            EventHandlers.set_title_font_name_from_path(gui, path)
        else:
            gui.update_preview()
    
    @staticmethod
    def on_subtitle_font_file_changed(gui):
        """부제목 폰트 파일 경로 변경 시 처리"""
        path = gui.subtitle_font_file.text().strip()
        if path and not gui.subtitle_font_name.text().strip():
            EventHandlers.set_subtitle_font_name_from_path(gui, path)
        else:
            gui.update_preview()
    
    @staticmethod
    def generate_preview(gui):
        """미리보기 생성"""
        if not hasattr(gui, 'current_dsl'):
            gui.update_preview()
        
        gui.preview_btn.setEnabled(False)
        gui.preview_btn.setText('생성 중...')
        
        # 스레드에서 생성
        from .preview_thread import PreviewThread
        gui.preview_thread = PreviewThread(gui.current_dsl)
        gui.preview_thread.preview_ready.connect(lambda path: EventHandlers.on_preview_ready(gui, path))
        gui.preview_thread.start()
    
    @staticmethod
    def on_preview_ready(gui, file_path):
        """미리보기 준비됨"""
        if file_path and os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            gui.preview_label.setPixmap(pixmap.scaled(
                480, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            msg = gui.preview_thread.error_message or '미리보기 생성 중 오류가 발생했습니다.'
            QMessageBox.critical(gui, '에러', msg)
        
        gui.preview_btn.setEnabled(True)
        gui.preview_btn.setText('미리보기 생성')
    
    @staticmethod
    def save_thumbnail(gui):
        """썸네일 저장"""
        if not hasattr(gui, 'current_dsl'):
            QMessageBox.warning(gui, '경고', '먼저 미리보기를 생성해주세요.')
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            gui, '썸네일 저장', 'thumbnail.png', 'Images (*.png)'
        )
        
        if file_path:
            try:
                ThumbnailRenderer.render_thumbnail(gui.current_dsl, file_path)
                QMessageBox.information(gui, '완료', f'저장 완료: {file_path}')
            except Exception as e:
                QMessageBox.critical(gui, '에러', f'저장 실패: {e}')
    
    @staticmethod
    def show_dsl_dialog(gui):
        """현재 DSL을 JSON으로 출력하는 다이얼로그"""
        if not hasattr(gui, 'current_dsl'):
            gui.update_preview()
        from .dsl_manager import DSLManager
        dsl = getattr(gui, 'current_dsl', DSLManager.generate_dsl(gui))
        try:
            text = json.dumps(dsl, ensure_ascii=False, indent=2)
        except Exception:
            text = str(dsl)

        dlg = QDialog(gui)
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
    
    @staticmethod
    def save_dsl(gui):
        """현재 DSL을 JSON 파일로 저장"""
        if not hasattr(gui, 'current_dsl'):
            gui.update_preview()
        from .dsl_manager import DSLManager
        dsl = getattr(gui, 'current_dsl', DSLManager.generate_dsl(gui))

        file_path, _ = QFileDialog.getSaveFileName(
            gui, 'DSL 저장', 'thumbnail.json', 'JSON (*.json)'
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dsl, f, ensure_ascii=False, indent=2)
            QMessageBox.information(gui, '완료', f'DSL 저장 완료: {file_path}')
        except Exception as e:
            QMessageBox.critical(gui, '에러', f'DSL 저장 실패: {e}')
    
    @staticmethod
    def load_thl_package(gui):
        """.thl 패키지를 로드하여 GUI에 적용"""
        file_path, _ = QFileDialog.getOpenFileName(
            gui, '패키지 로드', '', 'Thumbnail Package (*.thl)'
        )
        if not file_path:
            return
        
        try:
            from .dsl_manager import DSLManager
            dsl = DSLManager.load_thl_package(gui, file_path)
            DSLManager.load_dsl_to_gui(gui, dsl)
            QMessageBox.information(gui, '완료', f'패키지 로드 완료: {file_path}')
        except Exception as e:
            QMessageBox.critical(gui, '에러', f'패키지 로드 실패: {e}')
    
    @staticmethod
    def save_thl_package(gui):
        """현재 DSL과 사용 폰트를 묶어 .thl 패키지로 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            gui, '패키지 저장', 'thumbnail.thl', 'Thumbnail Package (*.thl)'
        )
        if not file_path:
            return
        try:
            from .dsl_manager import DSLManager
            DSLManager.save_thl_package(gui, file_path)
            QMessageBox.information(gui, '완료', f'패키지 저장 완료: {file_path}')
        except Exception as e:
            QMessageBox.critical(gui, '에러', f'패키지 저장 실패: {e}')

