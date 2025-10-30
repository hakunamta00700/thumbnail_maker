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
    parser.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로')
    parser.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    parser.add_argument('--title', help='제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    parser.add_argument('--subtitle', help='부제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    parser.add_argument('--bgImg', help='배경 이미지 경로')
    
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


if __name__ == '__main__':
    main()
