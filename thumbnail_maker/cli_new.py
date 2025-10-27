#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메인 썸네일 생성 스크립트
"""

import sys
import os
import json
import argparse
from .renderer import ThumbnailRenderer


def main():
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
    
    print(f"✅ 썸네일 생성 완료: {args.output}")


if __name__ == '__main__':
    main()

