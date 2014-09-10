# -*- coding: utf8 -*-
#
__author__ = 'bolay'

import httplib
import json
import random
import logging

from Singleton import Singleton
from DatabaseManager import DatabaseManager


@Singleton
class XbmcLibraryManager:

	def __init__(self):
		self.logger = logging.getLogger(__name__)
		dbm = DatabaseManager.Instance()
		query = "SELECT parameters FROM Parameters WHERE name='XbmcLibraryManager' LIMIT 1"
		dbm.cursor.execute(query)
		(parametersString, ) = dbm.cursor.fetchone()
		parameters = parametersString.split("&&")

		self.host = parameters[0]
		self.port = int(parameters[1])
		self.user = None
		self.pwd = None
		if len(parameters) > 3:
			self.user = parameters(2)
			self.pwd = parameters(3)
		self.pendingRequests = {}
		self.jsonrpcVersion = "2.0"

	def scanAudioLibrary(self):
		self.pendingRequests['AudioLibrary.Scan'] = self.buildRequest('AudioLibrary.Scan', {}, self.generateID())
		self.logger.info("add AudioLibrary.Scan action")
		#return self.sendRequest(request)

	def scanVideoLibrary(self):
		self.pendingRequests['VideoLibrary.Scan'] = self.buildRequest('VideoLibrary.Scan', {}, self.generateID())
		self.logger.info("add VideoLibrary.Scan action")
		#return self.sendRequest(request)

	def cleanAudioLibrary(self):
		self.pendingRequests['AudioLibrary.Clean'] = self.buildRequest('AudioLibrary.Clean', {}, self.generateID())
		self.logger.info("add AudioLibrary.Clean action")
		#return self.sendRequest(request)

	def cleanVideoLibrary(self):
		self.pendingRequests['VideoLibrary.Clean'] = self.buildRequest('VideoLibrary.Clean', {}, self.generateID())
		self.logger.info("add VideoLibrary.Clean action")
		#return self.sendRequest(request)

	def sendNotificationMessage(self, title, message, displayTime=None):#, image=None, displayTime=None):
		self.logger.info("send notification, title=%s message=%s", title, message)
		params = {"title": title, "message": message}
		if displayTime is not None:
			params["displaytime"] = displayTime
		id = self.generateID()
		request = self.buildRequest('GUI.ShowNotification', params, id)
		return self.sendRequest(request) is not None

	def sendRequest(self, request):
		#print request
		#print "host: ", self.host
		#print "port: ", self.port
		conn = httplib.HTTPConnection(self.host, self.port)
		conn.request("POST", "/jsonrpc", request, {"Content-type": "application/json"})
		return self.processResponse(conn.getresponse())

	def buildRequest(self, type, parameters, id=0):
		r = {"method": type, "params": parameters, "jsonrpc": self.jsonrpcVersion}
		if id != 0:
			r["id"] = id
		return json.JSONEncoder().encode(r)

	def generateID(self):
		id = 0
		while id == 0:
			id = random.randint(-9999999, 9999999)
		return id

	def processResponse(self, response):
		if response.getheader("content-length") is not None:
			page = response.read()
			#print page
			resp = json.JSONDecoder().decode(page)
			if resp["result"] == "OK":
				#print "Request Accepted."
				return resp
		#print "Error on request."
		return None

	def executePendingRequests(self):
		results = {}
		for k, v in self.pendingRequests.iteritems():
			r = self.sendRequest(v)
			if r is not None:
				self.logger.info("Request %s succeed", k)
			results[k] = r
