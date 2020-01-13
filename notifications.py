# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import io
import json
import time
import urllib

import requests

from database import DatabaseManager
from singleton import Singleton


class Serializable(object):
    def to_dict(self):
        raise NotImplementedError()


class UnSerializable(object):
    @staticmethod
    def from_dict(data):
        raise NotImplementedError


class Expiration(Serializable, UnSerializable, object):
    def __init__(self, seconds=0, minutes=0, hours=0, days=0, weeks=0, add_now_ts=True):
        self.expiration = 0
        self.increment(seconds, minutes, hours, days, weeks)
        if add_now_ts:
            self.expiration += time.time()

    def increment(self, seconds=0, minutes=0, hours=0, days=0, weeks=0):
        self.expiration += (seconds + (60 * (minutes + 60 * (hours + 24 * (days + 7 * weeks)))))

    def is_expired(self):
        return time.time() >= self.expiration

    def to_dict(self):
        return {"expiration": self.expiration}

    @staticmethod
    def from_dict(data):
        """

        :param dict data:
        :rtype Expiration:
        """
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

    def to_dict(self):
        a = {"title": self.title}
        if self.expiration:
            a["expiration"] = self.expiration.to_dict()
        return a

    @staticmethod
    def from_dict(data):
        """

        :param dict data:
        :rtype Notification:
        """
        try:
            expiration = None
            try:
                expiration = Expiration.from_dict(data["expiration"])
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
        self.service_name = "NotificationServer"
        self.notifications = {}
        if DatabaseManager.Instance().cursor:
            sql = "SELECT * FROM RemoteServices WHERE `ServiceName`=%s LIMIT 1;"
            DatabaseManager.Instance().cursor.execute(sql, (self.service_name,))
            for res in DatabaseManager.Instance().cursor:
                data = res[2].split("&&")
                self.user = data[0]
                self.url = data[1]
                break
        else:

            self.user = "dev-default"
            self.url = "http://bandb.dnsd.info/cgi-bin/replicator"

    def add_notification(self, title, category='general', expiration=None):
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

    def get_notification(self, list_expired=False):
        if list_expired:
            return self.notifications
        return dict(map(lambda k, v: (k, filter(lambda x: x.expiration and not x.expiration.is_expired(), v)),
                        self.notifications.items()))

    def serialize(self):
        notifications = dict(
            map(lambda k, v: (k, map(lambda x: x.to_dict(), v)), self.get_notification(True).items()))
        return {"notifications": notifications}

    def un_serialize(self, data):
        notifications_by_cat = data["notifications"]
        self.notifications.clear()
        for (k, v) in notifications_by_cat.items():
            for n in v:
                try:
                    notification = Notification.from_dict(n)
                    if notification.expiration and not notification.expiration.is_expired():
                        if k not in self.notifications:
                            self.notifications[k] = []
                        self.notifications[k].append(notification)
                except KeyError:
                    pass
                except TypeError:
                    pass

    def get_from_remote_server(self):
        url = self.url + "?q=getNotifications&user=" + self.user

        resp = requests.get(url)

        if not resp.ok:
            print("oups, can't get data from `%s`: %s" % (url, resp.text))
            return
        try:
            self.un_serialize(resp.json())
        except ValueError:
            pass

    def save_to_remote_server(self):
        url = self.url

        data = {
            "q": "setNotifications",
            "user": self.user,
            "data": json.dumps(self.serialize())
        }

        resp = requests.post(url, data=data)

        if not resp.ok:
            print("oups, can't get data from `%s`: %s" % (url, resp.text))
            return

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

                self.un_serialize(obj)
        except IOError:
            pass
