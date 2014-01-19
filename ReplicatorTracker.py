__author__ = 'bolay'

import os
import hashlib
import re
from DatabaseManager import DatabaseManager
from TomatoPy.TransmissionWrapper import *
import sys
import unicodedata
import base64
import Tools
from Singleton import Singleton


class TrackedTorrent:
	def __init__(self, hash, name, magnet, torrentFile=None):
		"""
		;type torrent : transmissionrpc.Torrent
		:param torrent:
		"""
		self.name = name
		self.hash = hash
		self.torrentFileData = ''
		self.magnet = magnet
		if torrentFile is not None and os.path.exists(torrentFile):
			f = open(torrentFile, "rb")
			self.torrentFileData = base64.b64encode(f.read())

	@staticmethod
	def fromSqlQuery(sqlQuery):
		if len(sqlQuery) >= 4:
			tt = TrackedTorrent(sqlQuery[0], sqlQuery[1], sqlQuery[3])
			tt.torrentFileData = sqlQuery[2]
			return tt
		return None

	@staticmethod
	def fromTorrent(torrent):
		return TrackedTorrent(torrent.hashString, torrent.name, torrent.magnetLink, torrent.torrentFile)


class InterestingFile:
	def __init__(self, name, torrentHash, torrentFileName, hash=None, timeout=2538000):  # default timeout set to 30 days
		self.name = name
		self.timeout = timeout
		self.torrentHash = torrentHash
		self.torrentFileName = torrentFileName
		self.hash = hash
		if (self.hash is None) or (len(self.hash)) == 0:
			self.hash = Tools.getHash(self.name)

	def setTimeout(self, timeout=2538000): # default timeout set to 30 days
		sql = "UPDATE TrackedTorrentFiles SET timeout=UNIX_TIMESTAMP()+" + timeout + " WHERE name=%s;"
		DatabaseManager.Instance().cursor.execute(sql, (self.name, ))
		DatabaseManager.Instance().connector.commit()

	def insertOrUpdateInDB(self):
		#if not self.isInDB:
		sql = "INSERT INTO TrackedTorrentFiles (hash, name, timeout, torrentHash, torrentFileName) " \
		      "VALUES (%s, %s, UNIX_TIMESTAMP()+%s, %s, %s) " \
		      "ON DUPLICATE KEY UPDATE timeout=VALUES(timeout);"
		DatabaseManager.Instance().cursor.execute(sql, (
			self.hash, self.name, self.timeout, self.torrentHash, self.torrentFileName))
		DatabaseManager.Instance().connector.commit()

	@staticmethod
	def fromSqlQuery(sqlQuery):
		if len(sqlQuery) >= 5:
			f = InterestingFile(sqlQuery[1], sqlQuery[3], sqlQuery[4], sqlQuery[0], sqlQuery[2])
			#f.isInDB = True
			return f
		#print "Fail to initiate InterestingFile with query : ", sqlQuery
		return None


class DoneTorrentFilter:
	def __init__(self, torrentManager):
		self.torrentManager = torrentManager
		self.filter = RFileFilter("avi|mkv|mp4|wmv")
		self.interestingFiles = {}

	def grabInterestingFiles(self):
		# Load old from DB
		sql = "SELECT * FROM TrackedTorrentFiles;"
		DatabaseManager.Instance().cursor.execute(sql)
		for res in DatabaseManager.Instance().cursor:
			iF = InterestingFile.fromSqlQuery(res)
			if iF is not None:
				self.interestingFiles[iF.name] = iF

		# Get new from torrent manager
		torrents = self.torrentManager.getTorrents()
		for torrent in torrents:
			if torrent.isFinished:
				torrentFiles = self.torrentManager.getTorrentFiles(torrent.hash)
				for f in torrentFiles:
					#print torrent.name
					#print f["name"],": ",
					file = File(os.path.join(self.torrentManager.downloadDirectory, f["name"]))
					if self.filter.test(file):
						#print "filter test = ok",
						if os.path.exists(file.fullPath):
							#print "existence test = ok"
							iF = InterestingFile(file.fullPath, torrent.hashString, f["name"])
							iF.insertOrUpdateInDB()    # update timeout in any case
							if not self.interestingFiles.has_key(file.fullPath):
								self.interestingFiles[file.fullPath] = iF
							sql = "INSERT INTO TrackedTorrents (hash, name, torrentFile, magnet) VALUES (%s, %s, %s, %s)" \
							      " ON DUPLICATE KEY UPDATE hash=VALUES(hash);"
							t = TrackedTorrent.fromTorrent(torrent)
							DatabaseManager.Instance().cursor.execute(sql,
							                                          (t.hash, t.name, t.torrentFileData, t.magnet))
							DatabaseManager.Instance().connector.commit()

						#for a, iF in self.interestingFiles.iteritems():
						#	print iF.hash, iF.name
					#print ""


