__author__ = 'bolay'

import urllib2
import urllib
import re
import logging

from operator import attrgetter

import bs4

from .ScrapperItem import TorrentItem, EpisodeItem
from .Filters import TorrentFilter


class EpisodesProvider(object):
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


class TorrentProvider(object):
	"""
	Abstract class providing structure for object that provide torrent file/item
	"""
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self._torrentItems = []
		pass

	def grabTorrents(self, search):
		"""
		Abstract method that must fill torrentItems.
		"""
		raise NotImplementedError

	def getTorrents(self, search, filter_=None, orderingKeys=None):
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
		self.grabTorrents(search)
		tList = self._torrentItems
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
		results = []
		for torrentItem in self._torrentItems:
			filterResult = filter_.test(torrentItem)
			if filter_.test(torrentItem) == filter_.TEST_OK:
				validTorrentItems.append(torrentItem)
			results.append((torrentItem, filterResult))
		if not validTorrentItems:
			self.logger.debug("No valid torrents Found, test results:")
			for result in results:
				torrent = result[0]
				flag = result[1]
				if flag & TorrentFilter.TEST_FAILED_AUTHOR_NO_MATCH:
					self.logger.debug("%s: no matches in author regex (%s)", torrent.title, torrent.author)
				elif flag & TorrentFilter.TEST_FAILED_NAME_NO_MATCH:
					self.logger.debug("%s: no matches in title regexs (%s)", torrent.title, torrent.author)
				elif flag & TorrentFilter.TEST_FAILED_SIZE_TOO_BIG:
					self.logger.debug("%s: size too big (%d bytes)", torrent.title, torrent.size)
				elif flag & TorrentFilter.TEST_FAILED_SIZE_TOO_SMALL:
					self.logger.debug("%s: size too small (%d bytes)", torrent.title, torrent.size)
				else:
					self.logger.debug("%s: OK", torrent.title)
		return validTorrentItems


class TPBScrapper(TorrentProvider):

	def __init__(self, ):
		super(TPBScrapper, self).__init__()
		self.logger = logging.getLogger(__name__)
		self._torrentItems = []

	def grabTorrents(self, searchString):
		self._torrentItems = []
		self.parse("http://thepiratebay.se/search/" + urllib.quote(searchString) + "/0/7/0")

	def parse(self, url):
		"""


		"""
		from StringIO import StringIO
		import gzip

		request = urllib2.Request('http://example.com/')
		request.add_header('Accept-encoding', 'gzip')
		response = urllib2.urlopen(request)
		if response.info().get('Content-Encoding') == 'gzip':
			buf = StringIO(response.read())
			f = gzip.GzipFile(fileobj=buf)
			data = f.read()
		else:
			data = response.read()
		soup = bs4.BeautifulSoup(data)
		_torrents = soup.select("tr div.detName")
		print _torrents
		for eachTorrent in _torrents:
			print eachTorrent
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

			self._torrentItems.append(item)

	@staticmethod
	def prescalerConverter(prescaler):
		"""

		:param prescaler:
		:return:
		"""
		if prescaler == "T":
			return 1000000000000
		elif prescaler == "G":
			return 1000000000
		elif prescaler == "M":
			return 1000000
		elif prescaler == "K":
			return 1000
		return 1


class BetaserieRSSScrapper(EpisodesProvider):

	baseUrl = "http://www.betaseries.com/rss/episodes/all/"

	def __init__(self, user):
		self.items = []
		self.rssFeedUser = user

	def parse(self):
		url = self.baseUrl+self.rssFeedUser
		page = urllib2.urlopen(url)
		soup = bs4.BeautifulSoup(page.read(), "xml")

		_items = soup.find_all("entry")
		for eachItem in _items:
			title = unicode(eachItem.find("title").string)
			#item.content = unicode(eachItem.content.string)
			#item.published = unicode(eachItem.published.string)
			#item.filter = None
			self.items.append(EpisodeItem.buildFromFullName(title))

	def getEpisodes(self):
		self.parse()
		return self.items

