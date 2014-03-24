__author__ = 'bolay'

import os

from DatabaseManager import DatabaseManager
from TomatoPy.SourceMapperItem import FileItem
from TomatoPy.Filters import FileFilter
import logging


class TorrentObject:
	"""
	Object that represents a torrent (task)
	"""
	def __init__(self, hash, name):
		self.name = ""
		self.hash = ""
		self.size = ""

		self.isDownloaded = False
		self.magnetLink = None

		self.files = list()

		self.hash = hash            # hashString	TORRENT_HASH: 0
		self.name = name            # name	TORRENT_NAME: 2
		self.eta = 0                # eta	TORRENT_ETA: 10
		self.size = 0               # sizeWhenDone	TORRENT_SIZE: 3
		self.downloaded = 0         # downloadedEver	TORRENT_DOWNLOADED: 5
		self.uploaded = 0           # uploadedEver	TORRENT_UPLOADED: 6
		self.seeders = 0            # peersSendingToUs	TORRENT_SEEDS_CONNECTED: 14
		self.totalSeeders = 0       # seeders	TORRENT_SEEDS_SWARM: 15
		self.peers = 0              # peersGettingFromUs	TORRENT_PEERS_CONNECTED: 12
		self.totalPeers = 0         # peersKnown	TORRENT_PEERS_SWARM: 13
		self.magnetLink = None      # magnetLink	create from torrent file
		self.torrentFilePath = ""   # torrentFile	/(dl dir)/_torrent_file/(torrentName).torrent
		self.ratio = 0	            # uploadRatio	TORRENT_RATIO: 7
		self.dlRate = 0	            # rateDownload (bps)	TORRENT_DOWNSPEED: 9
		self.ulRate = 0    	        # rateUpload (bps)	TORRENT_UPSPEED: 8
		self.isFinished = False     # percentDone == 1	(TORRENT_PROGRESS: 4) == 1'000'000


class TorrentFile:
	def __init__(self, name=None, size=None, completed=None, priority=None):
		# FILE NAME (string),
		# FILE SIZE (integer, in bytes),
		# DOWNLOADED (integer, in bytes),
		# PRIORITY* (integer, {0 = Don't Download, 1 = Low Priority, 2 = Normal Priority, 3 = High Priority})

		self.name = name
		self.size = size
		self.completed = completed
		self.priority = priority        # '0:noDl'|'3:high'|'2:normal'|'1:low'


	@staticmethod
	def fromTorrentProp(tFile):
		if len(tFile) >= 5:
			return TorrentFile(tFile["name"], tFile["size"], tFile["completed"], tFile["priority"], tFile["selected"])
		return None


class TorrentManager(object):
	# getTorrent(hash)
	# getTorrents
	# getTorrentFiles(hash)
	# addTorrentURL(torrentURL)
	# addTorrent(torrentFilePath)
	# removeTorrent(hash, deleteData)

	def __init__(self, parameters=None):
		self.logger = logging.getLogger(__name__)
		if parameters is None:
			query = "SELECT parameters FROM Parameters WHERE name='TorrentManager' LIMIT 1"
			DatabaseManager.Instance().cursor.execute(query)
			(parametersString, ) = DatabaseManager.Instance().cursor.fetchone()
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
			self.initWithExtraParams(parameters[5:])

	def initWithExtraParams(self, extraParams):
		pass

	def getTorrentFilePath(self, torrentName, filename):
		#print "Debug: downloadDirectory=", self.downloadDirectory
		#print "path1=", os.path.join(self.downloadDirectory, filename)
		#print "path2=", os.path.join(self.downloadDirectory, torrentName, filename)
		if os.path.isfile(os.path.join(self.downloadDirectory, filename)):
			return os.path.join(self.downloadDirectory, filename)
		elif os.path.isfile(os.path.join(self.downloadDirectory, torrentName, filename)):
			return os.path.join(self.downloadDirectory, torrentName, filename)
		self.logger.warn("no file found in %s with filename %s", torrentName, filename)
		raise IOError("file not found")
		return None

	def getTorrents(self):
		return list()

	def getTorrent(self, hash):
		"""

		:type hash: str
		"""
		return None

	def getTorrentFiles(self, torrentHash):
		"""

		:type torrentHash: str
		"""
		return list()

	def addTorrent(self, torrentFilePath):
		return None

	def addTorrentURL(self, torrentUrl):
		return None

	def removeTorrent(self, hash, deleteData=False):
		return None

	# def selectAndMoveFile(self, torrent, filter, destinationPath, filename):
	# 	files = self.getTorrentFiles(torrent.hashString)
	# 	rarFilter = FileFilter(".*", ["rar"])
	# 	validFiles = []
	# 	for file in files:
	# 		#print file.name
	# 		fileItem = FileItem(file.name, "")
	# 		if filter.test(fileItem):
	# 			validFiles.append(file)
	# 		elif rarFilter.test(fileItem):
	# 			extractedFile = self.extractFromRar(filter, self.getTorrentFilePath(torrent.name, file.name))
	# 			if extractedFile is not None:
	# 				validFiles.append(extractedFile)
	#
	# 	if len(validFiles) == 0:
	# 		print "No valid files found"
	# 		return False
	# 	id = 0
	# 	i = 1
	# 	while i < len(validFiles):
	# 		print validFiles[i].name, " size=", validFiles[i].size
	# 		if validFiles[i].size > validFiles[id].size:
	# 			print "    last id=", id, " new id=", i
	# 			id = i
	# 		i += 1
	# 	file = validFiles[id]
	# 	ext = FileItem(file.name, "").extension
	# 	src = self.getTorrentFilePath(torrent.name, file.name)
	# 	if src is None:
	# 		return False
	# 	dst = os.path.join(destinationPath, filename + "." + ext)
	# 	if len(src) > 0:
	# 		print "move: ", src, " to ", dst
	# 		try:
	# 			os.makedirs(destinationPath)
	# 		except OSError:
	# 			pass
	# 		finally:
	# 			pass
	# 		shutil.move(src, dst)
	# 		os.chmod(dst, 0777)
	# 		try:
	# 			os.chown(dst, pwd.getpwnam("guest").pw_uid, grp.getgrnam("guest").gr_gid)
	# 		except KeyError, e:
	# 			pass
	# 		finally:
	# 			pass
	# 		return True
	# 	return False
