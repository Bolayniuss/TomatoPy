# -*- coding: utf8 -*-
__author__ = 'bolay'

import os
import re
from TomatoPy.Filters import *
from TomatoPy.SourceMapperItem import *
import sys


class DirectoryMapper:

	def __init__(self, path, filter=FileFilter(), encoding=None):
		self.path = path
		if encoding is not None:
			self.path = path.encode(encoding)
		self.filter = filter
		self.files = []
		self.map()

	def map(self):
		reload(sys)
		sys.setdefaultencoding('UTF8')
		fsEncoding = "UTF8" #sys.getfilesystemencoding()
		#path = self.path.encode(fsEncoding)
		for root, dirs, files in os.walk(self.path):
			for file in files:
				#file = file.decode(fsEncoding)
				#root = root.decode(fsEncoding)
				#print file, type(file)
				item = FileItem.fromFilename(file, root)
				if self.filter.test(item):
					self.files.append(item)


class DirectoryMapper2:

	def __init__(self, path, filter=r"", encoding=None):
		self.path = path
		if encoding is not None:
			self.path = path.encode(encoding)
		self.filter = re.compile(filter)
		self.files = []
		self.map()

	def map(self):
		reload(sys)
		sys.setdefaultencoding('UTF8')
		fsEncoding = "UTF8" #sys.getfilesystemencoding()
		#path = self.path.encode(fsEncoding)
		for root, dirs, files in os.walk(self.path):
			for file in files:
				m = self.filter.match(file)
				if m:
					item = FileItem(m.group(1), m.group(2), root)
					self.files.append(item)
