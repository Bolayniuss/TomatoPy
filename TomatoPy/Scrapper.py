__author__ = 'bolay'

import urllib2
import urllib
import re

import bs4

from TomatoPy.ScrapperItem import *


class TPBScrapper:
	searchString = ""
	torrents = []
	error = False

	def __init__(self, searchString):
		self.searchString = searchString
		self.parse()

	def parse(self):
		url = "http://thepiratebay.sx/search/" + urllib.quote(self.searchString) + "/0/7/0"
		page = urllib2.urlopen(url)
		soup = bs4.BeautifulSoup(page.read())
		_torrents = soup.select("tr div.detName")
		print url
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
			item.size = m.group(1)
			item.author = unicode(textTag.find(["a", "i"]).string)
			prescaler = m.group(2)
			item.size *= self.prescalerConverter(prescaler)
			print item.title, item.size, item.seeds, item.author
			self.torrents.append(item);

	def prescalerConverter(self, prescaler):
		if prescaler is "T":
			return 1000000000000
		elif prescaler is "G":
			return 1000000000
		elif prescaler is "M":
			return 1000000
		elif prescaler is "K":
			return 1000
		return 1


class BetaserieRSSScrapper:
	items = []
	rssFeedUser = ""

	def __init__(self, user):
		self.rssFeedUser = user
		self.parse()

	def parse(self):
		url = "http://www.betaseries.com/rss/episodes/all/"+self.rssFeedUser
		page = urllib2.urlopen(url)
		soup = bs4.BeautifulSoup(page.read(), "xml")

		_items = soup.find_all("entry")
		for eachItem in _items:
			item = BetaserieRSSFeedItem()
			item.title = unicode(eachItem.find("title").string)
			item.content = unicode(eachItem.content.string)
			item.published = unicode(eachItem.published.string)
			print item.published, item.title, item.content
			self.items.append(item)

