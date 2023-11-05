import os
import time
from git.repo import Repo

def git_commit_repo(repo):
  curr_date = time.strftime("%Y%m%d", time.localtime(time.time()))

  local_repo = os.path.join("./repo", repo)
  repo = Repo(local_repo)
  repo.git.add(".")
  repo.git.commit('-m', curr_date + r": Auto updates from yuque.")
  repo.remote('github').push("nightly")