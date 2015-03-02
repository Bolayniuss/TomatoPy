# -*- coding: utf8 -*-
#
import MultiHostHandler

__author__ = 'bolay'

import urllib2
import urllib
import re
import logging

from operator import attrgetter

import bs4

from .ScrapperItem import TorrentItem, EpisodeItem
from .Filters import TorrentFilter
from MultiHostHandler import MultiHostHandler, MultiHostHandlerException, Host

TAG_RE = re.compile(r'<[^>]+>')
SPECIAL_RE = re.compile(r'[()]')


def remove_html_tags(text):
    return TAG_RE.sub('', text)


def sub_special_tags(text, sub_text=" "):
    return SPECIAL_RE.sub(sub_text, text)


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
                    self.logger.debug("%s: no matches in author regex (%s) => (%s)", torrent.title, torrent.author,
                                      filter_.authorFilter)
                elif flag & TorrentFilter.TEST_FAILED_NAME_NO_MATCH:
                    self.logger.debug("%s: no matches in title regexs (%s) => (%s)", torrent.title, torrent.title,
                                      ", ".join(filter_.nameFilters))
                elif flag & TorrentFilter.TEST_FAILED_SIZE_TOO_BIG:
                    self.logger.debug("%s: size too big (%d bytes) => (%d)", torrent.title, torrent.size,
                                      filter_.sizeFilter["lt"])
                elif flag & TorrentFilter.TEST_FAILED_SIZE_TOO_SMALL:
                    self.logger.debug("%s: size too small (%d bytes) => (%d)", torrent.title, torrent.size,
                                      filter_.sizeFilter["gt"])
                else:
                    self.logger.debug("%s: OK", torrent.title)
        return validTorrentItems


class TPBScrapper(TorrentProvider):
    timeout = 10

    def __init__(self, ):
        super(TPBScrapper, self).__init__()
        self.logger = logging.getLogger(__name__)
        self._torrentItems = []

    def grabTorrents(self, searchString):
        self._torrentItems = []
        data = self.getTPB_HTML(searchString)
        if data:
            self.parse(data)

    def getTPB_HTML(self, searchString):
        try:
            return MultiHostHandler.Instance().openURL(
                "https://thepiratebay.se/search/" + urllib.quote(sub_special_tags(searchString)) + "/0/7/0",
                self.timeout)
        except MultiHostHandlerException as e:
            #print e
            self.logger.warning(e)
        return None

    def parse(self, data):
        """


        """

        soup = bs4.BeautifulSoup(data)
        _torrents = soup.select("tr div.detName")

        for eachTorrent in _torrents:
            eachTorrent = eachTorrent.parent.parent
            item = TorrentItem()
            item.link = eachTorrent.find("a", href=re.compile("^magnet"))["href"]
            item.title = remove_html_tags(unicode(eachTorrent.find("a", class_="detLink").string))
            textTag = eachTorrent.find("font")
            tds = eachTorrent.find_all("td")
            item.seeds = int(tds[2].text)
            item.leeches = int(tds[3].text)
            reg = re.compile(".* ([\d.]+).*?([BkKmMgG])(iB|.?).*")
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


class KickAssTorrentScrapper(TorrentProvider):
    baseUrl = "kickass.to"
    path = "/usearch/%s/"
    timeout = 10

    def __init__(self, ):
        super(KickAssTorrentScrapper, self).__init__()
        self.logger = logging.getLogger(__name__)
        self._torrentItems = []

    def grabTorrents(self, searchString):
        self._torrentItems = []
        data = None
        try:
            kickass = Host(self.baseUrl)
            data = kickass.openPath(self.path % urllib.quote(sub_special_tags(searchString)), "https", self.timeout)
        except urllib2.HTTPError as e:
            self.logger.warning("%s, url=%s", e, self.baseUrl % urllib.quote(sub_special_tags(searchString)))

        if data:
            self.parse(data, searchString)

    def parse(self, data, searchString):
        """

        """

        searchString = r"^" + searchString + r"[\s+]"

        soup = bs4.BeautifulSoup(data)
        # print data
        selectors = soup.select("div.torrentname")

        #self.logger.debug("%s", selectors)

        for selector in selectors:

            torrent = selector.parent.parent
            item = TorrentItem()
            item.link = torrent.find("a", href=re.compile(r"^magnet"))["href"]
            item.title = unicode(torrent.find("a", class_="cellMainLink").text)
            tds = torrent.find_all("td")
            item.seeds = int(tds[4].text)
            item.leeches = int(tds[5].text)
            reg = re.compile("([\d.]+).*?([BkKmMgG])(iB|.?).*")
            m = reg.match(tds[1].text)
            item.size = float(m.group(1))

            author = torrent.find("a", href=re.compile(r"^/user/"))
            if author:
                item.author = unicode(author.text)
            prescaler = m.group(2).upper()

            item.size *= self.prescalerConverter(prescaler)

            if re.search(searchString, item.title, re.IGNORECASE) is not None:
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
        url = self.baseUrl + self.rssFeedUser
        page = urllib2.urlopen(url)
        soup = bs4.BeautifulSoup(page.read(), "xml")

        _items = soup.find_all("entry")
        for eachItem in _items:
            title = unicode(eachItem.find("title").string)
            # item.content = unicode(eachItem.content.string)
            #item.published = unicode(eachItem.published.string)
            #item.filter = None
            self.items.append(EpisodeItem.buildFromFullName(title))

    def getEpisodes(self):
        self.parse()
        return self.items


class ShowRSSScrapper(EpisodesProvider):
    baseUrl = "http://showrss.info/rss.php?user_id=%s&hd=1&proper=1&raw=true"

    def __init__(self, user_id):
        self.items = []
        self.user_id = user_id

    def getEpisodes(self):
        self.parse()
        return self.items

    def parse(self):
        """
        """
        url = self.baseUrl % self.user_id
        page = urllib2.urlopen(url)
        soup = bs4.BeautifulSoup(page.read(), "xml")

        items = soup.find_all("item")

        for item in items:
            title = item.find("title").text
            torrentItem = TorrentItem(link=item.find("link").text, title=title)
            self.items.append(EpisodeItem.buildFromFullName(title, torrentItem))



