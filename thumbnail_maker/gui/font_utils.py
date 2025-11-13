#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
폰트 관련 유틸리티 함수
"""

import os

try:
    from fontTools.ttLib import TTFont
except Exception:
    TTFont = None


def infer_font_name_from_file(file_path: str) -> str:
    """파일 경로에서 폰트 이름 추출"""
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

