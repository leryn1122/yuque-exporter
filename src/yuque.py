#!/usr/bin/env python3

from datetime import datetime
import http
import logging as log
import os
import re
from typing import List, Any, AnyStr

import pytz
import requests


def make_directory(path) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


class YuqueExporter:
    """
    YuqueExporter is an instance to export Yuque repo through open APIs.
    """
    YUQUE_URL = 'https://www.yuque.com/api/v2'

    def __init__(self):
        self._namespace, self._token = self.get_user_info()
        self._headers = {
            "Content-Type": "application/json",
            "User-Agent": "python script",
            "X-Auth-Token": self._token
        }
        self._repos = {}
        self._export_dir: None | os.PathLike[str] = None
        self._timestamp: None | datetime = None

    def get_user_info(self):
        """
        Get the Yuque user info, and save it in `~/.yuque/config`
        If the file does not exist, it will be created after interaction with command line.
        """
        user_info_file = os.path.join(os.path.expanduser('~'), '.yuque', 'config')
        if os.path.isfile(user_info_file):
            with open(user_info_file, encoding='utf-8') as f:
                user_info = f.read().strip('\n').split('|')
        else:
            namespace = input('输入语雀namespace: ')
            access_token = input('输入语雀token: ')
            user_info = [namespace, access_token]
            with open(user_info_file, 'w', encoding='utf-8') as f:
                f.write(namespace + '|' + access_token)
                log.debug("Save the user info to the file")
        return user_info

    def invoke_api(self, url) -> Any:
        """
        Invoke Yuque RESTful API
        """
        response = requests.get(YuqueExporter.YUQUE_URL + url, headers=self._headers, timeout=1000)
        if not http.HTTPStatus.OK <= response.status_code < http.HTTPStatus.MULTIPLE_CHOICES:
            log.error("Failed to invoke Yuque API, returning HTTP status code: %d",
                      response.status_code)
        response.encoding = 'utf-8'
        return response.json()

    def get_repos(self):
        url = f'/users/{self._namespace}/repos'
        result = self.invoke_api(url).get('data')
        for _repo in result:
            repo_id = _repo['id']
            repo_name = _repo['slug']
            self._repos[repo_name] = repo_id
        return self._repos

    def get_docs(self, repo_id) -> List:
        docs = []
        offset = 0
        while True:
            url = f'/repos/{repo_id}/docs?limit=100&offset={offset}'
            result = self.invoke_api(url).get('data')
            if len(result) == 0:
                break
            for _doc in result:
                if datetime.fromisoformat(_doc['updated_at']) > self._timestamp \
                        or datetime.fromisoformat(_doc['content_updated_at']) > self._timestamp:
                    docs.append({
                        "id": _doc['id'],
                        "name": _doc['title'],
                        "slug": _doc['slug']
                    })
            offset += 100
        return docs

    def download_markdown(self, repo_id, slug):
        url = f'/repos/{repo_id}/docs/{slug}'
        result = self.invoke_api(url).get('data')
        content = result.get('body')
        processor = YuqueDocumentProcessor(token=self._token,
                                           export_dir=self._export_dir,
                                           content=content)
        processor.save_markdown(slug)

    def dump_repo(self, repo_name):
        """
        Dump the all documents in the specified repo
        """
        repo_id = self.get_repos()[repo_name]
        repo = os.path.join('..', 'repo', repo_name)
        self._export_dir = repo
        self._timestamp = self.fetch_timestamp()
        make_directory(self._export_dir)
        for _docs in self.get_docs(repo_id):
            self.download_markdown(repo_id, _docs['slug'])
        self.save_timestamp()

    def save_timestamp(self):
        with open(os.path.join(self._export_dir, '_timestamp.txt'), 'w', encoding='utf-8') as f:
            f.write(datetime.now(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%S.%sZ"))

    def fetch_timestamp(self) -> datetime:
        try:
            with open(os.path.join(self._export_dir, '_timestamp.txt'), 'r', encoding='utf-8') as f:
                timestamp = f.read().strip('\n')
                log.info("Read timestamp: %s", timestamp)
                return datetime.fromisoformat(timestamp)
        except FileNotFoundError:
            log.info("Missing file `_timestamp.txt`, using current timestamp.")
            return datetime.fromisoformat('1970-01-01T00:00:00.000Z')


class YuqueDocumentProcessor:
    def __init__(self, token: str, export_dir: str, content: AnyStr):
        self._token = token
        self._export_dir = export_dir
        self._content = content

    def save_markdown(self, slug: str):
        content, images = self.rewrite_image_address()
        content = self.erase_empty_element()

        markdown_file = os.path.join(self._export_dir, slug.split('.')[0], slug.replace(' ', '') + '.md')
        markdown_dir = os.path.join(self._export_dir, slug.split('.')[0])
        make_directory(markdown_dir)
        with open(markdown_file, 'w', encoding='utf-8') as f:
            log.info("Saving markdown: %s", slug)
            f.write(content)

        if images:
            make_directory(os.path.join(self._export_dir, 'assets'))
            for _image in images:
                log.info("Downloading image: %s", _image['img_src'])
                image_file = os.path.join(self._export_dir, 'assets', _image['filename'])
                resp = requests.get(_image['img_src'], headers={
                    "User-Agent": "python script",
                    "X-Auth-Token": self._token
                }, timeout=1000)
                with open(image_file, 'wb') as f:
                    f.write(resp.content)
        return content

    def rewrite_image_address(self):
        """
        Use regular expression to replace image addresses by new local-redirected ones.
        """
        pattern = r"!\[(?P<img_name>.*?)\]" \
                  r"\((?P<img_src>https:\/\/cdn\.nlark\.com\/yuque.*\/(?P<slug>\d+)\/(?P<filename>.*?\.[a-zA-z]+)).*\)"
        repl = r"![\g<img_name>](./../assets/\g<filename>)"
        images = [_.groupdict() for _ in re.finditer(pattern, self._content)]
        new_content = re.sub(pattern, repl, self._content)
        self._content = new_content
        return new_content, images

    def erase_empty_element(self):
        pattern = r"<a\sname=\"[a-zA-Z0-9]+\"></a>"
        new_content = re.sub(pattern, '', self._content)
        self._content = new_content
        return new_content
