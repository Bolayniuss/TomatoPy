# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import re


class EpisodeItem(object):
    def __init__(self, title, tv_show=None, season=None, episode_number=None, torrent_item=None):
        """
        :param unicode title:
        :param unicode tv_show:
        :param int season:
        :param int episode_number:
        :return:
        """
        self.title = title
        self.tv_show = tv_show
        self.season = season
        self.episode_number = episode_number

        self.torrent_provided = (torrent_item is not None)
        self.torrent_item = torrent_item


    @staticmethod
    def build_from_fullname(full_name, torrent_item=None):
        m = re.match(r"^(.*?) *S0?(\d+)E0?(\d+)|^(.*?) *0?(\d+) ?x ?0?(\d+)", full_name)
        if m:
            if m.group(1) is None:
                return EpisodeItem(full_name, m.group(4), int(m.group(5)), int(m.group(6)), torrent_item)
            return EpisodeItem(full_name, m.group(1), int(m.group(2)), int(m.group(3)), torrent_item)

    def __str__(self):
        if not self.torrent_provided:
            return "%s: %s [%sx%s]" % (self.tv_show, self.title, self.season, self.episode_number)
        return "%s: %s [%sx%s]\n\t%s" % (self.tv_show, self.title, self.season, self.episode_number, self.torrent_item)


class TorrentItem(object):
    def __init__(self, url="", name="", seeds=0, leeches=0, size=0., date="", link="", is_magnet_link=False, author="",
                 title=""):
        self.url = url
        self.name = name
        self.seeds = seeds
        self.leeches = leeches
        self.size = size
        self.date = date
        self.link = link
        self.is_magnet_link = is_magnet_link
        self.author = author
        self.title = title

    def __unicode__(self):
        return "%s [%s](%s), s:%d, l:%d" % (self.title, self.author, self.size, self.seeds, self.leeches,)

    def __str__(self):
        return "%s [%s](%s), s:%d, l:%d" % (self.title, self.author, self.size, self.seeds, self.leeches,)
