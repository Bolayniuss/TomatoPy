# -*- coding: utf8 -*-

import transmissionrpc

from . import TorrentObject, TorrentFile
from ._base import TorrentManager


class TransmissionTorrentRPC(TorrentManager):
    def __init__(self):
        super(TransmissionTorrentRPC, self).__init__()
        self.torrentClient = transmissionrpc.Client(self.host, self.port, self.user, self.password)

    def get_torrents(self):
        """

        :rtype: list(TorrentObject)
        """
        torrents = []
        raw_torrents = self.torrentClient.get_torrents(None, None)
        for rawTorrent in raw_torrents:
            torrents.append(self.build_torrent_object(rawTorrent))
        return torrents

    def get_torrent_files(self, hash_=None):
        """

        :rtype : list(TorrentFile)
        """
        files = {}
        try:
            for j, _files in self.torrentClient.get_files(hash_).iteritems():
                torrentFiles = []
                for i, file in _files.iteritems():
                    tFile = self.build_torrent_file_object(file)
                    torrentFiles.append(tFile)
                # break
                files[j] = torrentFiles
            if len(files) == 1:
                return files[j]
            return files
        # return torrentFiles

        except KeyError as e:
            raise e

    def get_torrent(self, _hash):
        try:
            t = self.torrentClient.get_torrent(_hash)
            return self.build_torrent_object(t)
        except KeyError as e:
            raise e

    def torrent_exist(self, _hash):
        try:
            self.torrentClient.get_torrent(_hash, ["id"])
            return True
        except KeyError:
            pass
        finally:
            return False

    def add_torrent(self, torrent_file_path):
        return

    def add_torrent_url(self, torrent_url):
        return self.build_torrent_object(self.torrentClient.add_torrent(torrent_url), True)

    def remove_torrent(self, hash_, delete_data=False):
        try:
            self.torrentClient.remove_torrent(hash_, delete_data)
            return True
        except KeyError as e:
            raise e

    def build_torrent_object(self, transmission_torrent, mini=False):
        """
        :type transmission_torrent Torrent
        :param transmission_torrent:
        :return:
        """
        # print transmissionTorrent._fields
        torrent = TorrentObject(transmission_torrent.hashString, transmission_torrent.name)
        # torrent.eta = transmissionTorrent.eta
        # torrent.size = transmissionTorrent.totalSize
        # torrent.downloaded = transmissionTorrent.downloadedEver
        # torrent.uploaded = transmissionTorrent.uploadedEver
        # torrent.seeders = transmissionTorrent.peersSendingToUs
        # torrent.totalSeeders = transmissionTorrent.seeders
        # torrent.peers = transmissionTorrent.peersGettingFromUs
        # torrent.totalPeers = transmissionTorrent.peersKnown
        # torrent.magnetLink = transmissionTorrent.magnetLink
        # torrent.torrentFilePath = transmissionTorrent.torrentFile
        # torrent.ratio = transmissionTorrent.uploadRatio
        # torrent.dlRate = transmissionTorrent.rateDownload
        # torrent.ulRate = transmissionTorrent.rateUpload
        # torrent.isFinished = transmissionTorrent.percentDone == 1
        if not mini:
            # torrent.eta = transmissionTorrent.eta
            torrent.size = transmission_torrent.totalSize
            torrent.downloaded = transmission_torrent.downloadedEver
            torrent.uploaded = transmission_torrent.uploadedEver
            torrent.seeders = transmission_torrent.peersSendingToUs
            # torrent.totalSeeders = transmissionTorrent.seeders
            torrent.peers = transmission_torrent.peersGettingFromUs
            # torrent.totalPeers = transmissionTorrent.peersKnown
            torrent.magnetLink = transmission_torrent.magnetLink
            torrent.torrentFilePath = transmission_torrent.torrentFile
            torrent.ratio = transmission_torrent.uploadRatio
            torrent.dlRate = transmission_torrent.rateDownload
            torrent.ulRate = transmission_torrent.rateUpload
            torrent.isFinished = transmission_torrent.percentDone == 1
        return torrent

    def build_torrent_file_object(self, transmission_torrent_file):
        # 'noDl'|'high'|'normal'|'low'
        name = transmission_torrent_file["name"]
        size = transmission_torrent_file["size"]
        completed = transmission_torrent_file["completed"]
        priority = transmission_torrent_file["priority"]
        selected = transmission_torrent_file["selected"]
        _priority = None
        if not selected:
            _priority = 0
        if priority is not None:
            if priority == "high":
                _priority = 3
            elif priority == "normal":
                _priority = 2
            elif priority == "low":
                _priority = 1
        return TorrentFile(name, size, completed, _priority)
