__author__ = 'bolay'

import re


class SourceMapperItem:
	def __init__(self):
		self.name = ""
		self.source = ""


class FileItem(SourceMapperItem):
	extension = ""

	def __init__(self, filename, path):
		m = re.compile(r"(.*)\.([^.]*)").match(filename)
		if m is None:
			self.extension = ""
			self.name = filename
		else:
			self.name = m.group(1)
			self.extension = m.group(2)
		self.source = path
