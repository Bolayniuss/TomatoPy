__author__ = 'bolay'


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