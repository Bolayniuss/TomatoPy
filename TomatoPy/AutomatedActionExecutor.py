__author__ = 'bolay'

from DatabaseManager import DatabaseManager


class AutomatedAction:
	def __init__(self, type_, parameters):
		"""
		:type type_ : str
		:type parameters : list
		:param type_:
		:param parameters:
		:return:
		"""
		self.type = type_
		self.parameters = parameters

	def join(self, delimiter="&&"):
		joined = delimiter.join(self.parameters)
		if len(joined) > 0:
			joined = type + delimiter + joined
		return joined

	@staticmethod
	def fromString(str_):
		data = str_.split("&&")
		if len(data[0]) > 0:
			type_ = data.pop(0)
			return AutomatedAction(type_, data)
		return None


class AutomatedActionsExecutor(object):
	def __init__(self, actionNotifierName):
		self.actionNotifierName = actionNotifierName
		self.actions = {"onBegin": {}, "onTorrentDownloaded": {}, "onEnd": {}}
		self.actionsLoaded = False

	def loadActions(self, reload_=False):
		if not self.actionsLoaded or reload_:
			curs = DatabaseManager.Instance().cursor
			query = "SELECT id, `trigger`, data FROM AutomatedActions WHERE notifier=%s;"
			curs.execute(query, (self.actionNotifierName, ))
			for action in curs:
				data = action[2].split("&&")
				self.actions[action[1]][action[0]] = data
			self.actionsLoaded = True