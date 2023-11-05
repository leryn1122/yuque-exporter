import os
import re
import requests
from prettytable import PrettyTable

YUQUE_URL = "https://www.yuque.com/api/v2"

class Yuque:
  def __init__(self):
    self.namespace, self.token = self.get_user_info()
    self.headers = {
      "Content-Type": "application/json",
      "User-Agent": "python script",
      "X-Auth-Token": self.token
    }
    self.repos = {}
    self.export_dir = "./repo/wiki/"
  
  def get_user_info(self):
    """
    获取语雀的用户信息，保存在 `.yuque` 下,
    若文件不存在, 则在命令行询问并创建文件
    """
    user_info_file = ".yuque"
    if os.path.isfile(user_info_file):
      with open(user_info_file, encoding="utf-8") as f:
        user_info = f.read().split("|")
    else:
      namespace = input("输入语雀namespace: ")
      access_token = input("输入语雀token: ")
      user_info = [namespace, access_token]
      with open(user_info_file, 'w') as f:
        f.write(namespace + '|' + access_token)
    return user_info
  
  def invoke_api(self, url):
    """
    调用语雀的 API 地址
    params: API 的地址
    return: JSON 格式的请求响应
    """
    response = requests.get(YUQUE_URL + url, headers=self.headers)
    response.encoding = 'utf-8'
    return response.json()

  def get_repos(self):
    url = "/users/%s/repos" % self.namespace
    result = self.invoke_api(url).get('data')
    for _repo in result:
      repo_id = _repo['id']
      repo_name = _repo['slug']
      self.repos[repo_name] = repo_id
    return self.repos
  
  def get_docs(self, repo_id):
    url = "/repos/%s/docs" % repo_id
    result = self.invoke_api(url).get('data')
    docs = []
    for _docs in result:
      docs.append({
        "id": _docs['id'],
        "name": _docs['title'],
        "slug": _docs['slug']
      })
    return docs

  def make_directory(self, path):
    if not os.path.exists(path):
      os.makedirs(path)

  def download_markdown(self, repo_id, slug, title):
    """
    下载指定文章 Markdown 格式的正文内容, 并且把服务端图像修改为本地路径
    本地图像路径在./repo/<repo>/assets/<image>
    params: 仓库 ID
    params: Laravel slug
    return: 替换过的 Markdown
    """
    url = "/repos/%s/docs/%s" % (repo_id, slug)
    result = self.invoke_api(url).get('data')
    content_in_md = result.get('body')
    content_in_md, images = self.modify_redirect_local_image(content_in_md)
    content_in_md = self.modify_empty(content_in_md)

    markdown_file = os.path.join(self.export_dir, slug.split('.')[0], slug.replace(' ', '') + '.md')
    markdown_dir = os.path.join(self.export_dir, slug.split('.')[0])
    if not os.path.exists(markdown_dir):
      os.makedirs(markdown_dir)
    with open(markdown_file, 'w') as f:
      f.write(content_in_md)

    if images:
      image_dir = os.path.join(self.export_dir, 'assets')
      self.make_directory(image_dir)
      for _image in images:
        image_file = os.path.join(self.export_dir, 'assets', _image['filename'])
        resp = requests.get(_image['img_src'], headers=self.headers)
        with open(image_file, 'wb') as f:
          f.write(resp.content)
    return content_in_md

  def modify_redirect_local_image(self, content):
    """
    利用正则表达式替换图片地址, 并返回新的图片地址
    """
    pattern = r"!\[(?P<img_name>.*?)\]" \
              r"\((?P<img_src>https:\/\/cdn\.nlark\.com\/yuque.*\/(?P<slug>\d+)\/(?P<filename>.*?\.[a-zA-z]+)).*\)"
    repl = r"![\g<img_name>](./../assets/\g<filename>)"
    images = [_.groupdict() for _ in re.finditer(pattern, content)]
    new_content = re.sub(pattern, repl, content)
    return new_content, images

  def modify_empty(self, content):
    """
    """
    pattern = r"<a\sname=\"[a-zA-Z0-9]+\"></a>"
    new_content = re.sub(pattern, '', content)
    return new_content

  def dump_repo(self, repo_name):
      """
      导出指定仓库下的所有文档
      """
      repo_id = self.get_repos()[repo_name]
      repo = os.path.join('repo', repo_name)
      self.export_dir = repo
      self.make_directory(self.export_dir)
      for _docs in self.get_docs(repo_id):
        self.download_markdown(repo_id, _docs['slug'], _docs['name'])