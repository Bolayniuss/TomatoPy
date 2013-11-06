__author__ = 'bolay'

import re
from SourceMapperItem import *


class FileFilter:
	name = ""
	extensions = []

	def __init__(self, name=".*", extensions=[".*"]):
		self.name = name
		self.extensions = extensions

	def test(self, item):
		if re.search(self.name, item.name) is None:
			return False
		for ext in self.extensions:
			if re.search(ext, item.extension) is not None:
				return True
		return False


