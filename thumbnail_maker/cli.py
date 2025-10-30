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


def main():
    """메인 CLI 진입점"""
    parser = argparse.ArgumentParser(description='썸네일 생성')
    parser.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로')
    parser.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    
    args = parser.parse_args()
    
    # DSL 파일 확인
    if not os.path.exists(args.dsl):
        print(f"오류: DSL 파일을 찾을 수 없습니다: {args.dsl}")
        sys.exit(1)
    
    # DSL 읽기
    with open(args.dsl, 'r', encoding='utf-8') as f:
        dsl = json.load(f)
    
    # 썸네일 생성
    ThumbnailRenderer.render_thumbnail(dsl, args.output)


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
    
    # DSL 파일 확인
    if not os.path.exists(args.dsl):
        print(f"오류: DSL 파일을 찾을 수 없습니다: {args.dsl}")
        sys.exit(1)
    
    # DSL 읽기
    with open(args.dsl, 'r', encoding='utf-8') as f:
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
    ThumbnailRenderer.render_thumbnail(dsl, args.output)


if __name__ == '__main__':
    main()
