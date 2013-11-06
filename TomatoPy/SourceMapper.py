__author__ = 'bolay'

import os
from TomatoPy.Filters import *
from TomatoPy.SourceMapperItem import *


class DirectoryMapper:
	files = []
	path = ""
	filter

	def __init__(self, path, filter=FileFilter()):
		self.path = path
		self.filter = filter
		self.map()

	def map(self):
		for root, dirs, files in os.walk(self.path):
			for file in files:
				item = FileItem(file, root)
				if self.filter.test(item):
					self.files.append(item)


