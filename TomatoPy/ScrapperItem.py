__author__ = 'bolay'

import re


class EpisodeItem(object):

	def __init__(self, title, tvShow=None, season=None, episodeNumber=None):
		"""

		:param unicode title:
		:param unicode tvShow:
		:param int season:
		:param int episodeNumber:
		:return:
		"""
		self.title = title
		self.tvShow = tvShow
		self.season = season
		self.episodeNumber = episodeNumber

	@staticmethod
	def buildFromFullName(fullName):
		m = re.match(r"^(.*?) *S0?(\d+)E0?(\d+)", fullName)
		if m:
			return EpisodeItem(fullName, m.group(1), m.group(2), m.group(3))


class TorrentItem(object):

	def __init__(self):
		self.url = ""
		self.name = ""
		self.seeds = ""
		self.leeches = ""
		self.size = ""
		self.date = ""
		self.link = ""
		self.isMagnetLink = False
		self.author = ""
		self.title = ""
