__author__ = 'bolay'

import transmissionrpc

class Torrent:
	name = ""
	hash = ""
	size = ""

	seeds = {"active": 0, "total": 0}
	peers = {"active": 0, "total": 0}


class TorrentFile:
	name = None
	size = None
	completed = None
	priority = None
	selected = None


class TransmissionTorrentRPC:
	torrentClient = None

	def __init__(self, host, port=9091, user=None, password=None):
		self.torrentClient = transmissionrpc.Client(host, port, user, password)

	def getTorrents(self):
		return self.torrentClient.get_torrents(None, None)

	def getTorrentFiles(self, hash):

		torrentFiles = []
		for j, _files in self.torrentClient.get_files(hash).iteritems():
			for i, file in _files.iteritems():
				tFile = TorrentFile
				tFile.name = file["name"]
				tFile.size = file["size"]
				tFile.completed = file["completed"]
				tFile.priority = file["priority"]
				tFile.selected = file["selected"]
				torrentFiles.append(tFile)
			break
		return torrentFiles

	def addTorrent(self, torrentFilePath):
		return

	def addTorrentURL(self, torrentUrl):
		self.torrentClient.add_torrent(torrentUrl)