class RFileFilter:
	def __init__(self, extensionPattern):
		self.extension = extensionPattern

	def test(self, file):
		"""
		:type file : File
		:param file:
		:return:
		"""
		if file.extension is None:
			return False
		if file.name[0] == ".":
			return False
		return re.search(self.extension, file.extension, re.IGNORECASE) is not None


@Singleton
class DestinationManager:
	def __init__(self):
		self.destinations = {}

	def add(self, destination):
		"""
		:type destination : Destination
		:param destination:
		:return:
		"""
		if destination.name not in self.destinations:
			self.destinations[destination.name] = destination

	def get(self, name):
		return self.destinations[name]


class Destination:
	def __init__(self, path, name, filter):
		"""

		:param path: path of the destination directory
		:param name: name of the destination
		"""
		self.path = path
		self.name = name
		self.files = {}
		self.validInterestingFiles = []
		self.filter = filter
		DestinationManager.Instance().add(self)

	def getRelativePath(self, path):
		"""

		:param path: absolute path
		"""
		return os.path.relpath(path, self.path)

	def map(self, clean=False):
		self.files = {}
		curs = DatabaseManager.Instance().cursor
		if clean:
			curs.execute("DELETE FROM DestinationsFilesList WHERE destinationName=%s;", (self.name, ))
			DatabaseManager.Instance().connector.commit()
		for root, dir, files in os.walk(self.path):

			for file in files:
				path = os.path.join(root, file)
				relativePath = self.getRelativePath(path)
				if self.filter.test(File(path)):
					fwh = None
					if not clean:
						sql = "SELECT * FROM DestinationsFilesList WHERE path=%s AND destinationName=%s;"
						curs.execute(sql, (relativePath, self.name))
						res = curs.fetchone()
						curs.fetchall()
						if res is not None:
							# file already in DB, so use it
							fwh = FileWithHash.fromSqlQuery(res)
					if fwh is None:
						fwh = FileWithHash(path, self.name, None, relativePath)
						sql2 = "INSERT INTO DestinationsFilesList (hash, path, destinationName) VALUES(%s, %s, %s);"
						print self.name, " add: ", relativePath
						curs.execute(sql2, (fwh.hash, relativePath, fwh.destinationName))
						DatabaseManager.Instance().connector.commit()
					self.files[fwh.hash] = fwh

	def lookForInterestingFiles(self, ifList):
		self.validInterestingFiles = []
		for i, f in ifList.iteritems():
			if f.hash in self.files:
				print "New interesting file : ", f.name
				self.validInterestingFiles.append((f, self.files[f.hash]))

	@staticmethod
	def fromSqlQuery(query):
		if len(query) >= 3:
			if not isinstance(query[1], unicode):
				query[1] = unicode(query[1])
			return Destination(query[1], query[0], RFileFilter(query[2]))
		return None


class File:
	def __init__(self, path):
		"""

		:param path:
		"""
		self.fullPath = path
		self.path = os.path.dirname(path)
		self.name = os.path.basename(path)
		self.simpleName = self.name
		self.extension = None
		#if os.path.isfile(self.fullPath):
		m = re.compile(r"(.*)\.([^.]*)").match(self.name)
		if m is not None:
			self.simpleName = m.group(1)
			self.extension = m.group(2)


class FileWithHash(File):
	"""

	FileWithHash represent files present in destination directories
	"""

	def __init__(self, path, destinationName, hash=None, relativPath=None):
		"""

		:type destinationName : str
		:type hash : str
		:param hash: hash of the file, if None the hash is computed
		:param path: Path of the file
		:param destinationName: destination name
		"""
		File.__init__(self, path)
		self.id = None
		self.hash = hash
		self.destinationName = destinationName
		if hash is None:
			self.hash = Tools.getHash(self.fullPath)
		self.relativePath = path
		if relativPath is not None:
			self.relativePath = relativPath


	@staticmethod
	def fromSqlQuery(sqlQuery):
		if (sqlQuery is not None) and (len(sqlQuery) >= 3):
			f = FileWithHash(sqlQuery[3], sqlQuery[2], sqlQuery[1])
			f.id = sqlQuery[0]
			return f
		return None


