__author__ = 'bolay'

import urllib2
import urllib
import re
import logging

from operator import attrgetter

import bs4

from .ScrapperItem import TorrentItem, BetaserieRSSFeedItem
from .Filters import TorrentFilter


class EpisodesProvider:
	"""
	Abstract class providing structure for object that provide tv show episodes.
	"""
	def __init__(self):
		pass

	def getEpisodes(self):
		"""
		Must returns a list of episodes provided by this source
		:return: a list of episodes
		:rtype: list
		"""
		raise NotImplementedError


class TorrentProvider:
	"""
	Abstract class providing structure for object that provide torrent file/item
	"""
	def __init__(self):
		self.torrentItems = []
		pass

	def grabTorrents(self):
		"""
		Abstract method that must fill torrentItems.
		"""
		raise NotImplementedError

	def getTorrents(self, filter_=None, orderingKeys=None):
		"""
		Returns a list of torrent (TorrentItem). Optional filter and ordering keys can be provided for sorting and
		filtering the list.
		:param filter_: filter object
		:type filter_: TorrentFilter
		:param orderingKeys: tuple of ordering keys
		:type orderingKeys: tuple
		:return: An ordered and filtered list of torrents
		:rtype: list
		"""
		self.grabTorrents()
		tList = self.torrentItems
		if filter_:
			tList = self.filter(filter_)
		if orderingKeys:
			tList = sorted(tList, key=attrgetter(*orderingKeys))
		return tList

	def filter(self, filter_):
		"""
		Returns filtered version of torrentItems attribute using filter_ as filter. The new list is composed of elements
		that have passed filter_.test().
		:param filter_: the filter
		:type filter_: TorrentFilter
		"""
		validTorrentItems = []
		for torrentItem in self.torrentItems:
			if filter_.test(torrentItem):
				validTorrentItems.append(torrentItem)
		return validTorrentItems


class TPBScrapper:

	def __init__(self, searchString, filter=None):
		self.logger = logging.getLogger(__name__)
		self.torrents = []
		self.searchString = searchString
		self.filter = filter
		self.parse()

	def parse(self):
		url = "http://thepiratebay.se/search/" + urllib.quote(self.searchString) + "/0/7/0"
		page = urllib2.urlopen(url)
		soup = bs4.BeautifulSoup(page.read())
		_torrents = soup.select("tr div.detName")
		for eachTorrent in _torrents:
			eachTorrent = eachTorrent.parent.parent
			item = TorrentItem()
			item.link = eachTorrent.find("a", href=re.compile("^magnet"))["href"]
			item.title = unicode(eachTorrent.find("a", class_="detLink").string)
			textTag = eachTorrent.find("font")
			tds = eachTorrent.find_all("td")
			item.seeds = tds[2].text
			item.leeches = tds[3].text
			reg = re.compile(".* ([\d.]+).*?([kKmMgG])iB.*")
			m = reg.match(textTag.text)
			item.size = float(m.group(1))
			item.author = unicode(textTag.find(["a", "i"]).string)
			prescaler = m.group(2).upper()

			item.size *= self.prescalerConverter(prescaler)
			if self.filter is not None:
				if self.filter.test(item):
					self.torrents.append(item)
			else:
				self.torrents.append(item)

	def prescalerConverter(self, prescaler):
		if prescaler == "T":
			return 1000000000000
		elif prescaler == "G":
			return 1000000000
		elif prescaler == "M":
			return 1000000
		elif prescaler == "K":
			return 1000
		return 1


class BetaserieRSSScrapper:

	baseurl = "http://www.betaseries.com/rss/episodes/all/"

	def __init__(self, user):
		self.items = []
		self.rssFeedUser = user
		self.parse()

	def parse(self):
		url = self.baseurl+self.rssFeedUser
		page = urllib2.urlopen(url)
		soup = bs4.BeautifulSoup(page.read(), "xml")

		_items = soup.find_all("entry")
		for eachItem in _items:
			item = BetaserieRSSFeedItem()
			item.title = unicode(eachItem.find("title").string)
			item.content = unicode(eachItem.content.string)
			item.published = unicode(eachItem.published.string)
			item.filter = None
			self.items.append(item)

