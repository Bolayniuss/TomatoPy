__author__ = 'bolay'
from TomatoPy.TorrentRPC import *
from UTorrent.UTorrent import UTorrent


class UTorrentRPC(TorrentManager):

	def __init__(self, host=None, port=9090, user="admin", password="", dlDirectory=""):
		parameters = None
		if host is not None:
			parameters = [dlDirectory, host, port, user, password]
		super(UTorrentRPC, self).__init__(parameters)
		self.client = UTorrent(self.host, self.port, self.user, self.password)
		self.torrents = dict()

	def getTorrent(self, hash):
		"""
		Retrieve the torrent with hash

		:param hash: the UID of the desired torrent
		:return: torrent
		:type hash: str
		:rtype: TorrentRPC.TorrentObject
		"""
		if hash not in self.torrents:
			self.getTorrents()
		return self.torrents[hash]

	def getTorrents(self):
		"""
		Retrieve a list of all torrents

		:rtype: list[TorrentRPC.TorrentObject]
		"""
		rawTorrents = self.client.webui_ls()
		torrents = []
		self.torrents.clear()
		for rawTorrent in rawTorrents:
			t = self.buildTorrentObject(rawTorrent)
			self.torrents[t.hash] = t
			torrents.append(t)
		return torrents

	def getTorrentFiles(self, hash=None):
		"""
		Get a list of file for the torrent specified by hash. If hash is None, return a list of files for every torrents

		:param hash: the torrent UID
		:return: a list of files
		:type hash: str
		:rtype: list
		"""
		if hash is None:
			if len(self.torrents) == 0:
				self.getTorrents()
			files = []
			for hash2 in self.torrents.keys():
					files.append(self.getTorrentFiles(hash2))
			return files

		rawFiles = self.client.getTorrentFiles(hash)
		files = []
		for rawFile in rawFiles:
			files.append(self.buildTorrentFileObject(rawFile))
		return files

	def addTorrentURL(self, torrentURL):
		"""
		Add a torrent with url torrentURL

		:param torrentURL: the url of the torrent
		:return: the added torrent
		:type torrentURL: str
		:rtype: TorrentRPC.TorrentObject
		"""
		print "UTorrentWrapper Debug: Add new torrent from url"
		self.getTorrents()
		old = self.torrents.copy()
		self.client.webui_add_url(torrentURL)
		self.getTorrents()
		added = self.getTorrentListModifications(self.torrents, old)["added"]

		if len(added) > 0:
			return added[0]
		return None

	def addTorrent(self, torrentFilePath):
		"""
		Add a torrent using a .torrent file

		:param torrentFilePath: The path of the .torrent file
		:return: the added torrent
		:rtype: TorrentRPC.TorrentObject
		"""
		self.getTorrents()
		old = self.torrents.copy()
		self.client.webui_add_file(torrentFilePath)
		self.getTorrents()
		added = self.getTorrentListModifications(self.torrents, old)["added"]
		if len(added) > 0:
			return added[0]
		return None

	def getTorrentListModifications(self, new, old):
		"""
		Tool method used to retrieve added and removed torrents using two lists
		:param new: dict
		:param old: dict
		:return: a new dictionary with a field "added" and "removed" composed of two list of TorrentRPC.TorrentObject
		:rtype: dict
		"""
		removed = []
		added = []
		for h, n in new.iteritems():
			if h not in old:
				print "UTorrentWrapper Debug: new torrent", n.name
				added.append(n)
		for h, o in old.iteritems():
			if h not in new:
				print "UTorrentWrapper Debug: old torrent", n.name
				removed.append(o)
		return {"added": added, "removed": removed}

	def removeTorrent(self, hash, deleteData=False):
		"""
		Remove the torrent with the hash hash

		:param hash: the hash of the torrent to remove
		:param deleteData: if True remove also the data
		:return: True
		"""
		deleteData = False
		if deleteData:
			self.client.webui_remove_data(hash)
		else:
			self.client.webui_remove(hash)
		return True

	def buildTorrentObject(self, uTorrentTorrent):
		"""
		Build a TorrentObject using the data provided by uTorrentTorrent

		TODO:

		- Get the torrent file path

		- Generate the magnet link using the library bencode
		http://stackoverflow.com/questions/12479570/given-a-torrent-file-how-do-i-generate-a-magnet-link-in-python

		:type uTorrentTorrent: dict
		:param uTorrentTorrent: the data used to build the TorrentObject object
		:return: a TorrentObject object
		:rtype: TorrentRPC.TorrentObject
		"""
		torrent = TorrentObject(uTorrentTorrent[0], uTorrentTorrent[2])
		torrent.eta = uTorrentTorrent[10]               # eta	TORRENT_ETA: 10
		torrent.size = uTorrentTorrent[3]               # sizeWhenDone	TORRENT_SIZE: 3
		torrent.downloaded = uTorrentTorrent[5]         # downloadedEver	TORRENT_DOWNLOADED: 5
		torrent.uploaded = uTorrentTorrent[6]           # uploadedEver	TORRENT_UPLOADED: 6
		torrent.seeders = uTorrentTorrent[14]           # peersSendingToUs	TORRENT_SEEDS_CONNECTED: 14
		torrent.totalSeeders = uTorrentTorrent[15]      # seeders	TORRENT_SEEDS_SWARM: 15
		torrent.peers = uTorrentTorrent[12]             # peersGettingFromUs	TORRENT_PEERS_CONNECTED: 12
		torrent.totalPeers = uTorrentTorrent[13]        # peersKnown	TORRENT_PEERS_SWARM: 13
		torrent.magnetLink = None                       # magnetLink	create from torrent file
		torrent.torrentFilePath = ""                    # torrentFile	/(dl dir)/_torrent_file/(torrentName).torrent
		torrent.ratio = uTorrentTorrent[7]	            # uploadRatio	TORRENT_RATIO: 7
		torrent.dlRate = uTorrentTorrent[9]	            # rateDownload (bps)	TORRENT_DOWNSPEED: 9
		torrent.ulRate = uTorrentTorrent[8]     	    # rateUpload (bps)	TORRENT_UPSPEED: 8
		torrent.isFinished = uTorrentTorrent[4] >= 1000     # percentDone == 1	(TORRENT_PROGRESS: 4) == 1'000
		return torrent

	def buildTorrentFileObject(self, uTorrentTorrentFile):
		"""
		Build a TorrentFile using the data provided by uTorrentTorrentFile

		:param uTorrentTorrentFile: list
		:return: a TorrentFile object
		:rtype: TorrentRPC.TorrentFile
		"""
		# 'noDl'|'high'|'normal'|'low'
		name = uTorrentTorrentFile[0]
		size = uTorrentTorrentFile[1]
		completed = uTorrentTorrentFile[2]
		priority = uTorrentTorrentFile[3]
		return TorrentFile(name, size, completed, priority)