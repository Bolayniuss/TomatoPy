__author__ = 'bolay'

from DatabaseManager import DatabaseManager

class AutomatedActionsExecutor:
	def __init__(self, actionNotifierName):
		self.actionNotifierName = actionNotifierName
		self.actions = {"onBegin": {}, "onTorrentDownloaded": {}, "onEnd": {}}
		self.actionsLoaded = False

	def loadActions(self, reload=False):
		if not self.actionsLoaded or reload:
			curs = DatabaseManager.Instance().cursor
			query = "SELECT id, trigger, data FROM AutomatedActions WHERE notifier=%s;"
			curs.execute(query, (self.actionNotifierName, ))
			for action in curs:
				data = action[2].split("&&")
				self.actions[action[1]][action[0]] = data
			self.actionsLoaded = True