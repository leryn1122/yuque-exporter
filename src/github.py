#!/usr/bin/env python3

import os
import time
import logging as log

from git.repo import Repo


def git_commit_repo(repo):
    curr_date = time.strftime("%Y%m%d", time.localtime(time.time()))

    local_repo = os.path.join('..', 'repo', repo)
    repo = Repo(local_repo)

    config_writer = repo.config_writer()
    config_writer.set_value("user", "name", "leryn1122")
    config_writer.set_value("user", "email", "pinktin@sina.com")

    config_writer.release()

    repo.git.add('.')
    repo.git.commit('-m', f"{curr_date}: Auto updates from yuque.")
    log.info("git commit")

    repo.remote('origin').push(repo.active_branch.name)
    log.info("git push origin %s", repo.active_branch.name)
