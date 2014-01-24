# -*- coding: utf8 -*-
__author__ = 'bolay'

import os
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
				item = FileItem(file, root)
				if self.filter.test(item):
					self.files.append(item)
