__author__ = 'bolay'

import re


class FileFilter:
	def __init__(self, name=".*", extensions=[".*"]):
		self.name = name
		self.extensions = extensions

	def test(self, item):
		if re.search(self.name, item.name, re.IGNORECASE) is None:
			return False
		for ext in self.extensions:
			if re.search(ext, item.extension, re.IGNORECASE) is not None:
				return True
		return False


class TorrentFilter:
	TEST_OK = 0
	TEST_FAILED_SIZE_TOO_BIG = 1
	TEST_FAILED_SIZE_TOO_SMALL = 2
	TEST_FAILED_AUTHOR_NO_MATCH = 4
	TEST_FAILED_NAME_NO_MATCH = 8

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
		status = self.TEST_OK
		for nameFilter in self.nameFilters:
			#print "TorrentFilter: test pattern, ", nameFilter, " in ", torrent.title,
			if re.search(nameFilter, torrent.title, re.IGNORECASE) is not None:
				accepted = True
				break
		if not accepted:
			status |= self.TEST_FAILED_NAME_NO_MATCH
		accepted = False
		if len(self.authorFilter) != 0:
			#print "TorrentFilter: test pattern, ", self.authorFilter, " in ", torrent.author,
			if re.search(self.authorFilter, torrent.author, re.IGNORECASE) is None:
				accepted = False
		if not accepted:
			status |= self.TEST_FAILED_AUTHOR_NO_MATCH
		accepted = False
		if self.sizeFilter is not None:
			if "gt" in self.sizeFilter:
				accepted = torrent.size >= self.sizeFilter["gt"]
			if not accepted:
				status |= self.TEST_FAILED_SIZE_TOO_SMALL

			if "lt" in self.sizeFilter:
				accepted = torrent.size <= self.sizeFilter["lt"]
				if not accepted:
					status |= self.TEST_FAILED_SIZE_TOO_BIG
		return status