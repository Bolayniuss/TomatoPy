# -*- coding: utf8 -*-
#
__author__ = 'bolay'

import logging
import os
import re

from database import DatabaseManager


class TorrentObject(object):
    """
    Object that represents a torrent (task)
    """

    def __init__(self, _hash, name):
        """

        :param str _hash:
        :param str name:
        """
        self.name = ""
        self.hash = ""
        self.size = ""

        self.isDownloaded = False
        self.magnetLink = None

        self.files = list()

        self.hash = _hash  # hashString	TORRENT_HASH: 0
        self.name = name  # name	TORRENT_NAME: 2
        self.eta = 0  # eta	TORRENT_ETA: 10
        self.size = 0  # sizeWhenDone	TORRENT_SIZE: 3
        self.downloaded = 0  # downloadedEver	TORRENT_DOWNLOADED: 5
        self.uploaded = 0  # uploadedEver	TORRENT_UPLOADED: 6
        self.seeders = 0  # peersSendingToUs	TORRENT_SEEDS_CONNECTED: 14
        self.totalSeeders = 0  # seeders	TORRENT_SEEDS_SWARM: 15
        self.peers = 0  # peersGettingFromUs	TORRENT_PEERS_CONNECTED: 12
        self.totalPeers = 0  # peersKnown	TORRENT_PEERS_SWARM: 13
        self.magnetLink = None  # magnetLink	create from torrent file
        self.torrentFilePath = ""  # torrentFile	/(dl dir)/_torrent_file/(torrentName).torrent
        self.ratio = 0  # uploadRatio	TORRENT_RATIO: 7
        self.dlRate = 0  # rateDownload (bps)	TORRENT_DOWNSPEED: 9
        self.ulRate = 0  # rateUpload (bps)	TORRENT_UPSPEED: 8
        self.isFinished = False  # percentDone == 1	(TORRENT_PROGRESS: 4) == 1'000'000

    def getProgress(self):
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
    def fromTorrentProp(tFile):
        if len(tFile) >= 5:
            return TorrentFile(tFile["name"], tFile["size"], tFile["completed"], tFile["priority"], tFile["selected"])
        return None


class TorrentManager(object):

    def __init__(self, parameters=None):
        self.logger = logging.getLogger(__name__)
        if parameters is None:
            query = "SELECT parameters FROM Parameters WHERE name='TorrentManager' LIMIT 1"
            DatabaseManager.Instance().cursor.execute(query)
            (parametersString,) = DatabaseManager.Instance().cursor.fetchone()
            parameters = parametersString.split("&&")
        self.downloadDirectory = parameters[0]
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
        if os.path.isfile(os.path.join(self.downloadDirectory, filename)):
            return os.path.join(self.downloadDirectory, filename)
        elif os.path.isfile(os.path.join(self.downloadDirectory, torrent_name, filename)):
            return os.path.join(self.downloadDirectory, torrent_name, filename)
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
        :rtype: list[TorrentObject]
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
        :rtype: list[TorrentFile]
        """
        raise NotImplementedError()

    def add_torrent(self, torrent_file_path):
        """

        :param str torrent_file_path:
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