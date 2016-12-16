# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals
import base64
import os

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
            for j, _files in self.torrentClient.get_files(hash_).items():
                torrent_files = []
                for i, file in _files.items():
                    torrent_file = self.build_torrent_file_object(file)
                    torrent_files.append(torrent_file)
                # break
                files[j] = torrent_files
            if len(files) == 1:
                return files[-1]
            return files
        # return torrent_files

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

    def add_torrent(self, torrent_content):
        """

        :param TomatoPy.api.torrents.TorrentContent torrent_content:
        :return:
        """
        if torrent_content.type == torrent_content.TYPE_MAGNET:
            return self.add_torrent_url(torrent_content.content)
        elif torrent_content.type == torrent_content.TYPE_DATA:
            torrent_data = base64.b64encode(torrent_content.content)
            return self.build_torrent_object(self.torrentClient.add_torrent(torrent_data), False)
        elif torrent_content.type == torrent_content.TYPE_FILE:
            with open(torrent_content.content, "rb") as f:
                torrent_data = base64.b64encode(f.read())
            torrent = self.build_torrent_object(self.torrentClient.add_torrent(torrent_data), False)
            os.remove(torrent_content.content)
            return torrent

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
        :param mini:
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
        # torrent.is_finished = transmissionTorrent.percentDone == 1
        if not mini:
            # torrent.eta = transmissionTorrent.eta
            torrent.size = transmission_torrent.totalSize
            torrent.downloaded = transmission_torrent.downloadedEver
            torrent.uploaded = transmission_torrent.uploadedEver
            torrent.seeders = transmission_torrent.peersSendingToUs
            # torrent.totalSeeders = transmissionTorrent.seeders
            torrent.peers = transmission_torrent.peersGettingFromUs
            # torrent.totalPeers = transmissionTorrent.peersKnown
            torrent.magnet_link = transmission_torrent.magnetLink
            torrent.torrent_file_path = transmission_torrent.torrentFile
            torrent.ratio = transmission_torrent.uploadRatio
            torrent.download_rate = transmission_torrent.rateDownload
            torrent.upload_rate = transmission_torrent.rateUpload
            torrent.is_finished = transmission_torrent.percentDone == 1
        return torrent

    @staticmethod
    def build_torrent_file_object(transmission_torrent_file):
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
