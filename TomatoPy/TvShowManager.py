# -*- coding: utf8 -*-
#
__author__ = 'bolay'

import re
import os
import time
import logging

import rarfile

from DatabaseManager import DatabaseManager
import Tools


from Notifications import NotificationManager, Expiration
from .ScrapperItem import EpisodeItem
from .Scrapper import BetaserieRSSScrapper, TPBScrapper
from .SourceMapper import DirectoryMapper, TorrentFilter, FileFilter, FileItem

from XbmcLibraryManager import XbmcLibraryManager
from .AutomatedActionExecutor import AutomatedActionsExecutor
from .TorrentRPC import TorrentFile


class TrackedTvShow:
	def __init__(self, title, torrentFilter):
		self.title = title
		self.torrentFilter = torrentFilter


class TrackedEpisode(EpisodeItem):
	def __init__(self, episodeItem, trackedTvShow):
		"""

		:param episodeItem:
		:param trackedTvShow:
		:type episodeItem: EpisodeItem
		:type trackedTvShow: TrackedTvShow
		:return:
		"""

		super(TrackedEpisode, self).__init__(title=episodeItem.title,
		                                     tvShow=episodeItem.tvShow,
		                                     season=episodeItem.season,
		                                     episodeNumber=episodeItem.episodeNumber)
		#self.tvShow = episodeItem.tvShow
		#self.title = episodeItem.title
		#self.episodeNumber = episodeItem.episodeNumber
		#self.season = episodeItem.season

		self.trackedTvShow = trackedTvShow