class FileTracer:
	def __init__(self):
		# create useful objects
		self.dbm = DatabaseManager.Instance()
		self.torrentManager = TransmissionTorrentRPC()

		# Load parameters
		# Load destinations
		self.destinations = []
		self.dbm.cursor.execute("SELECT * FROM TrackedDestinations;")
		for res in self.dbm.cursor:
			d = Destination.fromSqlQuery(res)
			if d is not None:
				self.destinations.append(d)

		# init DoneTorrentFilter
		self.dtf = DoneTorrentFilter(self.torrentManager)

	def run(self):
		# get interesting files
		self.dtf.grabInterestingFiles()

		if len(self.dtf.interestingFiles) > 0:
			# Map all sources
			for d in self.destinations:
				d.map()
				d.lookForInterestingFiles(self.dtf.interestingFiles)
		self.dbm.connector.commit()
		# For each destinations
		for destination in self.destinations:
			# For each tuple (trackedFile, destinationFile) in interestingFiles
			for trackedFile, destinationFile in destination.validInterestingFiles:
				sql = "SELECT * FROM TrackedTorrents WHERE hash=%s;"
				self.dbm.cursor.execute(sql, (trackedFile.torrentHash, ))
				res = self.dbm.cursor.fetchone()
				# If torrent is in TrackedTorrents DB
				if res is not None:
					tt = TrackedTorrent.fromSqlQuery(res)
					if tt is not None:
						print "New replicator action with file: ", trackedFile.torrentFileName
						sql = "INSERT INTO ReplicatorActions " \
						      "(torrentName, torrentFileName, torrentData, destinationName, destinationRelativePath) " \
						      "VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE torrentFileName=torrentFileName;"
						self.dbm.cursor.execute(sql, (tt.name, trackedFile.torrentFileName, tt.magnet, destination.name, destinationFile.fullPath))
						self.dbm.connector.commit()

						# Remove File from TrackedTorrentFiles DB
						print "Remove TrackedTorrentFile ", trackedFile.name
						sql = "DELETE FROM TrackedTorrentFiles WHERE hash=%s;"
						self.dbm.cursor.execute(sql, (trackedFile.hash, ))
						self.dbm.connector.commit()
					else:
						print "Unable to create TrackedTorrent with query", res
				else:
					print "res is None for hash=", trackedFile.torrentHash

	def clean(self):
		#self.dbm.cursor.execute("DELETE FROM TrackedTorrentFiles WHERE timeout<UNIX_TIMESTAMP()")
		print "Begining Clean up."
		torrents = {}
		for torrent in self.torrentManager.getTorrents():
			torrents[torrent.hash] = 1

		deleteTTSql = "DELETE FROM TrackedTorrents WHERE hash=%s;"
		getTTFWithTorrentHashSql = "SELECT 1 FROM TrackedTorrentFiles WHERE torrentHash=%s LIMIT 1;"
		for iF in self.dtf.interestingFiles.itervalues():
			# Clean up TrackedTorrentFiles DB
			delete = False
			# Remove if file does not exist (deleted, moved)
			if not os.path.exists(iF.name):
				delete = True
			# Remove if associated torrent does not exists
			if not (iF.torrentHash in torrents):
				delete = True
			if delete:
				print "Remove TrackedTorrentFile ", iF.name
				self.dbm.cursor.execute("DELETE FROM TrackedTorrentFiles WHERE name=%s", (iF.name, ))
				self.dbm.connector.commit()

			# Clean up TrackedTorrents DB
			sql = "SELECT hash FROM TrackedTorrents;"
			self.dbm.cursor.execute(sql)
			trackedTorrents = []
			for res in self.dbm.cursor:
				trackedTorrents.append(res[0])

			for hashStr in trackedTorrents:
				self.dbm.cursor.execute(getTTFWithTorrentHashSql, (hashStr, ))
				res = self.dbm.cursor.fetchone()
				# No TrackedTorrentFile associated with this TrackedTorrent => remove
				if res is None:
					print "Remove TrackedTorrent with hash=", hashStr
					self.dbm.cursor.execute(deleteTTSql, (hashStr, ))
					self.dbm.connector.commit()

		print "End Clean up."




if __name__ == "__main__":
	DatabaseManager.Instance().connect('replicator', 'root', None, '127.0.0.1')
	ft = FileTracer()
	ft.run()
#ft.clean()
