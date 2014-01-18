__author__ = 'bolay'

import os
import pwd
import grp
import shutil
import transmissionrpc
from DatabaseManager import DatabaseManager
from SourceMapperItem import *
from Filters import FileFilter


class Torrent:
	def __init__(self):
		self.name = ""
		self.hash = ""
		self.size = ""

		self.seeds = {"active": 0, "total": 0}
		self.peers = {"active": 0, "total": 0}



class TorrentFile:

	def __init__(self, name=None, size=None, completed=None, priority=None, selected=None):
		self.name = name
		self.size = size
		self.completed = completed
		self.priority = priority
		self.selected = selected
	@staticmethod
	def fromTorrentProp(tFile):
		if len(tFile) >= 5:
			return TorrentFile(tFile["name"], tFile["size"], tFile["completed"], tFile["priority"], tFile["selected"])
		return None


class TorrentManager(object):

	def __init__(self):
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

	def getTorrentFilePath(self, torrentName, filename):
		if os.path.isfile(os.path.join(self.downloadDirectory, filename)):
			return os.path.join(self.downloadDirectory, filename)
		elif os.path.isfile(os.path.join(self.downloadDirectory, torrentName, filename)):
			return os.path.join(self.downloadDirectory, torrentName, filename)
		return None

	def selectAndMoveFile(self, torrent, filter, destinationPath, filename):
		files = self.getTorrentFiles(torrent.hashString)
		rarFilter = FileFilter(".*", ["rar"])
		validFiles = []
		for file in files:
			#print file.name
			fileItem = FileItem(file.name, "")
			if filter.test(fileItem):
				validFiles.append(file)
			elif rarFilter.test(fileItem):
				extractedFile = self.extractFromRar(filter, self.getTorrentFilePath(torrent.name, file.name))
				if extractedFile is not None:
					validFiles.append(extractedFile)

		if len(validFiles) == 0:
			print "No valid files found"
			return False
		id = 0
		i = 1
		while i < len(validFiles):
			print validFiles[i].name, " size=", validFiles[i].size
			if validFiles[i].size > validFiles[id].size:
				print "    last id=", id, " new id=", i
				id = i
			i += 1
		file = validFiles[id]
		ext = FileItem(file.name, "").extension
		src = self.getTorrentFilePath(torrent.name, file.name)
		if src is None:
			return False
		dst = os.path.join(destinationPath, filename + "." + ext)
		if len(src) > 0:
			print "move: ", src, " to ", dst
			try:
				os.makedirs(destinationPath)
			except OSError:
				pass
			finally:
				pass
			shutil.move(src, dst)
			os.chmod(dst, 0777)
			try:
				os.chown(dst, pwd.getpwnam("guest").pw_uid, grp.getgrnam("guest").gr_gid)
			except KeyError, e:
				pass
			finally:
				pass
			return True
		return False


class TransmissionTorrentRPC(TorrentManager):

	def __init__(self):
		super(TransmissionTorrentRPC, self).__init__()
		self.torrentClient = transmissionrpc.Client(self.host, self.port, self.user, self.password)

	def getTorrents(self):
		"""

		:rtype : list
		"""
		return self.torrentClient.get_torrents(None, None)

	def getTorrentFiles(self, hash=None):
		"""

		:rtype : list
		"""
		files = {}
		try:
			for j, _files in self.torrentClient.get_files(hash).iteritems():
				torrentFiles = []
				for i, file in _files.iteritems():
					tFile = TorrentFile(file["name"], file["size"], file["completed"], file["priority"], file["selected"])
					#tFile.name = file["name"]
					#tFile.size = file["size"]
					#tFile.completed = file["completed"]
					#tFile.priority = file["priority"]
					#tFile.selected = file["selected"]
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
			return t
		except KeyError as e:
			raise e

	def torrentExist(self, hash):
		try:
			self.torrentClient.get_torrent(hash, ["id"])
			return True
		except KeyError:
			raise False

	def addTorrent(self, torrentFilePath):
		return

	def addTorrentURL(self, torrentUrl):
		return self.torrentClient.add_torrent(torrentUrl)

	def removeTorrent(self, hash, deleteData):
		try:
			t = self.torrentClient.remove_torrent(hash, deleteData)
			return t
		except KeyError as e:
			raise e

