# -*- coding: utf-8 -*-
#
__author__ = 'Michael Bolay'

import time
import json
import io
import urllib2, urllib
from exceptions import NotImplementedError
from Singleton import Singleton
from DatabaseManager import DatabaseManager


class Serializable(object):

	def toDict(self):
		raise NotImplementedError()


class UnSerializable(object):
	@staticmethod
	def fromDict(data):
		raise NotImplementedError


class Expiration(Serializable, UnSerializable, object):
	def __init__(self, seconds=0, minutes=0, hours=0, days=0, weeks=0, add_now_ts=True):
		self.expiration = 0
		self.increment(seconds, minutes, hours, days, weeks)
		if add_now_ts:
			self.expiration += time.time()

	def increment(self, seconds=0, minutes=0, hours=0, days=0, weeks=0):
		self.expiration += (seconds + (60 * (minutes + 60 * (hours + 24 * (days + 7 * weeks)))))

	def isExpired(self):
		return time.time() >= self.expiration

	def toDict(self):
		return {"expiration": self.expiration}

	@staticmethod
	def fromDict(data):
		try:
			return Expiration(seconds=data["expiration"], add_now_ts=False)
		except TypeError:
			return None
		except KeyError:
			return None


class Notification(Serializable, UnSerializable, object):
	def __init__(self, title, expiration=None):
		self.title = title
		self.expiration = expiration

	def toDict(self):
		a = {"title": self.title}
		if self.expiration:
			a["expiration"] = self.expiration.toDict()
		return a

	@staticmethod
	def fromDict(data):
		try:
			expiration = None
			try:
				expiration = Expiration.fromDict(data["expiration"])
			except KeyError:
				pass
			return Notification(data["title"], expiration)
		except TypeError:
			return None
		except KeyError:
			return None


@Singleton
class NotificationManager(object):
	def __init__(self):
		self.url = ""
		self.user = ""
		self.serviceName = "NotificationServer"
		self.notifications = {}
		if DatabaseManager.Instance().cursor:
			sql = "SELECT * FROM RemoteServices WHERE `ServiceName`=%s LIMIT 1;"
			DatabaseManager.Instance().cursor.execute(sql, (self.serviceName, ))
			for res in DatabaseManager.Instance().cursor:
				data = res[2].split("&&")
				self.user = data[0]
				self.url = data[1]
				break
		else:
			self.user = "chalet-ms"
			self.url = "http://bandb.dnsd.info/cgi-bin/replicator"

	def addNotification(self, title, category='general', expiration=None):
		"""
		Add a notification to the manager.
		:param str title:
		:param str category:
		:param Expiration expiration:
		:return:
		"""
		if category not in self.notifications:
			self.notifications[category] = []

		self.notifications[category].append(Notification(title, expiration))

	def getNotification(self, listExpired=False):
		if listExpired:
			return self.notifications
		return dict(map(lambda (k, v): (k, filter(lambda x: x.expiration and not x.expiration.isExpired(), v)), self.notifications.iteritems()))

	def serialize(self):
		notifications = dict(map(lambda (k, v): (k, map(lambda x: x.toDict(), v)), self.getNotification(True).iteritems()))
		return {"notifications": notifications}

	def unSerialize(self, data):
		notifications_by_cat = data["notifications"]
		self.notifications.clear()
		for (k, v) in notifications_by_cat.iteritems():
			for n in v:
				try:
					notification = Notification.fromDict(n)
					if notification.expiration and not notification.expiration.isExpired():
						if k not in self.notifications:
							self.notifications[k] = []
						self.notifications[k].append(notification)
				except KeyError:
					pass
				except TypeError:
					pass

	def getFromRemoteServer(self):
		url = self.url + "?q=getNotifications&user=" + self.user

		jsonData = urllib2.urlopen(url).read()
		try:
			data = json.loads(jsonData)
			self.unSerialize(data)
		except ValueError:
			pass

	def saveToRemoteServer(self):
		url = self.url + "?" + urllib.urlencode((("q", "setNotifications"), ("user", self.user), ("data", json.dumps(self.serialize()))))
		urllib2.urlopen(url).read()

	def write_as_json(self, path):
		with io.open(path, 'wb') as fp:
			obj = self.serialize()
			json.dump(obj, fp)
			fp.close()

	def load_from_json(self, path):
		try:
			with io.open(path, 'rb') as fp:
				obj = json.load(fp)
				fp.close()

				self.unSerialize(obj)
		except IOError:
			pass


