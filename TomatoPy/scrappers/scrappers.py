# -*- coding: utf8 -*-
#
import multi_host

__author__ = 'bolay'

import requests

import urllib2
import urllib
import re
import logging

from operator import attrgetter

import bs4

from .items import TorrentItem, EpisodeItem
from TomatoPy.filters import TorrentFilter
from multi_host import MultiHostHandler, MultiHostHandlerException, Host

TAG_RE = re.compile(r'<[^>]+>')
SPECIAL_RE = re.compile(r'[()]')


def remove_html_tags(text):
    return TAG_RE.sub('', text)


def sub_special_tags(text, sub_text=" "):
    return SPECIAL_RE.sub(sub_text, text)


def prescaler_converter(prescaler):
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


class EpisodesProvider(object):
    """
    Abstract class providing structure for object that provide tv show episodes.
    """

    def __init__(self):
        pass

    def get_episodes(self):
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

    def grab_torrents(self, search):
        """
        Abstract method that must fill torrentItems.
        """
        raise NotImplementedError

    def get_torrents(self, search, filter_=None, ordering_keys=None):
        """
        Returns a list of torrent (TorrentItem). Optional filter and ordering keys can be provided for sorting and
        filtering the list.
        :param search:
        :param filter_: filter object
        :type filter_: TorrentFilter
        :param ordering_keys: tuple of ordering keys
        :type ordering_keys: tuple
        :return: An ordered and filtered list of torrents
        :rtype: list
        """
        self.grab_torrents(search)
        torrent_list = self._torrentItems
        if filter_:
            torrent_list = self.filter(filter_)
        if ordering_keys:
            torrent_list = sorted(torrent_list, key=attrgetter(*ordering_keys))
        return torrent_list

    def filter(self, filter_):
        """
        Returns filtered version of torrentItems attribute using filter_ as filter. The new list is composed of elements
        that have passed filter_.test().
        :param filter_: the filter
        :type filter_: TorrentFilter
        """
        valid_torrent_items = []
        results = []
        for torrent_item in self._torrentItems:
            filter_result = filter_.test(torrent_item)
            if filter_.test(torrent_item) == filter_.TEST_OK:
                valid_torrent_items.append(torrent_item)
            results.append((torrent_item, filter_result))
        if not valid_torrent_items:
            self.logger.debug("No valid torrents Found, test results:")
            for result in results:
                torrent, flag = result
                if flag & TorrentFilter.TEST_FAILED_AUTHOR_NO_MATCH:
                    self.logger.debug("%s: no matches in author regex (%s) => (%s)", torrent.title, torrent.author,
                                      filter_.author_filter)
                elif flag & TorrentFilter.TEST_FAILED_NAME_NO_MATCH:
                    self.logger.debug("%s: no matches in title regexs (%s) => (%s)", torrent.title, torrent.title,
                                      ", ".join(filter_.name_filters))
                elif flag & TorrentFilter.TEST_FAILED_SIZE_TOO_BIG:
                    self.logger.debug("%s: size too big (%d bytes) => (%d)", torrent.title, torrent.size,
                                      filter_.size_filter["lt"])
                elif flag & TorrentFilter.TEST_FAILED_SIZE_TOO_SMALL:
                    self.logger.debug("%s: size too small (%d bytes) => (%d)", torrent.title, torrent.size,
                                      filter_.size_filter["gt"])
                else:
                    self.logger.debug("%s: OK", torrent.title)
        return valid_torrent_items


class TPBScrapper(TorrentProvider):
    timeout = 10

    def __init__(self, ):
        super(TPBScrapper, self).__init__()
        self.logger = logging.getLogger(__name__)

    def grab_torrents(self, search_string):
        self._torrentItems = []
        data = self.get_source(search_string)
        if data:
            self.parse(data)

    def get_source(self, search_string):
        try:
            return MultiHostHandler.Instance().open_url(
                "https://thepiratebay.org/search/" + urllib.quote(sub_special_tags(search_string)) + "/0/7/0",
                self.timeout)
        except MultiHostHandlerException as e:
            #print e
            self.logger.warning(e)
        return None

    def parse(self, data):

        soup = bs4.BeautifulSoup(data, "lxml")
        _torrents = soup.select("tr div.detName")

        for each_torrent in _torrents:
            each_torrent = each_torrent.parent.parent
            item = TorrentItem()
            item.link = each_torrent.find("a", href=re.compile("^magnet"))["href"]
            item.title = remove_html_tags(unicode(each_torrent.find("a", class_="detLink").string))
            text_tag = each_torrent.find("font")
            tds = each_torrent.find_all("td")
            item.seeds = int(tds[2].text)
            item.leeches = int(tds[3].text)
            reg = re.compile(".* (\d[\d.]*).*?([BkKmMgG])(iB|.?).*")
            m = reg.match(text_tag.text)
            item.size = float(m.group(1))
            item.author = unicode(text_tag.find(["a", "i"]).string)
            prescaler = m.group(2).upper()

            item.size *= prescaler_converter(prescaler)

            self._torrentItems.append(item)


class KickAssTorrentScrapper(TorrentProvider):
    baseUrl = "kickass.to"
    path = "/usearch/%s/"
    timeout = 10

    def __init__(self, ):
        super(KickAssTorrentScrapper, self).__init__()
        self.logger = logging.getLogger(__name__)

    def grab_torrents(self, search_string):
        self._torrentItems = []
        data = None
        try:
            kickass = Host(self.baseUrl)
            data = kickass.open_path(self.path % urllib.quote(sub_special_tags(search_string)), "https", self.timeout)
        except urllib2.HTTPError as e:
            self.logger.warning("%s, url=%s", e, self.baseUrl % urllib.quote(sub_special_tags(search_string)))

        if data:
            self.parse(data, search_string)

    def parse(self, data, search_string):
        """

        """

        search_string = r"^" + search_string + r"[\s+]"

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

            item.size *= prescaler_converter(prescaler)

            if re.search(search_string, item.title, re.IGNORECASE) is not None:
                self._torrentItems.append(item)


class BetaserieRSSScrapper(EpisodesProvider):
    baseUrl = "https://www.betaseries.com/rss/episodes/all/"

    def __init__(self, user):
        super(BetaserieRSSScrapper, self).__init__()
        self.items = []
        self.rss_feed_user = user

    def parse(self):
        url = self.baseUrl + self.rss_feed_user

        logging.info("Fetching episodes from %s", url)

        resp = requests.get(url)

        soup = bs4.BeautifulSoup(resp.text, "xml")

        _items = soup.find_all("entry")
        for each_item in _items:
            title = unicode(each_item.find("title").string)
            # item.content = unicode(eachItem.content.string)
            #item.published = unicode(eachItem.published.string)
            #item.filter = None
            self.items.append(EpisodeItem.build_from_fullname(title))

    def get_episodes(self):
        """
        :rtype: list of EpisodeItem
        """
        self.parse()
        return self.items


class ShowRSSScrapper(EpisodesProvider):
    baseUrl = "http://showrss.info/rss.php?user_id=%s&hd=1&proper=1&raw=true"

    def __init__(self, user_id):
        super(ShowRSSScrapper, self).__init__()
        self.items = []
        self.user_id = user_id

    def get_episodes(self):
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
            torrent_item = TorrentItem(link=item.find("link").text, title=title)
            self.items.append(EpisodeItem.build_from_fullname(title, torrent_item))

