#!/usr/bin/env python3

import argparse
import logging as log

from yuque import YuqueExporter
import github
from support import init_logger

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='yuque-exporter')
    parser.add_argument('--log-level',
                        type=str,
                        default=log.getLevelName(log.INFO),
                        help=r'Set log level')
    parser.add_argument('--yuque',
                        default=False,
                        action='store_true',
                        help=r'Activate Yuque export')
    parser.add_argument('--git-push',
                        default=False,
                        action='store_true',
                        help='Activate Git push to remote')
    cli_args = parser.parse_args()

    cli_args.log_level = log.getLevelName(cli_args.log_level)
    init_logger(cli_args.log_level)

    if cli_args.yuque:
        yuque = YuqueExporter()
        yuque.dump_repo('wiki')

    if cli_args.git_push:
        github.git_commit_repo(r'wiki')
