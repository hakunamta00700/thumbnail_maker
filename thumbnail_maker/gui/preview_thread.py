#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
미리보기 생성 스레드
"""

from PySide6.QtCore import QThread, Signal
from ..renderer import ThumbnailRenderer


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

