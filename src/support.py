#!/usr/bin/env python3

import logging as log
import os
import sys

StrOrBytesPath = str | bytes | os.PathLike[str] | os.PathLike[bytes]


def init_logger(level: int | str = log.INFO) -> None:
    log.basicConfig(
        level=level,
        stream=sys.stdout,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def make_directory(path: StrOrBytesPath) -> None:
    if not os.path.exists(path):
        os.makedirs(path)