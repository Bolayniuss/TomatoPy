__author__ = 'bolay'


class EpisodeItem:

	def __init__(self, title, tvShow=None, season=None, episodeNumber=None):
		self.title = title
		self.tvShow = tvShow
		self.season = season
		self.episodeNumber = episodeNumber

	#TODO: fill method
	@staticmethod
	def buildFromFullName(fullName):
		pass


class TorrentItem:

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


class BetaserieRSSFeedItem:

	def __init__(self):
		self.title = ""
		self.content = ""
		self.published = ""
		self.filter = None
		self.tvShow = ""