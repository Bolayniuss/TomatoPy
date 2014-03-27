# -*- coding: utf8 -*-
__author__ = 'bolay'

import os
import re
import sys

from .Filters import *
from .SourceMapperItem import *

#old class
#class DirectoryMapper:
#
#	def __init__(self, path, filter=FileFilter(), encoding=None):
#		self.path = path
#		if encoding is not None:
#			self.path = path.encode(encoding)
#		self.filter = filter
#		self.files = []
#		self.map()
#
#	def map(self):
#		reload(sys)
#		sys.setdefaultencoding('UTF8')
#		fsEncoding = "UTF8" #sys.getfilesystemencoding()
#		#path = self.path.encode(fsEncoding)
#		for root, dirs, files in os.walk(self.path):
#			for file in files:
#				#file = file.decode(fsEncoding)
#				#root = root.decode(fsEncoding)
#				#print file, type(file)
#				item = FileItem.fromFilename(file, root)
#				if self.filter.test(item):
#					self.files.append(item)


class DirectoryMapper:

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

	def fileExists(self, file_):
		loweredFile = file_.lower()
		key = loweredFile[0]
		if key in self.indexedFiles:
			for item in self.indexedFiles[key]:
				if item.name.lower() == loweredFile:
					return True
		return False