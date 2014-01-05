__author__ = 'bolay'

from DatabaseManager import DatabaseManager

class ReplicatorManager:
	def __init__(self):
		self.dbm = DatabaseManager.Instance()

		self.actions = []
		sql = "SELECT * FROM ReplicatorActions;"