class TvShowManager(AutomatedActionsExecutor):
	def __init__(self, torrentManager):
		super(TvShowManager, self).__init__("TvShowManager")

		self.logger = logging.getLogger("TvShowManager")

		dbm = DatabaseManager.Instance()
		self.torrentManager = torrentManager

		self.trackedTvShows = []  # tv shows that can be downloaded // Get them form db

		query = "SELECT parameters FROM Parameters WHERE name='TvShowManager' LIMIT 1"
		dbm.cursor.execute(query)
		(parametersString, ) = dbm.cursor.fetchone()
		parameters = parametersString.split("&&")
		self.bUser = parameters[1]
		self.tvShowDirectory = u"" + parameters[0]
		self.fileSystemEncoding = None
		if len(parameters) > 2:
			self.fileSystemEncoding = parameters[2]

		query = "SELECT title, filter, authorFilter, sizeLimits FROM TrackedTvShows;"
		dbm.cursor.execute(query)

		for (title, nameFilter, authorFilter, sizeLimits) in dbm.cursor:
			sizes = {}
			sizeLimits = sizeLimits.split(":")
			if len(sizeLimits[0]) > 0:
				sizes["gt"] = int(sizeLimits[0])
			if len(sizeLimits) > 1:
				if len(sizeLimits[1]) > 0:
					sizes["lt"] = int(sizeLimits[1])
			filter_ = TorrentFilter(nameFilter.split(":"), authorFilter, sizes)
			self.trackedTvShows.append(TrackedTvShow(title, filter_))
		dbm.connector.commit()

		#TODO: replace this line
		self.registeredEpisodeProviders = [BetaserieRSSScrapper(self.bUser)]
		self.registeredTorrentProviders = [TPBScrapper()]

		self.directoryMapper = DirectoryMapper(self.tvShowDirectory, r"(.*)\.(mkv|avi|mp4|wmv)$", self.fileSystemEncoding)

		self.loadActions()

	def getTrackedTvShow(self, episode):
		"""
		Returns the associate tracked tv show if it exists, otherwise return None
		:param episode: the episode to test
		:type episode: EpisodeItem
		:return: The associate tracked tv show if exists, otherwise return None
		:rtype: TrackedTvShow
		"""
		if episode.tvShow:
			for trackedTvShow in self.trackedTvShows:
				if episode.tvShow.lower() == trackedTvShow.title.lower():
					return trackedTvShow
		return None

	def getNewEpisodes(self):
		episodes = []
		for episodeProvider in self.registeredEpisodeProviders:
			for episode in episodeProvider.getEpisodes():
				self.logger.debug("Episode : %s (%s)", episode.title, episode.tvShow)

				trackedTvShow = self.getTrackedTvShow(episode)
				if trackedTvShow:
					#self.logger.debug("is in tracked tv shows")

					if not self.directoryMapper.fileExists(episode.title):
						self.logger.debug("is not in source directory")

						pattern = self.deleteBadChars(episode.title)
						pattern = pattern.replace(" ", ".*")
						if not self.torrentManager.searchInTorrents(pattern):
							self.logger.debug("doesn't exists in torrentManager.torrents")

							episodes.append(TrackedEpisode(episode, trackedTvShow))
		return episodes

	def addNewToTorrentManager(self, episodes=None):
		if not episodes:
			episodes = self.getNewEpisodes()
		# TODO: fix multi torrent providers function
		self.logger.info("Episodes ready for download:")
		for episode in episodes:
			torrentItems = []
			for torrentProvider in self.registeredTorrentProviders:
				torrentItems = torrentProvider.getTorrents(episode.title, episode.trackedTvShow.torrentFilter)
				if torrentItems:
					break

			if len(torrentItems) > 0:
				newTorrent = self.torrentManager.addTorrentURL(torrentItems[0].link)
				if newTorrent:
					self.addAutomatedActions(newTorrent.hash, episode.trackedTvShow.title, episode.title)
					self.logger.debug("New torrent added for episode %s", episode.title)
					NotificationManager.Instance().addNotification(episode.title, "TvShowManager: New", Expiration(weeks=4))
				else:
					self.logger.info("No torrent added for %s", episode.title)
					NotificationManager.Instance().addNotification("Unable to add %s to TM" % episode.title, "TvShowManager: Error", Expiration())
			else:
				NotificationManager.Instance().addNotification("No torrent found for %s" % episode.title, "TvShowManager: Error", Expiration())
				self.logger.info("No torrent found for %s", episode.title)

	def getNewTvShow(self):
		"""
		Retrieves new episodes from Betaserie and then retain only those that doesn't exists
		in destination directories.
		"""
		self.logger.debug("getNetTvShow | Get items from BS")
		betaserieEpisodes = BetaserieRSSScrapper(self.bUser).items

		_tmp = []
		for item in betaserieEpisodes:
			for (tvShowTitle, filter_) in self.trackedTvShows:
				if re.search(re.escape(tvShowTitle), item.title, re.IGNORECASE) is not None:
					self.logger.debug("getNetTvShow | Likely new episode found: %s", item.title)
					item.filter = filter_
					item.tvShow = tvShowTitle
					_tmp.append(item)
					break

		betaserieEpisodes = _tmp
		_tmp = []

		tvShowInDir = DirectoryMapper(self.tvShowDirectory, r".*(mkv|avi|mp4|wmv)$", self.fileSystemEncoding).files
		for item in betaserieEpisodes:
			add = True
			for fileItem in tvShowInDir:
				#if True or fileItem.name[0] == "H":
				#	print "look for ", re.escape(item.title), " in ", fileItem.name
				if re.search(re.escape(item.title), fileItem.name, re.IGNORECASE) is not None:
					self.logger.debug("getNewTvShow | Episode %s removed because it already exist in source directory %s", item.title, fileItem.name)
					add = False
					break
			if add:
				_tmp.append(item)
				self.logger.debug("new item %s ready to download", item.title)

		betaserieEpisodes = _tmp
		return betaserieEpisodes

	def addAutomatedActions(self, torrentId, tvShow, episodeName):
		self.logger.debug("addAutomatedActions | new (%s, %s, %s)", torrentId, tvShow, episodeName)
		query = "INSERT INTO `AutomatedActions` (`notifier`, `trigger`, `data`) VALUES ('TvShowManager', 'onTorrentDownloaded', %s);"
		data = "&&".join(["move", torrentId, tvShow, episodeName])
		self.logger.info("add automated action, quest=%s, data=%s", query, data)
		DatabaseManager.Instance().cursor.execute(query, (data, ))
		DatabaseManager.Instance().connector.commit()

	def getEpisodeFinalPath(self, file_, tvShow, episodeName):
		"""
		:param file_: file to move
		:type file_ : FileItem
		:param tvShow: tv show name
		:type tvShow: unicode
		:param episodeName: episode name (e.g. {tvShow} S01E01)
		:type episodeName: unicode
		:return: The final destination path for this episode
		:rtype: unicode
		"""

		season = self.getSeasonFromTitle(episodeName)
		dst = os.path.join(self.tvShowDirectory, tvShow, "Saison " + season, episodeName + "." + file_.extension)
		return dst

	def getTvShowFileFromTorrent(self, torrent, filter_):
		"""
		:param torrent:
		:type torrent: TorrentObject
		:param filter_:
		:type filter_: FileFilter
		"""
		files = self.torrentManager.getTorrentFiles(torrent.hash)
		rarFilter = FileFilter(".*", ["rar"])
		validFiles = []
		for file_ in files:
			fileItem = FileItem.fromFilename(file_.name, "")
			if filter_.test(fileItem):
				validFiles.append(file_)
			elif rarFilter.test(fileItem):
				extractedFile = self.extractFromRar(filter_, self.torrentManager.getTorrentFilePath(torrent.name, file_.name))
				if extractedFile is not None:
					validFiles.append(extractedFile)

		if len(validFiles) == 0:
			mediaFilter = FileFilter(".*", ["mkv", "mp4", "avi", "wmv"])
			for file_ in files:
				if mediaFilter.test(FileItem.fromFilename(file_.name, "")):
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
		"""
		Execute generic action

		:param list actionData: list
		:return bool: success
		"""
		data = actionData

		hashString = data[1]
		tvShow = data[2]
		episodeName = data[3]
		try:
			torrent = self.torrentManager.getTorrent(hashString)
			if torrent.isFinished:
				pattern = self.deleteBadChars(episodeName)
				pattern = pattern.replace(" ", ".")
				filter_ = FileFilter(pattern, ["mkv", "avi", "mp4"])
				if data[0] == "move":
					self.logger.info("move action")
					try:
						fileToMove = self.getTvShowFileFromTorrent(torrent, filter_)
						if fileToMove:
							success = False
							destinationPath = self.getEpisodeFinalPath(fileToMove, tvShow, episodeName)
							sourceFilePath = fileToMove.getFullPath()
							self.logger.info("try to move %s* to %s", sourceFilePath, destinationPath)
							if len(sourceFilePath) > 0:
								success = Tools.FileSystemHelper.Instance().move(sourceFilePath, destinationPath)
							if success:
								self.logger.info("move succeed")
								time.sleep(0.5)
								XbmcLibraryManager.Instance().scanVideoLibrary(
									Tools.PathSubstitution.Instance().substitute(os.path.dirname(destinationPath))
								)
								self.logger.info("delete associated torrent")
								self.torrentManager.removeTorrent(hashString, True)
								NotificationManager.Instance().addNotification(
									torrent.name,
									"TvShowManager: Done", Expiration(weeks=4)
								)
								return True
							# else
							self.logger.warn("Failed to move %s", torrent.name)
							NotificationManager.Instance().addNotification(
								"Move failure in %s" % torrent.name,
								"TvShowManager: Errors", Expiration()
							)
						else:
							self.logger.warn("No valid file found in %s", torrent.name)
							NotificationManager.Instance().addNotification(
								"No valid file found in %s" % torrent.name,
								"TvShowManager: Errors", Expiration()
							)
						return False
					except IOError:
						self.logger.error("error while moving file, file does not exists.")
						NotificationManager.Instance().addNotification(
							"File doesn't exists %s" % torrent.name,
							"TvShowManager: Errors", Expiration()
						)
			else:
				self.logger.info("Torrent %s isn't yet finished", torrent.name)
				prc = 0
				try:
					prc = float(torrent.downloaded) / torrent.size
				except Exception:
					pass
				NotificationManager.Instance().addNotification(
					"%s %s" % ('{0:.0%}'.format(prc), torrent.name),
					"TvShowManager: Downloading", Expiration()
				)
				return False
		finally:
			pass
		return False

	def executeOnTorrentDownloadedActions(self):
		"""
		Execute onTorrentDownloaded action
		"""
		curs = DatabaseManager.Instance().cursor
		#query = "SELECT id, data FROM AutomatedActions WHERE `trigger`='onTorrentDownloaded' AND notifier='TvShowManager';"
		#curs.execute(query)
		actions = self.actions["onTorrentDownloaded"]
		for a in curs:
			actions.append(a)
		for id_, data in actions.iteritems():
			try:
				self.logger.info("try to execute action id=%d", id_)
				success = self.executeAction(data)
				self.logger.info("action (id=%d) result=%d", id_, success)
				delete = success
			except KeyError:
				self.logger.info("error while processing action (id=%d) torrent does not exist", id_)
				delete = True
			finally:
				pass

			if delete:
				self.logger.info("remove action with id=%d", id_)
				delQuery = "DELETE FROM AutomatedActions WHERE id=%s;"
				curs.execute(delQuery, (id_, ))
				DatabaseManager.Instance().connector.commit()

	def extractFromRar(self, filter_, file_):
		"""
		Extract valid files from RAR file
		:param filter_: valid file filter
		:type filter_: FileFilter
		:param file_: rar file path
		:type file_: unicode
		"""
		possibleFiles = []
		rar = rarfile.RarFile(file_)
		for f in rar.infolist():
			if filter_.test(FileItem.fromFilename(f.filename, "")):
				possibleFiles.append(f)
		if len(possibleFiles) != 0:
			theFile = possibleFiles[0]
			for f in possibleFiles:
				if f.file_size > theFile.file_size:
					theFile = f
			rar.extract(theFile, os.path.split(file_)[0])
			self.logger.info("extract file, %s --- %s from rar, %s", os.path.split(file_)[0], theFile.filename, file_)
			fakeTorrentFile = TorrentFile()
			fakeTorrentFile.name = theFile.filename
			fakeTorrentFile.size = theFile.file_size
			return fakeTorrentFile
		return None

	@staticmethod
	def getSeasonFromTitle(title):
		"""
		Static method to get tv show season number from file name (title)
		:param title:
		:type title: unicode
		"""
		res = re.match(r".*S0?(\d+)E.*", title, re.IGNORECASE)
		if res is not None:
			return res.group(1)
		return None

	@staticmethod
	def deleteBadChars(inp):
		"""
		Remove bad characters from inp. Useful when we want to use inp as a regex pattern.
		:param unicode inp:
		:return:
		:rtype unicode:
		"""
		bad_chars = '(){}<>[]*'
		badCharsDict = dict((ord(char), None) for char in bad_chars)
		pattern = inp.translate(badCharsDict)
		return pattern
