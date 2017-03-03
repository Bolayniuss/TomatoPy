# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

from TomatoPy.api.torrents import TorrentContent

import requests

import urllib2
import urllib
import re
import logging

from operator import attrgetter

import bs4

from TomatoPy.api.torrents.utils import magnet_from_data
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
        search = search.encode("utf-8")
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
            self.logger.debug("No valid torrents Found, test results [%d]:", len(results))
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
                "https://thepiratebay.se/search/" + urllib.quote(sub_special_tags(search_string)) + "/0/7/0",
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
            tds = each_torrent.find_all("td")
            text_tag = each_torrent.find("font")
            m = re.match(r".* (\d[\d.]*).*?([BkKmMgG])(iB|.?).*", text_tag.text)
            prescaler = prescaler_converter(m.group(2).upper())

            size = float(m.group(1)) * prescaler
            magnet = each_torrent.find("a", href=re.compile("^magnet"))["href"]

            item = TorrentItem(
                link=magnet,
                title=remove_html_tags(each_torrent.find("a", class_="detLink").string),
                seeds=int(tds[2].text),
                leeches=int(tds[3].text),
                size=size,
                author=text_tag.find(["a", "i"]).string,
            )

            item.size *= prescaler_converter(prescaler)
            item.content = TorrentContent(magnet, ctype=TorrentContent.TYPE_MAGNET)

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

        soup = bs4.BeautifulSoup(data, "lxml")
        # print data
        selectors = soup.select("div.torrentname")

        #self.logger.debug("%s", selectors)

        for selector in selectors:

            torrent = selector.parent.parent

            tds = torrent.find_all("td")
            m = re.match(r"([\d.]+).*?([BkKmMgG])(iB|.?).*", tds[1].text)
            prescaler = prescaler_converter(m.group(2).upper())

            magnet = torrent.find("a", href=re.compile(r"^magnet"))["href"]
            size = float(m.group(1)) * prescaler

            item = TorrentItem(
                link=magnet,
                title=torrent.find("a", class_="cellMainLink").text,
                seeds=int(tds[4].text),
                leeches=int(tds[5].text),
                size=size,
                author=torrent.find("a", href=re.compile(r"^/user/")) or "",
                content=TorrentContent(magnet, ctype=TorrentContent.TYPE_MAGNET),
            )

            if re.search(search_string, item.title, re.IGNORECASE) is not None:
                self._torrentItems.append(item)


# get torrent
def content_getter_closure(scrapper, it, id):
    def content_getter():
        scrapper.logger.debug("Download torrent: item.title=%s, id=%s", it.title, id)
        resp = scrapper.session.get(url=scrapper.host + scrapper.download_url, params=dict(id=id))
        if resp.ok:
            torrent_data = resp.content

            # convert to magnet
            magnet = magnet_from_data(torrent_data)
            it.link = magnet
            return TorrentContent(torrent_data, ctype=TorrentContent.TYPE_DATA)
    return content_getter


class T411Scrapper(TorrentProvider):
    """
    <tr>
        <td valign="center">
            <a href="/torrents/search/?subcat=433">
                <i class="categories-icons category-spline-video-tv-series"></i>
            </a>
        </td>
        <td valign="center">
            <a href="//www.t411.li/torrents/un-village-franais-s06e06-hd-1080p-french-fb" title="Un.village.français.S06E06.HD.1080p.FRENCH.FB">Un.village.français.S06E06.HD.1080p.FRENCH.FB&nbsp;<span class="up">(A)</span></a>
            <a href="#" class="switcher alignright"></a>
                                <a href="http://www.xmediaserve.com/apu.php?n=&zoneid=16673&direct=1&lcat=download&q=Un.village.fran%C3%A7ais.S06E06.HD.1080p.FRENCH.FB"><img src="http://i.imgur.com/wbD6VXb.png" alt="" /></a>
                                            <dl>
                <dt>Ajout&#233; le:</dt>
                <dd>2015-10-11 14:19:42 (+00:00)</dd>
                <dt>Ajout&#233; par:</dt>
                <dd><a href="/users/profile/GCDomlol86" title="GCDomlol86" class="profile">GCDomlol86</a></dd>
                <dt>Status:</dt>
                <dd><strong class="up">BON</strong> &mdash; Ce torrent est actif (<strong>77</strong> seeders et <strong>0</strong> leechers) et devrait &#281;tre t&#233;l&#233;charg&#233; rapidement</dd>
            </dl>
        </td>
        <td>
            <a href="/torrents/nfo/?id=5390527" class="ajax nfo"></a>
        </td>
        <td align="center">9</td>
        <td align="center">1 an</td>
        <td align="center">2.02 GB</td>
        <td align="center">1782</td>
        <td align="center" class="up">77</td>
        <td align="center" class="down">0</td>
    </tr>
    """

    host = "https://www.t411.li"

    login_url = "/users/login/"
    search_url = "/torrents/search/"     # GET search=str, cat=210, name=un+village+français, user=uploader, &order=seeders&type=desc
    download_url = "/torrents/download/"  # GET id=id

    timeout = 10

    def __init__(self, user, password):
        super(T411Scrapper, self).__init__()
        self.logger = logging.getLogger(__name__)

        self.session = requests.Session()
        self.session.post(url=self.host+self.login_url, data=dict(login=user, password=password, url="/"))

    def grab_torrents(self, search_string):
        self._torrentItems = []
        source = None

        try:
            params = dict(
                search=urllib.quote_plus(search_string),
                order="seeder",
                type="desc",
                cat=210
            )
            resp = self.session.get(self.host+self.search_url, params=params, timeout=self.timeout)
            if resp.ok:
                source = resp.text
        except urllib2.HTTPError as e:
            self.logger.warning("%s, url=%s", e, self.baseUrl % urllib.quote(sub_special_tags(search_string)))

        if source:
            self.parse(source, search_string)

    def parse(self, data, search_string):
        """

        """

        search_string = r"^" + search_string + r"[\s+]"

        soup = bs4.BeautifulSoup(data, "lxml")

        self.logger.debug(data)

        selectors = soup.select("table.results tr")
        #selectors = results.select("tr")

        for torrent_tr in selectors:
            tds = torrent_tr.find_all("td", align="center")
            if tds:
                nfo_link = torrent_tr.find("a", class_=["ajax", "nfo"])["href"]

                re_id = re.search(r"\?id=(?P<id>\d+)", nfo_link)
                t411_id = re_id.group('id')

                m = re.match(r"([\d.]+).*?([BkKmMgG])(iB|.?).*", tds[2].text)
                prescaler = m.group(2).upper()
                size = float(m.group(1)) * prescaler_converter(prescaler)

                pre_author = torrent_tr.find("a", class_="profile")
                author = pre_author.text if pre_author else ""

                item = TorrentItem(
                    title=torrent_tr.find("a", href=re.compile(r"^//www\.t411\.li/torrents/")).text,
                    seeds=int(tds[4].text),
                    leeches=int(tds[5].text),
                    size=size,
                    author=author,
                )

                self.logger.debug("%s", item)

                if re.search(search_string, item.title, re.IGNORECASE) is not None:
                    item.content = content_getter_closure(self, item, t411_id)
                    self._torrentItems.append(item)
                else:
                    self.logger.debug("No match between %s and %s", item.title, search_string)


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
            title = each_item.find("title").string
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
            magnet = item.find("link").text
            torrent_item = TorrentItem(
                link=magnet,
                title=title,
                content=TorrentContent(magnet, ctype=TorrentContent.TYPE_MAGNET)
            )
            self.items.append(EpisodeItem.build_from_fullname(title, torrent_item))

