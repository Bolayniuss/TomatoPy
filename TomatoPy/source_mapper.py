# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import sys
import os

from TomatoPy.filters import *


class SourceMapperItem(object):
    def __init__(self):
        self.name = ""
        self.source = ""


class FileItem(SourceMapperItem):
    def __init__(self, filename, extension, path):
        super(FileItem, self).__init__()
        self.filename = filename + "." + extension
        self.extension = extension
        self.name = filename
        self.source = path

    def get_full_path(self):
        return os.path.join(self.source, self.filename)

    @staticmethod
    def from_filename(filename, path):
        """
        :type filename: str
        :type path: str
        :rtype: FileItem
        """
        try:
            p = filename.rindex(".")
            return FileItem(filename[0:p], filename[p + 1:], path)
        except ValueError:
            return FileItem(filename, "", path)

    @staticmethod
    def from_complete_path(path):
        filename = os.path.basename(path)
        directory = os.path.dirname(path)
        return FileItem.from_filename(filename, directory)


class DirectoryMapper:
    """
    :type path: str
    :type filter: str
    :type files: list[FileItem]
    :type indexedFiles: dict[str, list[FileItem]]
    """
    def __init__(self, path, filter_=r"", encoding=None):
        self.path = path
        if encoding is not None:
            self.path = path.encode(encoding)
        self.filter = re.compile(filter_)
        self.files = []
        self.indexedFiles = {}
        self.map()

    def map(self):
        reload(sys)
        sys.setdefaultencoding('UTF8')
        for root, dirs, files in os.walk(self.path):
            for file_ in files:
                m = self.filter.match(file_)
                if m:
                    item = FileItem(m.group(1), m.group(2), root)
                    self.files.append(item)
                    key = file_[0].lower()
                    if key not in self.indexedFiles:
                        self.indexedFiles[key] = []
                    self.indexedFiles[key].append(item)

    def file_exists(self, file_):
        """
        :param file_:
        :rtype: bool
        """
        lowered_file = file_.lower()
        key = lowered_file[0]
        if key in self.indexedFiles:
            for item in self.indexedFiles[key]:
                if item.name.lower() == lowered_file:
                    return True
        return False
