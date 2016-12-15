# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals
import mysql.connector

from singleton import Singleton


@Singleton
class DatabaseManager:
    def __init__(self):
        self.connector = None
        self.cursor = None

    def connect(self, database, user, password, host="127.0.0.1", port=3306):
        self.connector = mysql.connector.connect(user=user, password=password, database=database, host=host, port=port,
                                                 buffered=True)
        self.cursor = self.connector.cursor()

    def close(self):
        self.cursor.close()
        self.connector.close()

    def is_connected(self):
        return (self.connector is None) or (self.cursor is None)
