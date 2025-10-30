#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
thumbnail_maker: 단일 엔트리포인트 (subcommands: gui, generate-thumbnail, genthumb)
"""

import sys
import argparse

from .gui import main as gui_main
from .cli import main as generate_main, main_cli as genthumb_main


def main() -> None:
    parser = argparse.ArgumentParser(prog='thumbnail_maker', description='썸네일 메이커')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # gui
    subparsers.add_parser('gui', help='GUI 실행')

    # generate-thumbnail (DSL만 사용)
    gen = subparsers.add_parser('generate-thumbnail', help='DSL로 썸네일 생성')
    gen.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로')
    gen.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')

    # genthumb (간편 CLI: 제목/부제목 덮어쓰기 등)
    gt = subparsers.add_parser('genthumb', help='간편 CLI로 썸네일 생성')
    gt.add_argument('dsl', nargs='?', default='thumbnail.json', help='DSL 파일 경로')
    gt.add_argument('-o', '--output', default='thumbnail.png', help='출력 파일 경로')
    gt.add_argument('--title', help='제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    gt.add_argument('--subtitle', help='부제목 덮어쓰기 (\\n 또는 실제 줄바꿈 지원)')
    gt.add_argument('--bgImg', help='배경 이미지 경로')

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


if __name__ == '__main__':
    main()


