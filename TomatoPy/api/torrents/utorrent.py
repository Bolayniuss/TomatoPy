# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import logging

from TomatoPy.api.torrents._base import TorrentManager, TorrentObject, TorrentFile
from UTorrent.UTorrent import UTorrent


class UTorrentRPC(TorrentManager):
    def __init__(self, host=None, port=9090, user="admin", password="", dlDirectory=""):
        self.logger = logging.getLogger(__name__)
        parameters = None
        if host is not None:
            parameters = [dlDirectory, host, port, user, password]
        super(UTorrentRPC, self).__init__(parameters)
        self.client = UTorrent(self.host, self.port, self.user, self.password)
        self.torrents = dict()

    def get_torrent(self, hash_):
        """
        Retrieve the torrent with hash

        :param hash_: the UID of the desired torrent
        :return: torrent
        :type hash_: str
        :rtype: TorrentRPC.TorrentObject
        """
        if hash_ not in self.torrents:
            self.get_torrents()
        return self.torrents[hash_]

    def get_torrents(self):
        """ Retrieve a list of all torrents

        :rtype: list[TorrentRPC.TorrentObject]
        """
        raw_torrents = self.client.webui_ls()
        torrents = []
        self.torrents.clear()
        for rawTorrent in raw_torrents:
            t = self.build_torrent_object(rawTorrent)
            self.torrents[t.hash] = t
            torrents.append(t)
        return torrents

    def get_torrent_files(self, hash_=None):
        """
        Get a list of file for the torrent specified by hash. If hash is None, return a list of files for every torrents

        :param hash_: the torrent UID
        :return: a list of files
        :type hash_: str
        :rtype: list
        """
        if hash_ is None:
            if len(self.torrents) == 0:
                self.get_torrents()
            files = []
            for hash2 in self.torrents.keys():
                files.append(self.get_torrent_files(hash2))
            return files

        raw_files = self.client.getTorrentFiles(hash_)
        files = []
        for raw_file in raw_files:
            files.append(self.build_torrent_file_object(raw_file))
        return files

    def add_torrent_url(self, torrent_url):
        """
        Add a torrent with url torrentURL

        :param torrent_url: the url of the torrent
        :return: the added torrent
        :type torrent_url: str
        :rtype: TorrentRPC.TorrentObject
        """
        self.logger.debug("Add new torrent from url")
        self.get_torrents()
        old = self.torrents.copy()
        self.client.webui_add_url(torrent_url)
        self.get_torrents()
        added = self.get_torrent_list_modifications(self.torrents, old)["added"]

        if len(added) > 0:
            return added[0]
        return None

    def add_torrent(self, torrent_file_path):
        """
        Add a torrent using a .torrent file

        :param torrent_file_path: The path of the .torrent file
        :return: the added torrent
        :rtype: TorrentRPC.TorrentObject
        """
        self.get_torrents()
        old = self.torrents.copy()
        self.client.webui_add_file(torrent_file_path)
        self.get_torrents()
        added = self.get_torrent_list_modifications(self.torrents, old)["added"]
        if len(added) > 0:
            return added[0]
        return None

    @staticmethod
    def get_torrent_list_modifications(new, old):
        """
        Tool method used to retrieve added and removed torrents using two lists
        :param new: dict
        :param old: dict
        :return: a new dictionary with a field "added" and "removed" composed of two list of TorrentRPC.TorrentObject
        :rtype: dict
        """
        removed = []
        added = []
        for h, n in new.items():
            # print "UTorrentWrapper Debug: new list, [", h, "] ", n.name
            if h not in old:
                # print "UTorrentWrapper Debug: new torrent", n.name
                added.append(n)
        for h, o in old.items():
            # print "UTorrentWrapper Debug: old list, [", h, "] ", o.name
            if h not in new:
                # print "UTorrentWrapper Debug: old torrent", o.name
                removed.append(o)
        return {"added": added, "removed": removed}

    def remove_torrent(self, hash, delete_data=False):
        """
        Remove the torrent with the hash hash

        :param hash: the hash of the torrent to remove
        :param delete_data: if True remove also the data
        :return: True
        """
        if delete_data:
            self.client.webui_remove_data(hash)
        else:
            self.client.webui_remove(hash)
        return True

    def build_torrent_object(self, utorrent_torrent):
        """
        Build a TorrentObject using the data provided by uTorrentTorrent

        TODO:

        - Get the torrent file path

        - Generate the magnet link using the library bencode
        http://stackoverflow.com/questions/12479570/given-a-torrent-file-how-do-i-generate-a-magnet-link-in-python

        :type utorrent_torrent: dict
        :param utorrent_torrent: the data used to build the TorrentObject object
        :return: a TorrentObject object
        :rtype: TorrentRPC.TorrentObject
        """

        torrent = TorrentObject(utorrent_torrent[0], utorrent_torrent[2])
        torrent.eta = utorrent_torrent[10]  # eta	TORRENT_ETA: 10
        torrent.size = utorrent_torrent[3]  # sizeWhenDone	TORRENT_SIZE: 3
        torrent.downloaded = utorrent_torrent[5]  # downloadedEver	TORRENT_DOWNLOADED: 5
        torrent.uploaded = utorrent_torrent[6]  # uploadedEver	TORRENT_UPLOADED: 6
        torrent.seeders = utorrent_torrent[14]  # peersSendingToUs	TORRENT_SEEDS_CONNECTED: 14
        torrent.total_seeders = utorrent_torrent[15]  # seeders	TORRENT_SEEDS_SWARM: 15
        torrent.peers = utorrent_torrent[12]  # peersGettingFromUs	TORRENT_PEERS_CONNECTED: 12
        torrent.total_peers = utorrent_torrent[13]  # peersKnown	TORRENT_PEERS_SWARM: 13
        torrent.magnet_link = None  # magnetLink	create from torrent file
        torrent.torrent_file_path = ""  # torrentFile	/(dl dir)/_torrent_file/(torrentName).torrent
        torrent.ratio = utorrent_torrent[7]  # uploadRatio	TORRENT_RATIO: 7
        torrent.download_rate = utorrent_torrent[9]  # rateDownload (bps)	TORRENT_DOWNSPEED: 9
        torrent.upload_rate = utorrent_torrent[8]  # rateUpload (bps)	TORRENT_UPSPEED: 8
        torrent.is_finished = utorrent_torrent[4] >= 1000  # percentDone == 1	(TORRENT_PROGRESS: 4) == 1'000

        return torrent

    def build_torrent_file_object(self, utorrent_torrent_file):
        """
        Build a TorrentFile using the data provided by uTorrentTorrentFile

        :param utorrent_torrent_file: list
        :return: a TorrentFile object
        :rtype: TorrentRPC.TorrentFile
        """
        # 'noDl'|'high'|'normal'|'low'
        name = utorrent_torrent_file[0]
        size = utorrent_torrent_file[1]
        completed = utorrent_torrent_file[2]
        priority = utorrent_torrent_file[3]
        return TorrentFile(name, size, completed, priority)
