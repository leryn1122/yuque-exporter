#!/usr/bin/env python3

from datetime import datetime
import http
import logging as log
import os
from typing import List, Any, AnyStr

import pytz
import requests
import support

from md_filter import (MarkdownProcessFilter,
                       MarkdownEraseEmptyAnchorFilter,
                       MarkdownRewriteImageFilter,
                       MarkdownEraseLineBreakFilter,
                       MarkdownAddDocusaurusDescriptionFilter)


class YuqueExporter:
    """
    YuqueExporter is an instance to export Yuque repo through open APIs.
    """
    YUQUE_URL = 'https://www.yuque.com/api/v2'

    def __init__(self):
        self._namespace, self._token = self.get_user_info()
        self._headers: dict[AnyStr, AnyStr] = {
            "Content-Type": "application/json",
            "User-Agent": "python script",
            "X-Auth-Token": self._token
        }
        self._repos = {}
        self._export_dir: None | support.StrOrBytesPath = None
        self._timestamp: None | datetime = None

    def get_user_info(self) -> List[AnyStr]:
        """
        Get the Yuque user info, and save it in `~/.yuque/config`
        If the file does not exist, it will be created after interaction with command line.
        """
        user_info_file = os.path.join(os.path.expanduser('~'), '.yuque', 'config')
        if os.path.isfile(user_info_file):
            with open(user_info_file, encoding='utf-8') as f:
                user_info = f.read().strip('\n').split('|')
        else:
            user_info = self._ask_for_user_info(user_info_file)
        return user_info

    # noinspection PyMethodMayBeStatic
    def _ask_for_user_info(self, user_info_file: AnyStr) -> List[AnyStr]:
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

    def get_docs(self, repo_id) -> List[Any]:
        docs = []
        offset = 0
        while True:
            url = f'/repos/{repo_id}/docs?limit=100&offset={offset}'
            result = self.invoke_api(url).get('data')
            if len(result) == 0:
                break
            for _doc in result:
                # if _doc['slug'] != "readme":
                #     continue
                # if datetime.fromisoformat(_doc['updated_at']) > self._timestamp \
                #         or datetime.fromisoformat(_doc['content_updated_at']) > self._timestamp\
                #         or datetime.fromisoformat(_doc['published_at']) > self._timestamp\
                #         or True:
                if True:
                    docs.append({
                        "id": _doc['id'],
                        "name": _doc['title'],
                        "slug": _doc['slug']
                    })
            offset += 100
        return docs

    def download_markdown(self, repo_id, slug) -> None:
        url = f'/repos/{repo_id}/docs/{slug}'
        result = self.invoke_api(url).get('data')
        content = result.get('body')
        processor = YuqueDocumentProcessor(token=self._token,
                                           export_dir=self._export_dir,
                                           content=content,
                                           doc=result)
        processor.save_markdown(slug)

    def dump_repo(self, repo_name: str) -> None:
        """
        Dump the all documents in the specified repo
        """
        repo_id = self.get_repos()[repo_name]
        repo = os.path.join('..', 'repo', repo_name)
        self._export_dir = repo
        self._timestamp = self.fetch_timestamp()
        support.make_directory(self._export_dir)
        for _docs in self.get_docs(repo_id):
            self.download_markdown(repo_id, _docs['slug'])
        self.save_timestamp()

    def save_timestamp(self) -> None:
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
    def __init__(self, token: str, export_dir: str, content: AnyStr, doc: Any):
        self._token: str = token
        self._export_dir: str = export_dir
        self._content: str = content
        self._filters: List[MarkdownProcessFilter] = [
            MarkdownEraseEmptyAnchorFilter(),
            MarkdownRewriteImageFilter(path=self._export_dir, token=self._token),
            MarkdownEraseLineBreakFilter(),
            MarkdownAddDocusaurusDescriptionFilter(doc=doc)
        ]

    def save_markdown(self, slug: str):
        for filter in self._filters:
            self._content = filter.do_filter(content=self._content)

        markdown_file = os.path.join(self._export_dir, slug.split('.')[0], slug.replace(' ', '') + '.md')
        markdown_dir = os.path.join(self._export_dir, slug.split('.')[0])
        support.make_directory(markdown_dir)
        with open(markdown_file, 'w', encoding='utf-8') as f:
            log.info("Saving markdown: %s", slug)
            f.write(self._content)
        return self._content
