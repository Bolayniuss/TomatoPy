# -*- coding: utf8 -*-
__author__ = 'bolay'

import re
import os
from TomatoPy.Scrapper import *
from TomatoPy.SourceMapper import *
from DatabaseManager import DatabaseManager
from XbmcLibraryManager import XbmcLibraryManager
from AutomatedActionExecutor import *
import time
import Tools
import rarfile
from TomatoPy.TorrentRPC import TorrentFile


class TvShowManager(AutomatedActionsExecutor):
	def __init__(self, torrentManager):
		super(TvShowManager, self).__init__("TvShowManager")
		dbm = DatabaseManager.Instance()
		self.torrentManager = torrentManager

		self.trackedTvShows = []  # tv shows that can be downloaded // Get them form db
		#self.bUser = "bolayniuss"           # betaserie user // Get it form db
		#self.tvShowDirectory = "/Volumes/Partage/Serie"  # directory of tv shows // Get from db

		query = "SELECT parameters FROM Parameters WHERE name='TvShowManager' LIMIT 1"
		dbm.cursor.execute(query)
		(parametersString, ) = dbm.cursor.fetchone()
		parameters = parametersString.split("&&")
		self.bUser = parameters[1]
		self.tvShowDirectory = u""+parameters[0]
		self.fileSystemEncoding = None
		if len(parameters) > 2:
			self.fileSystemEncoding = parameters[2]

		query = "SELECT title, filter, authorFilter, sizeLimits FROM TrackedTvShows;"
		dbm.cursor.execute(query)
		filter = None
		for (title, nameFilter, authorFilter, sizeLimits) in dbm.cursor:
			sizes = {}
			sizeLimits = sizeLimits.split(":")
			if len(sizeLimits[0]) > 0:
				sizes["gt"] = int(sizeLimits[0])
			if len(sizeLimits) > 1:
				if len(sizeLimits[1]) > 0:
					sizes["lt"] = int(sizeLimits[1])
			filter = TorrentFilter(nameFilter.split(":"), authorFilter, sizes)
			self.trackedTvShows.append((title, filter))
		dbm.connector.commit()
		self.loadActions()

	def getNewTvShow(self):

		betaserieEpisodes = BetaserieRSSScrapper(self.bUser).items

		_tmp = []
		for item in betaserieEpisodes:
			for (tvShowTitle, filter) in self.trackedTvShows:
				if re.search(re.escape(tvShowTitle), item.title, re.IGNORECASE) is not None:
					#print "TvShowManager: Possible new episode found: ", item.title
					item.filter = filter
					item.tvShow = tvShowTitle
					_tmp.append(item)
					break

		betaserieEpisodes = _tmp
		_tmp = []

		tvShowInDir = DirectoryMapper(self.tvShowDirectory, FileFilter(".*", ["mkv", "avi", "mp4"]), self.fileSystemEncoding).files
		for item in betaserieEpisodes:
			add = True
			for fileItem in tvShowInDir:
				if re.search(re.escape(item.title), fileItem.name, re.IGNORECASE) is not None:
					#print "TvShowManager: Episode ", item.title, " removed because it already exist in source directory ", fileItem.name
					add = False
					break
				else:
					if fileItem.name[0] == "H":
						print item.title, re.escape(item.title), " is not in ", fileItem.name
			if add:
				_tmp.append(item)

		betaserieEpisodes = _tmp
		return betaserieEpisodes

	def addNewToTorrentManager(self, torrentManager):
		episodes = self.getNewTvShow()

		torrents = torrentManager.getTorrents()
		for episode in episodes:

			patternArray = episode.title.split(" ")
			for i in xrange(len(patternArray)):
				patternArray[i] = re.escape(patternArray[i])
			pattern = ".".join(patternArray)
			new = True
			for torrent in torrents:
				if re.search(re.escape(pattern), torrent.name, re.IGNORECASE) is not None:
					#print "TvShowManager: episode ", pattern, " found in torrent list ", torrent.name
					#self.addAutomatedActions(torrent.hashString, episode.tvShow, episode.title)
					new = False
					break
			if new:
				rpbItems = TPBScrapper(episode.title, episode.filter).torrents
				if len(rpbItems) > 0:
					newTorrent = torrentManager.addTorrentURL(rpbItems[0].link)
					self.addAutomatedActions(newTorrent.hash, episode.tvShow, episode.title)
				else:
					print "No torrent found for ", episode.title

	def addAutomatedActions(self, torrentId, tvShow, episodeName):
		#sql = "INSERT INTO `AutomatedActions` (`id`, `notifier`, `trigger`, `data`) VALUES (NULL, 'asd', 'onTorrentDownloaded', 'asdasd');"
		query = "INSERT INTO `AutomatedActions` (`notifier`, `trigger`, `data`) VALUES ('TvShowManager', 'onTorrentDownloaded', %s);"
		data = "&&".join(["move", torrentId, tvShow, episodeName])
		print query, data
		DatabaseManager.Instance().cursor.execute(query, (data, ))
		DatabaseManager.Instance().connector.commit()

	def moveTvShow(self, file, tvShow, episodeName, fsUser="guest", fsGroup="guest"):
		"""
		:type file : FileItem
		:param file:
		:param tvShow:
		:param episodeName:
		:param user:
		:param group:
		:return:
		"""
		if file is None:
			return False
		season = self.getSeasonFromTitle(episodeName)
		dst = os.path.join(self.tvShowDirectory, tvShow, "Saison " + season, episodeName + "." + file.extension)
		sourceFilePath = file.getFullPath()
		print "TvShowManager: try to move ", sourceFilePath, " to ", dst
		if len(sourceFilePath) > 0:
			return Tools.FileSystemHelper.Instance().move(sourceFilePath, dst)
		return False

	def getTvShowFileFromTorrent(self, torrent, filter):
		files = self.torrentManager.getTorrentFiles(torrent.hash)
		rarFilter = FileFilter(".*", ["rar"])
		validFiles = []
		for file in files:
			#print file.name
			fileItem = FileItem(file.name, "")
			if filter.test(fileItem):
				validFiles.append(file)
			elif rarFilter.test(fileItem):
				extractedFile = self.extractFromRar(filter, self.torrentManager.getTorrentFilePath(torrent.name, file.name))
				if extractedFile is not None:
					validFiles.append(extractedFile)

		if len(validFiles) == 0:
			print "No valid files found"
			return None
		id = 0
		i = 1
		while i < len(validFiles):
			if validFiles[i].size > validFiles[id].size:
				id = i
			i += 1
		file = FileItem.fromCompletePath(self.torrentManager.getTorrentFilePath(torrent.name, validFiles[id].name))
		return file

	def executeAction(self, actionData):
		data = actionData

		hashString = data[1]
		tvShow = data[2]
		episodeName = data[3]
		try:
			torrent = self.torrentManager.getTorrent(hashString)
			if torrent.isFinished:
				pattern = episodeName.replace(" ", ".")
				filter = FileFilter(pattern, ["mkv", "avi", "mp4"])
				if data[0] == "move":
					print "TvShowManager: move action"
					fileToMove = self.getTvShowFileFromTorrent(torrent, filter)

					if self.moveTvShow(fileToMove, tvShow, episodeName):
						print "TvShowManager: move succeed"
						time.sleep(0.5)
						XbmcLibraryManager.Instance().scanVideoLibrary()
						print "TvShowManager: delete associated torrent"
						self.torrentManager.removeTorrent(hashString, True)
						return True
					print "TvShowManager: failed to move", torrent.name
					return False
			else:
				print torrent.name, " isn't yet finished"
				return False
		finally:
			pass
		return False

	def executeOnTorrentDownloadedActions(self):
		curs = DatabaseManager.Instance().cursor
		#query = "SELECT id, data FROM AutomatedActions WHERE `trigger`='onTorrentDownloaded' AND notifier='TvShowManager';"
		#curs.execute(query)
		actions = self.actions["onTorrentDownloaded"]
		for a in curs:
			actions.append(a)
		for id, data in actions.iteritems():
			delete = False
			try:
				print "TvShowManager: try to execute action id=", id
				success = self.executeAction(data)
				print "TvShowManager: action (id=", id, ") result=", success
				delete = success
			except KeyError as e:
				print "TvShowManager: error while processing action (id=", id, ") torrent does not exist"
				delete = True
			finally:
				pass

			if delete:
				print "TvShowManager: remove action with id=", id
				delQuery = "DELETE FROM AutomatedActions WHERE id=%s;"
				curs.execute(delQuery, (id, ))
				DatabaseManager.Instance().connector.commit()

	def getSeasonFromTitle(self, title):
		res = re.match(r".*S0?(\d+)E.*", title, re.IGNORECASE)
		if res is not None:
			return res.group(1)
		return 0

	def extractFromRar(self, filter, file):
		possibleFiles = []
		rar = rarfile.RarFile(file)
		for f in rar.infolist():
			if filter.test(FileItem(f.filename, "")):
				possibleFiles.append(f)
		if len(possibleFiles) != 0:
			theFile = possibleFiles[0]
			for f in possibleFiles:
				if f.file_size > theFile.file_size:
					theFile = f
			rar.extract(theFile, os.path.split(file)[0])
			print "TorrentRPC: extract file, ", os.path.split(file)[0], " --- ", theFile.filename, " from rar, ", file
			fakeTorrentFile = TorrentFile()
			fakeTorrentFile.name = theFile.filename
			fakeTorrentFile.size = theFile.file_size
			return fakeTorrentFile
		return None
