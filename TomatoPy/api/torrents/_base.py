# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import logging
import os
import re

from database import DatabaseManager


def _torrent_type_str(type_):
    if type_ == TorrentContent.TYPE_MAGNET:
        return "TYPE_MAGNET"
    if type_ == TorrentContent.TYPE_DATA:
        return "TYPE_DATA"
    if type_ == TorrentContent.TYPE_FILE:
        return "TYPE_FILE"


class TorrentContent(object):
    TYPE_MAGNET = 0
    TYPE_DATA = 1
    TYPE_FILE = 2

    TYPES = [TYPE_MAGNET, TYPE_DATA, TYPE_FILE]

    def __init__(self, content, ctype):
        if ctype not in self.TYPES:
            raise ValueError("'ctype' as to be a valid torrent content type")
        self.content = content
        self.type = ctype

    def __str__(self):
        return "TorrentContent(type=%s, content=%s)" % (self.type, self.content)


class TorrentObject(object):
    """
    Object that represents a torrent (task)
    """

    def __init__(self, _hash, name):
        """

        :param str _hash:
        :param str name:
        """
        self.is_downloaded = False
        self.magnet_link = None

        self.files = list()

        self.hash = _hash  # hashString	TORRENT_HASH: 0
        self.name = name  # name	TORRENT_NAME: 2
        self.eta = 0  # eta	TORRENT_ETA: 10
        self.size = 0  # sizeWhenDone	TORRENT_SIZE: 3
        self.downloaded = 0  # downloadedEver	TORRENT_DOWNLOADED: 5
        self.uploaded = 0  # uploadedEver	TORRENT_UPLOADED: 6
        self.seeders = 0  # peersSendingToUs	TORRENT_SEEDS_CONNECTED: 14
        self.total_seeders = 0  # seeders	TORRENT_SEEDS_SWARM: 15
        self.peers = 0  # peersGettingFromUs	TORRENT_PEERS_CONNECTED: 12
        self.total_peers = 0  # peersKnown	TORRENT_PEERS_SWARM: 13
        self.magnet_link = None  # magnetLink	create from torrent file
        self.torrent_file_path = ""  # torrentFile	/(dl dir)/_torrent_file/(torrentName).torrent
        self.ratio = 0  # uploadRatio	TORRENT_RATIO: 7
        self.download_rate = 0  # rateDownload (bps)	TORRENT_DOWNSPEED: 9
        self.upload_rate = 0  # rateUpload (bps)	TORRENT_UPSPEED: 8
        self.is_finished = False  # percentDone == 1	(TORRENT_PROGRESS: 4) == 1'000'000

    def get_progress(self):
        if not self.size or self.size == 0:
            return 0
        return float(self.downloaded) / self.size


class TorrentFile:
    def __init__(self, name=None, size=None, completed=None, priority=None):
        """

        :param str name:
        :param int size:
        :param bool completed:
        :param int priority:
        """
        # FILE NAME (string),
        # FILE SIZE (integer, in bytes),
        # DOWNLOADED (integer, in bytes),
        # PRIORITY* (integer, {0 = Don't Download, 1 = Low Priority, 2 = Normal Priority, 3 = High Priority})

        self.name = name
        self.size = size
        self.completed = completed
        self.priority = priority  # '0:noDl'|'3:high'|'2:normal'|'1:low'

    @staticmethod
    def from_torrent_prop(torrent_file):
        if len(torrent_file) >= 5:
            return TorrentFile(
                torrent_file["name"],
                torrent_file["size"],
                torrent_file["completed"],
                torrent_file["priority"],
                # torrent_file["selected"]
            )
        return None


class TorrentManager(object):

    def __init__(self, parameters=None):
        self.logger = logging.getLogger(__name__)
        if parameters is None:
            query = "SELECT parameters FROM Parameters WHERE name='TorrentManager' LIMIT 1"
            DatabaseManager.Instance().cursor.execute(query)
            (parameters_string,) = DatabaseManager.Instance().cursor.fetchone()
            parameters = str(parameters_string).split("&&")
        self.download_directory = parameters[0]
        self.host = parameters[1]
        self.port = 9091
        self.user = None
        self.password = None
        if len(parameters) > 2:
            self.port = parameters[2]
        if len(parameters) > 3:
            self.user = parameters[3]
        if len(parameters) > 4:
            self.password = parameters[4]
        if len(parameters) > 5:
            self.init_with_extra_params(parameters[5:])

    def init_with_extra_params(self, extra_params):
        pass

    def get_torrent_file_path(self, torrent_name, filename):
        """

        :param str torrent_name:
        :param str filename:
        :return: path for the given torrent and filename
        :rtype: str
        """
        if os.path.isfile(os.path.join(self.download_directory, filename)):
            return os.path.join(self.download_directory, filename)
        elif os.path.isfile(os.path.join(self.download_directory, torrent_name, filename)):
            return os.path.join(self.download_directory, torrent_name, filename)
        self.logger.warn("no file found in %s with filename %s", torrent_name, filename)
        raise IOError("file not found")

    def search_in_torrents(self, pattern):
        """
        Test if the regular expression pattern match a torrent's name. If so return True, False otherwise.
        :param str pattern: The regular expression to test
        :return: True if pattern found in a torrent's name
        :rtype: bool
        """
        torrents = self.get_torrents()
        for torrent in torrents:
            if re.search(pattern, torrent.name, re.IGNORECASE) is not None:
                return True
        return False

    def get_torrents(self):
        """

        :return:
        :rtype: list of TorrentObject
        """
        raise NotImplementedError()

    def get_torrent(self, hash_):
        """

        :type hash_: str
        :rtype: TorrentObject | None
        """
        raise NotImplementedError()

    def get_torrent_files(self, torrent_hash):
        """

        :type torrent_hash: str
        :rtype: list of TorrentFile
        """
        raise NotImplementedError()

    def add_torrent(self, torrent_content):
        """

        :param TorrentContent torrent_content:
        :return:
        """
        raise NotImplementedError()

    def add_torrent_url(self, torrent_url):
        """

        :param str torrent_url:
        :return:
        """
        raise NotImplementedError()

    def remove_torrent(self, hash_, delete_data=False):
        raise NotImplementedError()
