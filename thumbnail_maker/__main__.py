#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
thumbnail_maker: 단일 엔트리포인트 (subcommands: gui, generate-thumbnail, genthumb, upload)
"""

import sys
import argparse
import os

from .gui import main as gui_main
from .cli import main as generate_main, main_cli as genthumb_main
from .upload import upload_file


def main() -> None:
    parser = argparse.ArgumentParser(prog='thumbnail_maker', description='썸네일 메이커')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # gui
    subparsers.add_parser('gui', help='GUI 실행')

    # generate-thumbnail (DSL만 사용)
    gen = subparsers.add_parser('generate-thumbnail', help='DSL로 썸네일 생성')
    gen.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로')
    gen.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    gen.add_argument('--upload', action='store_true', help='생성 후 자동 업로드')

    # genthumb (간편 CLI: 제목/부제목 덮어쓰기 등)
    gt = subparsers.add_parser('genthumb', help='간편 CLI로 썸네일 생성')
    gt.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로')
    gt.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    gt.add_argument('--title', help='제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    gt.add_argument('--subtitle', help='부제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    gt.add_argument('--bgImg', help='배경 이미지 경로')
    
    # upload
    upload_parser = subparsers.add_parser('upload', help='이미지 파일 업로드')
    upload_parser.add_argument('file', help='업로드할 파일 경로')

    args, unknown = parser.parse_known_args()

    if args.command == 'gui':
        gui_main()
        return

    if args.command == 'generate-thumbnail':
        # generate_main은 자체 argparse를 사용하므로 여기서 직접 동작 위임이 어려움
        # 동일 기능을 직접 수행하기보다는 해당 모듈의 메인 로직을 그대로 호출하도록 유지
        # 간단하게는 모듈 내부가 파일 인자를 읽도록 짜여 있으므로, 여기서 args를 재적용
        # 하지만 기존 main()은 sys.argv를 파싱하므로, 안전하게 별도 경로로 수행
        # 대신 renderer를 직접 호출하지 않고, cli.main의 구현을 차용하기 위해 임시 argv 구성
        sys.argv = ['generate-thumbnail', args.dsl, '-o', args.output]
        generate_main()
        
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
        # 동일 이유로 간편 CLI도 기존 파서를 활용하기 위해 argv 재구성
        new_argv = ['genthumb']
        if args.dsl:
            new_argv.append(args.dsl)
        if args.output:
            new_argv += ['-o', args.output]
        if args.title:
            new_argv += ['--title', args.title]
        if args.subtitle:
            new_argv += ['--subtitle', args.subtitle]
        if args.bgImg:
            new_argv += ['--bgImg', args.bgImg]
        sys.argv = new_argv
        genthumb_main()
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


