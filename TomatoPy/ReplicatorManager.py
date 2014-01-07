__author__ = 'bolay'

from DatabaseManager import DatabaseManager
import urllib2
import json
import os
from AutomatedActionExecutor import *


class ReplicatorManager(AutomatedActionsExecutor):
	def __init__(self, user, torrentManager):
		super(ReplicatorManager, self).__init__("ReplicatorManager")
		self.user = user
		self.serviceName = "Replicator"
		self.dbm = DatabaseManager.Instance()
		self.torrentManager = torrentManager
		self.replicatorActions = []
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

	def loadRemoteActions(self):
		for server in self.replicatorServers:
			print "ReplicatorManager : Loading actions from remote server, ", server["name"]
			url = server["url"]+"?q=getReplicatorActions&user="+self.user

			jsonData = urllib2.urlopen(url).read()
			print "ReplicatorManager : jsonData=", jsonData
			self.replicatorActions.append(json.loads(jsonData))

	def processReplicatorActions(self):
		for k, action in self.replicatorActions.iteritems():

			# Test if source exist
			if action.destinationName in self.destinations:
				destinationPath = os.path.join(self.destinations[action.destinationName], action.destinationRelativePath)
				# if path does not exist create directories (not here)
				#try:
				#	os.makedirs(os.path.dirname(destinationPath))
				#except OSError:
				#	pass
				#finally:
				#	pass

				# Test if destination file does not already exist
				if not os.path.exists(destinationPath):

					# Add Torrent
					t = self.torrentManager.addTorrentURL(action.torrentData)

					# Add move action with torrentHash, fileName, destinationPath
					aa = "move&&"+t.hashString+"&&"+action.torrentFileName+"&&"+destinationPath
					sql = "INSERT INTO AutomatedActions (notifier, trigger, data) VALUES(%s, %s, %s);"
					self.dbm.cursor.execute(sql, (self.actionNotifierName, "onTorrentDownloaded", aa))
					self.dbm.connector.commit()

					print "ReplicatorManager : Add new automated action, ", aa