# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

try:
    from httplib import HTTPConnection
except ImportError:
    from http.client import HTTPConnection

import requests

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
        parameters = str(parametersString).split("&&")

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
            if not directory.endswith("/"):
                directory += "/"
            params["directory"] = directory
        self.pendingRequests['AudioLibrary.Scan'] = self.build_request_data('AudioLibrary.Scan', params, self.generate_id())
        if directory:
            self.logger.info("add AudioLibrary.Scan action, directory %s", directory)
        else:
            self.logger.info("add AudioLibrary.Scan action")

    def scan_video_library(self, directory=None):
        params = {}
        if directory:
            if not directory.endswith("/"):
                directory += "/"
            params["directory"] = directory
        self.pendingRequests[('VideoLibrary.Scan', directory)] = self.build_request_data('VideoLibrary.Scan', params, self.generate_id())
        if directory:
            self.logger.info("add VideoLibrary.Scan action, directory %s", directory)
        else:
            self.logger.info("add VideoLibrary.Scan action")

    def clean_audio_library(self):
        self.pendingRequests['AudioLibrary.Clean'] = self.build_request_data('AudioLibrary.Clean', {}, self.generate_id())
        self.logger.info("add AudioLibrary.Clean action")

    def clean_video_library(self):
        self.pendingRequests['VideoLibrary.Clean'] = self.build_request_data('VideoLibrary.Clean', {}, self.generate_id())
        self.logger.info("add VideoLibrary.Clean action")

    def send_notification_message(self, title, message, displayTime=None):  # , image=None, displayTime=None):
        self.logger.info("send notification, title=%s message=%s", title, message)
        params = {"title": title, "message": message}
        if displayTime is not None:
            params["displaytime"] = displayTime
        id = self.generate_id()
        request = self.build_request_data('GUI.ShowNotification', params, id)
        return self.send_request(request) is not None

    def send_request(self, request_data):
        url = "http://%s:%s/jsonrpc" % (self.host, self.port)
        resp = requests.post(url, json=request_data)

        if resp.ok:
            data = resp.json()
            if data.get("result") == "OK":
                return resp.json()
        return None

    def build_request_data(self, type, parameters, id=0):
        r = {"method": type, "params": parameters, "jsonrpc": self.jsonrpcVersion}
        if id != 0:
            r["id"] = id
        return r

    def generate_id(self):
        id = 0
        while id == 0:
            id = random.randint(-9999999, 9999999)
        return id

    def execute_pending_requests(self):
        results = {}
        for k in list(self.pendingRequests.keys()):
            v = self.pendingRequests.pop(k)
            r = self.send_request(v)
            if r is not None:
                self.logger.debug("Request %s succeed", k)
            results[k] = r
