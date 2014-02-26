__author__ = 'bolay'

from DatabaseManager import DatabaseManager
import urllib2
import json
import os
from TomatoPy.AutomatedActionExecutor import *
import Tools
from XbmcLibraryManager import XbmcLibraryManager
from TomatoPy.TorrentRPC import *


class ReplicatorManager(AutomatedActionsExecutor):
	def __init__(self, user, torrentManager):
		"""
		:type user: str
		:type torrentManager: TorrentManager
		:param user:
		:param torrentManager:
		:return:
		"""
		super(ReplicatorManager, self).__init__("ReplicatorManager")
		self.user = user
		self.serviceName = "Replicator"
		self.dbm = DatabaseManager.Instance()
		self.torrentManager = torrentManager
		self.replicatorActions = {}
		self.replicatorServers = []

		sql = "SELECT * FROM RemoteServices WHERE `ServiceName`=%s;"
		self.dbm.cursor.execute(sql, (self.serviceName, ))
		for res in self.dbm.cursor:
			self.replicatorServers.append({"name": res[1], "url": res[2]})

		# Load destinations from DB
		self.destinations = {}
		sql = "SELECT * FROM TrackedDestinations;"
		self.dbm.cursor.execute(sql)
		for res in self.dbm.cursor:
			self.destinations[res[0]] = res[1]

		self.loadRemoteActions()
		self.processReplicatorActions()
		self.loadActions()

	def loadRemoteActions(self):
		for server in self.replicatorServers:
			print "ReplicatorManager: Loading actions from remote server, ", server["name"]
			url = server["url"]+"?q=getReplicatorActions&user="+self.user

			jsonData = urllib2.urlopen(url).read()
			#print "ReplicatorManager: jsonData=", jsonData
			data = json.loads(jsonData)
			if server["name"] not in self.replicatorActions:
				self.replicatorActions[server["name"]] = []
			self.replicatorActions[server["name"]].append(data)

	def processReplicatorActions(self):
		for serverName, serverActionsList in self.replicatorActions.iteritems():
			for actionsDict in serverActionsList:
				for torrentName, actions in actionsDict.iteritems():
					actionParams = []
					for action in actions:

						# Test if source exist
						if action["destinationName"] in self.destinations:
							destinationPath = os.path.join(self.destinations[action["destinationName"]], action["destinationRelativePath"])
							if not os.path.exists(destinationPath):
								actionParams.append(action["torrentFileName"])
								actionParams.append(destinationPath)

					if actionParams:
						# Add Torrent
						t = self.torrentManager.addTorrentURL(action["torrentData"])

						# Add move action with torrentHash, fileName, destinationPath
						aa = "move&&"+t.hash+"&&"+"&&".join(actionParams)
						sql = "INSERT INTO AutomatedActions (notifier, `trigger`, `data`) VALUES(%s, %s, %s);"
						self.dbm.cursor.execute(sql, (self.actionNotifierName, "onTorrentDownloaded", aa))
						self.dbm.connector.commit()

						print "ReplicatorManager: Add new automated action from server=", serverName, ", ", aa

	def executeAction(self, data):
		if data[0] == "move":
			hashString = data[1]
			try:
				torrent = self.torrentManager.getTorrent(hashString)
				if torrent.isFinished:
					nFiles = (len(data)-2)/2
					success = True
					for i in xrange(nFiles):
						filename = data[2+i*2]
						destinationPath = data[3+i*2]
						fileToMove = self.torrentManager.getTorrentFilePath(torrent.name, filename)

						if Tools.FileSystemHelper.Instance().move(fileToMove, destinationPath):
							print "ReplicatorManager: file (", (i+1), "/", nFiles, ") move succeeded."
							#time.sleep(0.5)
						else:
							success = False
					if success:
						XbmcLibraryManager.Instance().scanVideoLibrary()
						print "ReplicatorManager: delete associated torrent"
						self.torrentManager.removeTorrent(hashString, True)
					else:
						print "TvShowManager: failed to move", torrent.name
					return success
				else:
					print torrent.name, " isn't yet finished"
					return False
			finally:
				pass
		return False

	def executeOnTorrentDownloadedActions(self):
		#print self.actions
		curs = DatabaseManager.Instance().cursor
		actions = self.actions["onTorrentDownloaded"]
		#for a in curs:
		#	actions.append(a)
		for id, data in actions.iteritems():
			delete = False
			try:
				print "ReplicatorManager: try to execute action id=", id
				success = self.executeAction(data)
				print "ReplicatorManager: action (id=", id, ") result=", success
				delete = success
			except KeyError as e:
				print "ReplicatorManager: error while processing action (id=", id, ") torrent does not exist"
				delete = True
			finally:
				pass

			if delete:
				print "ReplicatorManager: remove action with id=", id
				delQuery = "DELETE FROM AutomatedActions WHERE id=%s;"
				curs.execute(delQuery, (id, ))
				DatabaseManager.Instance().connector.commit()