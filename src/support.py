#!/usr/bin/env python3

import logging as log
import sys


def init_logger(level: int | str = log.INFO) -> None:
    log.basicConfig(
        level=level,
        stream=sys.stdout,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
