__author__ = 'bolay'
import os
import re
import mysql.connector


class Rule:
	name = ''
	type = ''

	def __init__(self, mysqlData):
		self.name = mysqlData.name
		self.type = mysqlData.type

	def isUsable(self):
		return True


class FileRule(Rule):
	def __init__(self, mysqlData):
		super(Rule, self).__init__(self, mysqlData)

	def apply(self, file):
		raise NotImplementedError('')


class TorrentRule(Rule):
	def __init(self, mysqlData):
		super(Rule, self).__init__(self, mysqlData)


class MoveRule(FileRule):
	fromPattern = ''
	toPattern = ''
	options = {}

	def MoveRule(self, mysqlData):
		super(FileRule, self).__init__(self, mysqlData)
		self.fromPattern = mysqlData.fromPattern
		self.toPattern = mysqlData.toPattern
		self.options = mysqlData.options

	def isUsable(self, file):
		usable = super(FileRule, self).isUsable()



class UnRarRule(FileRule):
	def __init__(self, mysqlData):
		super(FileRule, self).__init__(self, mysqlData)

	def apply(self, file):


