__author__ = 'bolay'

from DatabaseManager import DatabaseManager


class AutomatedAction:
	def __init__(self, type, parameters):
		"""
		:type type : str
		:type parameters : list
		:param type:
		:param parameters:
		:return:
		"""
		self.type = type
		self.parameters = parameters

	def join(self, delimiter="&&"):
		joined = delimiter.join(self.parameters)
		if len(joined) > 0:
			joined = type + delimiter + joined
		return joined

	@staticmethod
	def fromString(str):
		data = str.split("&&")
		if len(data[0]) > 0:
			type = data.pop(0)
			return AutomatedAction(type, data)
		return None


class AutomatedActionsExecutor(object):
	def __init__(self, actionNotifierName):
		self.actionNotifierName = actionNotifierName
		self.actions = {"onBegin": {}, "onTorrentDownloaded": {}, "onEnd": {}}
		self.actionsLoaded = False

	def loadActions(self, reload=False):
		if not self.actionsLoaded or reload:
			curs = DatabaseManager.Instance().cursor
			query = "SELECT id, `trigger`, data FROM AutomatedActions WHERE notifier=%s;"
			curs.execute(query, (self.actionNotifierName, ))
			for action in curs:
				data = action[2].split("&&")
				self.actions[action[1]][action[0]] = data
			self.actionsLoaded = True