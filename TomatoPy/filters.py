# -*- coding: utf8 -*-
#
__author__ = 'bolay'

import re


class FileFilter:
    def __init__(self, name=".*", extensions=[".*"]):
        self.name = name
        self.extensions = extensions

    def test(self, item):
        if re.search(self.name, item.name, re.IGNORECASE) is None:
            return False
        for ext in self.extensions:
            if re.search(ext, item.extension, re.IGNORECASE) is not None:
                return True
        return False


class TorrentFilter:
    TEST_OK = 0
    TEST_FAILED_SIZE_TOO_BIG = 1
    TEST_FAILED_SIZE_TOO_SMALL = 2
    TEST_FAILED_AUTHOR_NO_MATCH = 4
    TEST_FAILED_NAME_NO_MATCH = 8

    def __init__(self, name_filters, author_filter, size=None):
        """
        :type size : dict
        :type author_filter : str
        :type name_filters : str
        :param name_filters:
        :param author_filter:
        :param size:
        """
        self.name_filters = name_filters
        self.author_filter = author_filter
        self.size_filter = size

    def test(self, torrent):
        accepted = False
        status = self.TEST_OK
        for name_filter in self.name_filters:
            if re.search(name_filter, torrent.title, re.IGNORECASE) is not None:
                accepted = True
                break
        if not accepted:
            status |= self.TEST_FAILED_NAME_NO_MATCH
        accepted = True
        if len(self.author_filter) != 0:
            if re.search(self.author_filter, torrent.author, re.IGNORECASE) is None:
                accepted = False
        if not accepted:
            status |= self.TEST_FAILED_AUTHOR_NO_MATCH

        if self.size_filter is not None:
            if "gt" in self.size_filter:
                accepted = torrent.size >= self.size_filter["gt"]
                if not accepted:
                    status |= self.TEST_FAILED_SIZE_TOO_SMALL

            if "lt" in self.size_filter:
                accepted = torrent.size <= self.size_filter["lt"]
                if not accepted:
                    status |= self.TEST_FAILED_SIZE_TOO_BIG
        return status
