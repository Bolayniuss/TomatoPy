import XbmcLibraryManager

__author__ = 'bolay'

import re
import os
from TomatoPy.Scrapper import *
from TomatoPy.SourceMapper import *
from DatabaseManager import DatabaseManager
from XbmcLibraryManager import XbmcLibraryManager
import time


class TvShowManager:
	def __init__(self, torrentManager):
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
		self.tvShowDirectory = parameters[0]

		query = "SELECT title, filter, authorFilter, sizeLimits FROM TrackedTvShows;"
		dbm.cursor.execute(query)
		filter = None
		for (title, nameFilter, authorFilter, sizeLimits) in dbm.cursor:
			sizes = None
			sizeLimits = sizeLimits.split(":")
			if len(sizeLimits[0]) > 0:
				sizes["gt"] = int(sizeLimits[0])
			if len(sizeLimits) > 1:
				if len(sizeLimits[1]) > 0:
					sizes["lt"] = int(sizeLimits[1])
			filter = TorrentFilter(nameFilter.split(":"), authorFilter, sizes)
			self.trackedTvShows.append((title, filter))
		dbm.connector.commit()

	def getNewTvShow(self):

		betaserieEpisodes = BetaserieRSSScrapper(self.bUser).items

		_tmp = []
		for item in betaserieEpisodes:
			for (tvShowTitle, filter) in self.trackedTvShows:
				if re.search(tvShowTitle, item.title, re.IGNORECASE) is not None:
					#print "TvShowManager: Possible new episode found: ", item.title
					item.filter = filter
					item.tvShow = tvShowTitle
					_tmp.append(item)
					break

		betaserieEpisodes = _tmp
		_tmp = []

		tvShowInDir = DirectoryMapper(self.tvShowDirectory, FileFilter(".*", ["mkv", "avi", "mp4"])).files
		for item in betaserieEpisodes:
			for fileItem in tvShowInDir:
				add = True
				if re.search(item.title, fileItem.name, re.IGNORECASE) is not None:
					#print "TvShowManager: Episode ", item.title, " removed because it already exist in source directory ", fileItem.name
					add = False
					break
			if add:
				_tmp.append(item)

		betaserieEpisodes = _tmp
		return betaserieEpisodes

	def addNewToTorrentManager(self, torrentManager):
		episodes = self.getNewTvShow()

		torrents = torrentManager.getTorrents()
		for episode in episodes:

			pattern = episode.title.replace(" ", ".")
			new = True
			for torrent in torrents:
				if re.search(pattern, torrent.name, re.IGNORECASE) is not None:
					#print "TvShowManager: episode ", pattern, " found in torrent list ", torrent.name
					#self.addAutomatedActions(torrent.hashString, episode.tvShow, episode.title)
					new = False
					break
			if new:
				rpbItems = TPBScrapper(episode.title, episode.filter).torrents
				if len(rpbItems) > 0:
					newTorrent = torrentManager.addTorrentURL(rpbItems[0].link)
					self.addAutomatedActions(newTorrent.hashString, episode.tvShow, episode.title)
				else:
					print "No torrent found for ", episode.title

	def addAutomatedActions(self, torrentId, tvShow, episodeName):
		#sql = "INSERT INTO `AutomatedActions` (`id`, `notifier`, `trigger`, `data`) VALUES (NULL, 'asd', 'onTorrentDownloaded', 'asdasd');"
		query = "INSERT INTO `AutomatedActions` (`notifier`, `trigger`, `data`) VALUES ('TvShowManager', 'onTorrentDownloaded', %s);"
		data = "&&".join(["move", torrentId, tvShow, episodeName])
		print query, data
		DatabaseManager.Instance().cursor.execute(query, (data, ))
		DatabaseManager.Instance().connector.commit()

	def executeAction(self, actionData):
		data = actionData.split("&&")

		hashString = data[1]
		tvShow = data[2]
		episodeName = data[3]
		try:
			torrent = self.torrentManager.getTorrent(hashString)
			if torrent.percentDone >= 1:
				pattern = episodeName.replace(" ", ".")
				filter = FileFilter(pattern, ["mkv", "avi", "mp4"])
				if data[0] == "move":
					print "TvShowManager: move action"
					dstDir = os.path.join(self.tvShowDirectory, tvShow, "Saison " + self.getSeasonFromTitle(episodeName))
					print "TvShowManager: try to move ", torrent.name, " to ", dstDir
					if self.torrentManager.moveFile(torrent, filter, dstDir, episodeName):
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
		query = "SELECT id, data FROM AutomatedActions WHERE `trigger`='onTorrentDownloaded' AND notifier='TvShowManager';"
		curs.execute(query)
		actions = []
		for a in curs:
			actions.append(a)
		for (id, data, ) in actions:
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
				#curs.fetchall()
				DatabaseManager.Instance().connector.commit()

	def getSeasonFromTitle(self, title):
		res = re.match(r".*S0?(\d+)E.*", title, re.IGNORECASE)
		if res is not None:
			return res.group(1)
		return 0
