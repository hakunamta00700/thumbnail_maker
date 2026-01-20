#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
thumbnail_maker: 단일 엔트리포인트 (subcommands: gui, generate-thumbnail, genthumb, upload)
"""

import sys
import argparse
import os

from .gui import main as gui_main
from .cli import main as generate_main, main_cli as genthumb_main, generate_thumbnail_from_args
from .upload import upload_file


def main() -> None:
    parser = argparse.ArgumentParser(prog='thumbnail_maker', description='썸네일 메이커')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # gui
    subparsers.add_parser('gui', help='GUI 실행')

    # generate-thumbnail (DSL만 사용)
    gen = subparsers.add_parser('generate-thumbnail', help='DSL로 썸네일 생성')
    gen.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로 또는 .thl 파일 경로')
    gen.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    gen.add_argument('-u', '--upload', action='store_true', help='생성 후 자동 업로드')
    
    # 해상도 관련
    gen.add_argument('-rm', '--resolution-mode', choices=['preset', 'fixedRatio', 'custom'], help='해상도 모드')
    gen.add_argument('-ar', '--aspect-ratio', choices=['16:9', '9:16', '4:3', '1:1'], help='종횡비')
    gen.add_argument('-w', '--width', type=int, help='너비')
    gen.add_argument('-h', '--height', type=int, help='높이')
    
    # 배경 관련
    gen.add_argument('-bt', '--background-type', choices=['solid', 'gradient', 'image'], help='배경 타입')
    gen.add_argument('-bc', '--background-color', help='배경 색상 (hex)')
    gen.add_argument('-bi', '--background-image', help='배경 이미지 경로')
    gen.add_argument('-bo', '--background-opacity', type=int, help='배경 투명도 (0-100)')
    gen.add_argument('-bb', '--background-blur', type=int, help='배경 블러 (0-20)')
    
    # 제목 관련
    gen.add_argument('-tt', '--title-text', help='제목 텍스트')
    gen.add_argument('-tp', '--title-position', choices=['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br'], help='제목 위치')
    gen.add_argument('-tfn', '--title-font-name', help='제목 폰트 이름')
    gen.add_argument('-tfu', '--title-font-url', help='제목 폰트 URL')
    gen.add_argument('-tff', '--title-font-file', help='제목 로컬 폰트 파일 경로')
    gen.add_argument('-tfw', '--title-font-weight', choices=['normal', 'bold'], help='제목 폰트 굵기')
    gen.add_argument('-tfs', '--title-font-style', choices=['normal', 'italic'], help='제목 폰트 스타일')
    gen.add_argument('-tfsz', '--title-font-size', type=int, help='제목 폰트 크기')
    gen.add_argument('-tc', '--title-color', help='제목 색상 (hex)')
    gen.add_argument('-to', '--title-outline', action='store_true', help='제목 외곽선 사용')
    gen.add_argument('-tot', '--title-outline-thickness', type=int, help='제목 외곽선 두께')
    gen.add_argument('-tww', '--title-word-wrap', action='store_true', help='제목 단어 단위 줄바꿈')
    
    # 부제목 관련
    gen.add_argument('-sv', '--subtitle-visible', action='store_true', help='부제목 표시')
    gen.add_argument('-st', '--subtitle-text', help='부제목 텍스트')
    gen.add_argument('-sp', '--subtitle-position', choices=['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br'], help='부제목 위치')
    gen.add_argument('-sfn', '--subtitle-font-name', help='부제목 폰트 이름')
    gen.add_argument('-sfu', '--subtitle-font-url', help='부제목 폰트 URL')
    gen.add_argument('-sff', '--subtitle-font-file', help='부제목 로컬 폰트 파일 경로')
    gen.add_argument('-sfw', '--subtitle-font-weight', choices=['normal', 'bold'], help='부제목 폰트 굵기')
    gen.add_argument('-sfs', '--subtitle-font-style', choices=['normal', 'italic'], help='부제목 폰트 스타일')
    gen.add_argument('-sfsz', '--subtitle-font-size', type=int, help='부제목 폰트 크기')
    gen.add_argument('-sc', '--subtitle-color', help='부제목 색상 (hex)')
    gen.add_argument('-sww', '--subtitle-word-wrap', action='store_true', help='부제목 단어 단위 줄바꿈')

    # genthumb (간편 CLI: 제목/부제목 덮어쓰기 등)
    gt = subparsers.add_parser('genthumb', help='간편 CLI로 썸네일 생성')
    gt.add_argument('dsl', nargs='?', default=None, help='DSL 파일 경로 또는 .thl 파일 경로')
    gt.add_argument('--template', help='템플릿 파일 경로 (.thl 파일)')
    gt.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    gt.add_argument('-t', '--title', help='제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    gt.add_argument('--subtitle', help='부제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    gt.add_argument('-b', '--background-image', dest='bgImg', help='배경 이미지 경로')
    gt.add_argument('-u', '--upload', action='store_true', help='생성 후 자동 업로드')
    
    # upload
    upload_parser = subparsers.add_parser('upload', help='이미지 파일 업로드')
    upload_parser.add_argument('file', help='업로드할 파일 경로')

    args, unknown = parser.parse_known_args()

    if args.command == 'gui':
        gui_main()
        return

    if args.command == 'generate-thumbnail':
        # CLI 파라미터를 사용하여 썸네일 생성
        generate_thumbnail_from_args(args)
        
        # 업로드 옵션이 있으면 업로드 수행
        if args.upload:
            output_path = args.output
            if not os.path.isabs(output_path):
                output_path = os.path.abspath(output_path)
            
            if not os.path.exists(output_path):
                print(f"오류: 출력 파일을 찾을 수 없습니다: {output_path}")
                sys.exit(1)
            
            print(f"업로드 중: {output_path}")
            url = upload_file(output_path)
            if url:
                print(f"✅ 업로드 완료: {url}")
            else:
                print("❌ 업로드 실패")
                sys.exit(1)
        return

    if args.command == 'genthumb':
        # 템플릿 파일 또는 DSL 파일 결정
        template_or_dsl = args.template or args.dsl
        if not template_or_dsl:
            template_or_dsl = 'thumbnail.json'  # 기본값
        
        # 동일 이유로 간편 CLI도 기존 파서를 활용하기 위해 argv 재구성
        new_argv = ['genthumb']
        if template_or_dsl:
            new_argv.append(template_or_dsl)
        if args.output:
            new_argv += ['-o', args.output]
        if args.title:
            new_argv += ['-t', args.title]
        if args.subtitle:
            new_argv += ['--subtitle', args.subtitle]
        if args.bgImg:
            new_argv += ['-b', args.bgImg]
        sys.argv = new_argv
        genthumb_main()
        
        # 업로드 옵션이 있으면 업로드 수행
        if args.upload:
            output_path = args.output
            if not os.path.isabs(output_path):
                output_path = os.path.abspath(output_path)
            
            if not os.path.exists(output_path):
                print(f"오류: 출력 파일을 찾을 수 없습니다: {output_path}")
                sys.exit(1)
            
            print(f"업로드 중: {output_path}")
            url = upload_file(output_path)
            if url:
                print(f"✅ 업로드 완료: {url}")
            else:
                print("❌ 업로드 실패")
                sys.exit(1)
        return
    
    if args.command == 'upload':
        file_path = args.file
        if not os.path.exists(file_path):
            print(f"오류: 파일을 찾을 수 없습니다: {file_path}")
            sys.exit(1)
        
        print(f"업로드 중: {file_path}")
        url = upload_file(file_path)
        if url:
            print(f"✅ 업로드 완료: {url}")
        else:
            print("❌ 업로드 실패")
            sys.exit(1)
        return


if __name__ == '__main__':
    main()


