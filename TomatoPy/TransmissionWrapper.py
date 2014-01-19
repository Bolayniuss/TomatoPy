__author__ = 'bolay'
from TorrentRPC import *
import transmissionrpc

transmissionrpc.Torrent
class TransmissionTorrentRPC(TorrentManager):

	def __init__(self):
		super(TransmissionTorrentRPC, self).__init__()
		self.torrentClient = transmissionrpc.Client(self.host, self.port, self.user, self.password)

	def getTorrents(self):
		"""

		:rtype : list
		"""
		torrents = []
		rawTorrents = self.torrentClient.get_torrents(None, None)
		for rawTorrent in rawTorrents:
			print rawTorrent
			torrents.append(self.buildTorrentObject(rawTorrent))
		return torrents

	def getTorrentFiles(self, hash=None):
		"""

		:rtype : list
		"""
		files = {}
		try:
			for j, _files in self.torrentClient.get_files(hash).iteritems():
				torrentFiles = []
				for i, file in _files.iteritems():
					tFile = self.buildTorrentFileObject(file)
					torrentFiles.append(tFile)
				#break
				files[j] = torrentFiles
			if len(files) == 1:
				return files[j]
			return files
			#return torrentFiles

		except KeyError as e:
			raise e

	def getTorrent(self, hash):
		try:
			t = self.torrentClient.get_torrent(hash)
			return self.buildTorrentObject(t)
		except KeyError as e:
			raise e

	def torrentExist(self, hash):
		try:
			self.torrentClient.get_torrent(hash, ["id"])
			return True
		except KeyError:
			pass
		finally:
			return False

	def addTorrent(self, torrentFilePath):
		return

	def addTorrentURL(self, torrentUrl):
		return self.torrentClient.add_torrent(torrentUrl)

	def removeTorrent(self, hash, deleteData):
		try:
			self.torrentClient.remove_torrent(hash, deleteData)
			return True
		except KeyError as e:
			raise e

	def buildTorrentObject(self, transmissionTorrent):
		"""
		:type transmissionTorrent Torrent
		:param transmissionTorrent:
		:return:
		"""
		torrent = TorrentObject(transmissionTorrent.hashString, transmissionTorrent.name)
		torrent.eta = transmissionTorrent.eta
		torrent.size = transmissionTorrent.sizeWhenDone
		torrent.downloaded = transmissionTorrent.downloadedEver
		torrent.uploaded = transmissionTorrent.uploadedEver
		torrent.seeders = transmissionTorrent.peersSendingToUs
		torrent.totalSeeders = transmissionTorrent.seeders
		torrent.peers = transmissionTorrent.peersGettingFromUs
		torrent.totalPeers = transmissionTorrent.peersKnown
		torrent.magnetLink = transmissionTorrent.magnetLink
		torrent.torrentFilePath = transmissionTorrent.torrentFile
		torrent.ratio = transmissionTorrent.uploadRatio
		torrent.dlRate = transmissionTorrent.rateDownload
		torrent.ulRate = transmissionTorrent.rateUpload
		torrent.isFinished = transmissionTorrent.percentDone == 1
		return torrent

	def buildTorrentFileObject(self, transmissionTorrentFile):
		# 'noDl'|'high'|'normal'|'low'
		name = transmissionTorrentFile["name"]
		size = transmissionTorrentFile["size"]
		completed = transmissionTorrentFile["completed"]
		priority = transmissionTorrentFile["priority"]
		selected = transmissionTorrentFile["selected"]
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