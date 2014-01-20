# -*- coding: utf8 -*-
__author__ = 'bolay'

import os
from TomatoPy.Filters import *
from TomatoPy.SourceMapperItem import *


class DirectoryMapper:

	def __init__(self, path, filter=FileFilter()):
		self.path = u""+path
		self.filter = filter
		self.files = []
		self.map()

	def map(self):
		for root, dirs, files in os.walk(self.path):
			for file in files:
				print(file)
				item = FileItem(file, root)
				if self.filter.test(item):
					self.files.append(item)


