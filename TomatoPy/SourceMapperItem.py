__author__ = 'bolay'

import re
import os


class SourceMapperItem:
	def __init__(self):
		self.name = ""
		self.source = ""


class FileItem(SourceMapperItem):

	def __init__(self, filename, path):
		self.filename = filename
		m = re.compile(r"(.*)\.([^.]*)").match(filename)
		if m is None:
			self.extension = ""
			self.name = filename
		else:
			self.name = m.group(1)
			self.extension = m.group(2)
		self.source = path

	def getFullPath(self):
		return os.path.join(self.source, self.filename)

	@staticmethod
	def fromCompletePath(path):
		filename = os.path.basename(path)
		directory = os.path.dirname(path)
		return FileItem(filename, directory)
