__author__ = 'bolay'

import re
from SourceMapperItem import *
from ScrapperItem import *


class FileFilter:
	def __init__(self, name=".*", extensions=[".*"]):
		self.name = name
		self.extensions = extensions

	def test(self, item):
		if re.search(re.escape(self.name), item.name, re.IGNORECASE) is None:
			return False
		for ext in self.extensions:
			if re.search(ext, item.extension, re.IGNORECASE) is not None:
				return True
		return False


class TorrentFilter:
	def __init__(self, nameFilters, authorFilter, size=None):
		"""
		:type size : dict
		:type authorFilter : str
		:type nameFilters : str
		:param nameFilters:
		:param authorFilter:
		:param size:
		"""
		self.nameFilters = nameFilters
		self.authorFilter = authorFilter
		self.sizeFilter = size

	def test(self, torrent):
		accepted = False
		for nameFilter in self.nameFilters:
			#print "TorrentFilter: test pattern, ", nameFilter, " in ", torrent.title,
			if re.search(nameFilter, torrent.title, re.IGNORECASE) is not None:
				accepted = True
				#	print " return True"
				break
			#else:
			#	print " return False"
		if len(self.authorFilter) != 0:
			#print "TorrentFilter: test pattern, ", self.authorFilter, " in ", torrent.author,
			if re.search(self.authorFilter, torrent.author, re.IGNORECASE) is None:
				accepted &= False
			#	print " return False"
			else:
			#	print " return True"
				accepted &= True
		if self.sizeFilter is not None:
			if "gt" in self.sizeFilter:
				accepted &= torrent.size >= self.sizeFilter["gt"]
			if "lt" in self.sizeFilter:
				accepted &= torrent <= self.sizeFilter["lt"]
		return accepted