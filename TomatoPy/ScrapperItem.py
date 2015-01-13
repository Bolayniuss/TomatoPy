__author__ = 'bolay'

import re


class EpisodeItem(object):

	def __init__(self, title, tvShow=None, season=None, episodeNumber=None, torrentItem=None):
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

		self.torrentProvided = (torrentItem is not None)
		self.torrentItem = torrentItem

	@staticmethod
	def buildFromFullName(fullName, torrentItem=None):
		m = re.match(r"^(.*?) *S0?(\d+)E0?(\d+)|^(.*?) *0?(\d+) ?x ?0?(\d+)", fullName)
		if m:
			if m.group(1) is None:
				return EpisodeItem(fullName, m.group(4), m.group(5), m.group(6), torrentItem)
			return EpisodeItem(fullName, m.group(1), int(m.group(2)), int(m.group(3)), torrentItem)

	def __str__(self):
		if not self.torrentProvided:
			return "%s: %s [%sx%s]" % (self.tvShow, self.title, self.season, self.episodeNumber)
		return "%s: %s [%sx%s]\n\t%s" % (self.tvShow, self.title, self.season, self.episodeNumber, self.torrentItem)


class TorrentItem(object):

	def __init__(self, url="", name="", seeds=0, leeches=0, size=0., date="", link="", isMagnetLink=False, author="", title=""):
		self.url = url
		self.name = name
		self.seeds = seeds
		self.leeches = leeches
		self.size = size
		self.date = date
		self.link = link
		self.isMagnetLink = isMagnetLink
		self.author = author
		self.title = title

	def __unicode__(self):
		return "%s [%s](%s), s:%d, l:%d" % (self.title, self.author, self.size, self.seeds, self.leeches, )

	def __str__(self):
		return "%s [%s](%s), s:%d, l:%d" % (self.title, self.author, self.size, self.seeds, self.leeches, )
