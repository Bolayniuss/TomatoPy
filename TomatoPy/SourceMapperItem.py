__author__ = 'bolay'

import re
import os


class SourceMapperItem:
	def __init__(self):
		self.name = ""
		self.source = ""


class FileItem(SourceMapperItem):

	def __init__(self, filename, extension, path):
		self.filename = filename + "." + extension
		self.extension = extension
		self.name = filename
		self.source = path

	def getFullPath(self):
		return os.path.join(self.source, self.filename)

	@staticmethod
	def fromFilename(filename, path):
		"""
		:type filename: str
		:type path: str
		"""
		try:
			p = filename.rindex(".")
			return FileItem(filename[0:p], filename[p + 1:], path)
		except ValueError:
			return FileItem(filename, "", path)

	@staticmethod
	def fromCompletePath(path):
		filename = os.path.basename(path)
		directory = os.path.dirname(path)
		return FileItem.fromFilename(filename, directory)
