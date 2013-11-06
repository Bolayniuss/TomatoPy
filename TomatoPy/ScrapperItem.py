__author__ = 'bolay'

class TorrentItem:
	url = ""
	name = ""
	seeds = ""
	leeches = ""
	size = ""
	date = ""
	link = ""
	isMagnetLink = False
	author = ""
	title = ""

	def __init__(self):
		self.url = ""

class BetaserieRSSFeedItem:
	title = ""
	content = ""
	published = ""