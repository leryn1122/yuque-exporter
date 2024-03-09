#!/usr/bin/env python3

import logging as log
import os
import re
from re import Match
import requests
from typing import List

import support


class MarkdownProcessFilter:
    """
    """

    def do_filter(self, content: str, **kwargs) -> str:
        pass


class MarkdownEraseEmptyAnchorFilter(MarkdownProcessFilter):
    """
    Erases empty anchor in markdown.
    """

    def __init__(self):
        self._pattern = r"<a\sname=\"[a-zA-Z0-9]+\"></a>"

    def do_filter(self, content: str, **kwargs) -> str:
        return re.sub(self._pattern, '\n', content)


class MarkdownEraseEmptyAnchorFilter(MarkdownProcessFilter):
    """
    Erases empty anchor in markdown.
    """

    def __init__(self):
        self._pattern = r"<a\sname=\"[a-zA-Z0-9]+\"></a>\n"

    def do_filter(self, content: str, **kwargs) -> str:
        return re.sub(self._pattern, '\n', content)


class MarkdownRewriteImageFilter(MarkdownProcessFilter):
    """
    Use regular expression to replace image addresses by new local-redirected ones.

    Markdown image link:
      r'\!\[(.*?)\]\((.*?)\)'

    URL pattern:
      r'https?:\/\/([\w\-_]+\.)+([\w\-_]+)(\/(?P<filename>[\w\-_\.]+))+(?:(\/[^\/?#]+)*)?(\?[^#]+)?(#.+)?'

    """
    MARKDOWN_IMAGE_REGEX = r'\!\[(.*?)\]\((.*?)\)'
    HTTP_URL_REGEX = r'https?:\/\/([\w\-_]+\.)+([\w\-_]+)(\/(?P<filename>[\w\-_\.]+))+(?:(\/[^\/?#]+)*)?(\?[^#]+)?(#[\w%\.=\-_&]+)?'

    def __init__(self, path, token):
        self._pattern = MarkdownRewriteImageFilter.image_regex()
        self._export_dir = path
        self._token = token

    @classmethod
    def image_regex(cls) -> str:
        return (MarkdownRewriteImageFilter.MARKDOWN_IMAGE_REGEX
                .replace(r'(.*?)', r'(?P<img_name>.*?)', 1)
                .replace(r'(.*?)',
                         r'(?P<img_src>' + MarkdownRewriteImageFilter.HTTP_URL_REGEX + ')',
                         1))

    def do_filter(self, content: str, **kwargs) -> (str, List[Match[str]]):
        images = [_.groupdict() for _ in re.finditer(self._pattern, content)]
        repl = r"![\g<img_name>](./../assets/\g<filename>)\n"
        content = re.sub(self._pattern, repl, content)

        if images:
            support.make_directory(os.path.join(self._export_dir, 'assets'))
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


class MarkdownEraseLineBreakFilter(MarkdownProcessFilter):
    def do_filter(self, content: str, **kwargs) -> str:
        return re.sub("<br\s?/>", '\n', content)

