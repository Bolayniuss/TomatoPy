# -*- coding: utf8 -*-
#
__author__ = 'bolay'

import httplib
import json
import random
import logging

from singleton import Singleton
from database import DatabaseManager


@Singleton
class XbmcLibraryManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        dbm = DatabaseManager.Instance()
        query = "SELECT parameters FROM Parameters WHERE name='XbmcLibraryManager' LIMIT 1"
        dbm.cursor.execute(query)
        (parametersString,) = dbm.cursor.fetchone()
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

    def scan_audio_library(self, directory=None):
        params = {}
        if directory:
            params["directory"] = directory
        self.pendingRequests['AudioLibrary.Scan'] = self.build_request('AudioLibrary.Scan', params, self.generate_id())
        if directory:
            self.logger.info("add AudioLibrary.Scan action, directory %s", directory)
        else:
            self.logger.info("add AudioLibrary.Scan action")
        # return self.sendRequest(request)

    def scan_video_library(self, directory=None):
        params = {}
        if directory:
            params["directory"] = directory
        self.pendingRequests[('VideoLibrary.Scan', directory)] = self.build_request('VideoLibrary.Scan', params, self.generate_id())
        if directory:
            self.logger.info("add VideoLibrary.Scan action, directory %s", directory)
        else:
            self.logger.info("add VideoLibrary.Scan action")
        # return self.sendRequest(request)

    def clean_audio_library(self):
        self.pendingRequests['AudioLibrary.Clean'] = self.build_request('AudioLibrary.Clean', {}, self.generate_id())
        self.logger.info("add AudioLibrary.Clean action")

    # return self.sendRequest(request)

    def clean_video_library(self):
        self.pendingRequests['VideoLibrary.Clean'] = self.build_request('VideoLibrary.Clean', {}, self.generate_id())
        self.logger.info("add VideoLibrary.Clean action")

    # return self.sendRequest(request)

    def send_notification_message(self, title, message, displayTime=None):  # , image=None, displayTime=None):
        self.logger.info("send notification, title=%s message=%s", title, message)
        params = {"title": title, "message": message}
        if displayTime is not None:
            params["displaytime"] = displayTime
        id = self.generate_id()
        request = self.build_request('GUI.ShowNotification', params, id)
        return self.send_request(request) is not None

    def send_request(self, request):
        # print request
        # print "host: ", self.host
        # print "port: ", self.port
        conn = httplib.HTTPConnection(self.host, self.port)
        conn.request("POST", "/jsonrpc", request, {"Content-type": "application/json"})
        self.logger.debug("Send request: %s", request)
        return self.process_response(conn.getresponse())

    def build_request(self, type, parameters, id=0):
        r = {"method": type, "params": parameters, "jsonrpc": self.jsonrpcVersion}
        if id != 0:
            r["id"] = id
        return json.JSONEncoder().encode(r)

    def generate_id(self):
        id = 0
        while id == 0:
            id = random.randint(-9999999, 9999999)
        return id

    def process_response(self, response):
        if response.getheader("content-length") is not None:
            page = response.read()
            # print page
            self.logger.debug("Receive: %s", page)
            resp = json.JSONDecoder().decode(page)
            if resp["result"] == "OK":
                # print "Request Accepted."
                return resp
        # print "Error on request."
        return None

    def execute_pending_requests(self):
        results = {}
        for k, v in self.pendingRequests.items():
            r = self.send_request(v)
            if r is not None:
                self.logger.debug("Request %s succeed", k)
            results[k] = r
