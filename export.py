from yuque import Yuque
import github

if __name__ == '__main__':
    yuque = Yuque()
    yuque.dump_repo('wiki')

    github.git_commit_repo(r"wiki")
