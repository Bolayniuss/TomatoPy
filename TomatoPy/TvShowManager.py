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
import logging


class TvShowManager(AutomatedActionsExecutor):
	def __init__(self, torrentManager):
		super(TvShowManager, self).__init__("TvShowManager")

		self.logger = logging.getLogger("TvShowManager")
		self.logger.debug("init")

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
				#if True or fileItem.name[0] == "H":
				#	print "look for ", re.escape(item.title), " in ", fileItem.name
				if re.search(re.escape(item.title), fileItem.name, re.IGNORECASE) is not None:
					#print "TvShowManager: Episode ", item.title, " removed because it already exist in source directory ", fileItem.name
					add = False
					break
			if add:
				_tmp.append(item)
				self.logger.debug("new item %s ready to download", item.title)

		betaserieEpisodes = _tmp
		return betaserieEpisodes

	def deleteBadChars(self, inp):
		"""

		:param unicode inp:
		:return:
		:rtype unicode:
		"""
		bad_chars = '(){}<>[]*'
		badCharsDict = dict((ord(char), None) for char in bad_chars)
		pattern = inp.translate(badCharsDict)
		return pattern

	def addNewToTorrentManager(self, torrentManager):
		self.logger.debug("begin: addNewToTorrentManager")
		episodes = self.getNewTvShow()

		torrents = torrentManager.getTorrents()

		for episode in episodes:
			pattern = self.deleteBadChars(episode.title)
			pattern = pattern.replace(" ", ".*?")
			new = True
			for torrent in torrents:
				print "pattern:", pattern, "torrent.name:", torrent.name
				if re.search(pattern, torrent.name, re.IGNORECASE) is not None:
					new = False
					break
			if new:
				rpbItems = TPBScrapper(episode.title, episode.filter).torrents
				if len(rpbItems) > 0:
					newTorrent = torrentManager.addTorrentURL(rpbItems[0].link)
					if newTorrent:
						self.addAutomatedActions(newTorrent.hash, episode.tvShow, episode.title)
						self.logger.debug("New torrent added for episode %s", episode.title)
					else:
						self.logger.info("No torrent added for %s", episode.title)
				else:
					self.logger.info("No torrent found for %s", episode.title)
		self.logger.debug("end: addNewToTorrentManager")

	def addAutomatedActions(self, torrentId, tvShow, episodeName):
		#sql = "INSERT INTO `AutomatedActions` (`id`, `notifier`, `trigger`, `data`) VALUES (NULL, 'asd', 'onTorrentDownloaded', 'asdasd');"
		query = "INSERT INTO `AutomatedActions` (`notifier`, `trigger`, `data`) VALUES ('TvShowManager', 'onTorrentDownloaded', %s);"
		data = "&&".join(["move", torrentId, tvShow, episodeName])
		self.logger.info("add automated action, quest=%s, data=%s", query, data)
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
		self.logger.info("try to move %s* to %s", sourceFilePath, dst)
		if len(sourceFilePath) > 0:
			return Tools.FileSystemHelper.Instance().move(sourceFilePath, dst)
		return False

	def getTvShowFileFromTorrent(self, torrent, filter):
		files = self.torrentManager.getTorrentFiles(torrent.hash)
		rarFilter = FileFilter(".*", ["rar"])
		validFiles = []
		for file_ in files:
			fileItem = FileItem(file_.name, "")
			if filter.test(fileItem):
				validFiles.append(file_)
			elif rarFilter.test(fileItem):
				extractedFile = self.extractFromRar(filter, self.torrentManager.getTorrentFilePath(torrent.name, file_.name))
				if extractedFile is not None:
					validFiles.append(extractedFile)

		if len(validFiles) == 0:
			mediaFilter = FileFilter(".*", ["mkv", "mp4", "avi", "wmv"])
			for file_ in files:
				if mediaFilter.test(FileItem(file_.name, "")):
					validFiles.append(file_)
		if len(validFiles) == 0:
			self.logger.info("No valid files found")
			return None
		id_ = 0
		i = 1
		while i < len(validFiles):
			if validFiles[i].size > validFiles[id_].size:
				id_ = i
			i += 1
		self.logger.debug("validFile id_=%d, name=%s", id_, validFiles[id_].name)
		try:
			completePath = self.torrentManager.getTorrentFilePath(torrent.name, validFiles[id_].name)
		except IOError, e:
			raise e
		file_ = FileItem.fromCompletePath(completePath)
		return file_

	def executeAction(self, actionData):
		data = actionData

		hashString = data[1]
		tvShow = data[2]
		episodeName = data[3]
		try:
			torrent = self.torrentManager.getTorrent(hashString)
			if torrent.isFinished:
				pattern = self.deleteBadChars(episodeName)
				pattern = pattern.replace(" ", ".")
				filter = FileFilter(pattern, ["mkv", "avi", "mp4"])
				if data[0] == "move":
					self.logger.info("move action")
					try:
						fileToMove = self.getTvShowFileFromTorrent(torrent, filter)
						if fileToMove:
							if self.moveTvShow(fileToMove, tvShow, episodeName):
								self.logger.info("move succeed")
								time.sleep(0.5)
								XbmcLibraryManager.Instance().scanVideoLibrary()
								self.logger.info("delete associated torrent")
								self.torrentManager.removeTorrent(hashString, True)
								return True
							self.logger.warn("Failed to move %s", torrent.name)
						else:
							self.logger.warn("No valid file found in %s", torrent.name)
						return False
					except IOError, e:
						self.logger.error("error while moving file, file does not exists.")
			else:
				self.logger.info("Torrent %s isn't yet finished", torrent.name)
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
				self.logger.info("try to execute action id=%d", id)
				success = self.executeAction(data)
				self.logger.info("action (id=%d) result=%d", id, success)
				delete = success
			except KeyError as e:
				self.logger.info("error while processing action (id=%d) torrent does not exist", id)
				delete = True
			finally:
				pass

			if delete:
				self.logger.info("remove action with id=%d", id)
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
			self.logger.info("extract file, %s --- %s from rar, %s", os.path.split(file)[0], theFile.filename, file)
			fakeTorrentFile = TorrentFile()
			fakeTorrentFile.name = theFile.filename
			fakeTorrentFile.size = theFile.file_size
			return fakeTorrentFile
		return None
