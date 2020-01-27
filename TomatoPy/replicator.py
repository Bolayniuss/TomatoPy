# -*- coding: utf8 -*-
#
from __future__ import absolute_import, unicode_literals, print_function

import logging
import os

import requests

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

import tools
from database import DatabaseManager
from notifications import Expiration, NotificationManager
from TomatoPy.automated_action import AutomatedActionsExecutor
from kodi_api import XbmcLibraryManager


class ReplicatorManager(AutomatedActionsExecutor):
    def __init__(self, user, torrent_manager):
        """
        :type user: str
        :type torrent_manager: TomatoPy.api.torrents.TorrentManager
        :param user:
        :param torrent_manager:
        :return:
        """
        super(ReplicatorManager, self).__init__("ReplicatorManager")

        self.logger = logging.getLogger("ReplicatorManager")

        self.user = user
        self.serviceName = "Replicator"
        self.dbm = DatabaseManager.Instance()
        self.torrent_manager = torrent_manager
        self.replicator_actions = {}
        self.replicator_servers = []

        sql = "SELECT * FROM RemoteServices WHERE `ServiceName`=%s;"
        self.dbm.cursor.execute(sql, (self.serviceName,))
        for res in self.dbm.cursor:
            self.replicator_servers.append(dict(name=str(res[1]), url=str(res[2])))

        # Load destinations from DB
        self.destinations = {}
        sql = "SELECT * FROM TrackedDestinations;"
        self.dbm.cursor.execute(sql)
        for res in self.dbm.cursor:
            self.destinations[str(res[0])] = str(res[1])

        self.load_remote_actions()
        self.process_replicator_actions()
        self.load_actions()

    def load_remote_actions(self):
        for server in self.replicator_servers:
            self.logger.info("Loading actions from remote server, %s", server["name"])
            url = server["url"] + "?q=getReplicatorActions&user=" + self.user

            resp = requests.get(url)

            data = resp.json()
            if server["name"] not in self.replicator_actions:
                self.replicator_actions[server["name"]] = []
            self.replicator_actions[server["name"]].append(data)

    def process_replicator_actions(self):
        for server_name, server_actions_list in self.replicator_actions.items():
            for actions_dict in server_actions_list:
                for torrentName, actions in actions_dict.items():
                    action_params = []
                    for action in actions:

                        # Test if source exist
                        if action["destinationName"] in self.destinations:
                            destination_path = os.path.join(
                                self.destinations[action["destinationName"]],
                                action["destinationRelativePath"]
                            )
                            if not os.path.exists(destination_path):
                                action_params.append(action["torrentFileName"])
                                action_params.append(destination_path)

                    if action_params:
                        # Add Torrent
                        t = self.torrent_manager.add_torrent_url(action["torrentData"])

                        # Add move action with torrentHash, fileName, destination_path
                        aa = "move&&" + t.hash + "&&" + "&&".join(action_params)
                        sql = "INSERT INTO AutomatedActions (notifier, `trigger`, `data`) VALUES(%s, %s, %s);"
                        self.dbm.cursor.execute(sql, (self.actionNotifierName, "onTorrentDownloaded", aa))
                        self.dbm.connector.commit()

                        self.logger.info("Add new automated action from server=%s, %s", server_name, aa)

    def execute_action(self, data):
        if data[0] == "move":
            hash_string = data[1]
            try:
                torrent = self.torrent_manager.get_torrent(hash_string)
                if torrent.is_finished:
                    n_files = int((len(data) - 2) / 2)
                    success = True
                    destination_path = None
                    for i in range(n_files):
                        filename = data[2 + i * 2]
                        destination_path = data[3 + i * 2]
                        file_to_move = self.torrent_manager.get_torrent_file_path(torrent.name, filename)

                        if tools.FileSystemHelper.Instance().move(file_to_move, destination_path):
                            self.logger.info("file (%d/%d) move succeeded.", (i + 1), n_files)
                        # time.sleep(0.5)
                        else:
                            success = False
                    if success:
                        if destination_path is not None:
                            # XbmcLibraryManager.Instance().scan_video_library(
                            #    tools.PathSubstitution.Instance().substitute(os.path.dirname(destination_path))
                            # )
                            XbmcLibraryManager.Instance().scan_video_library()
                        self.logger.info("delete associated torrent")
                        self.torrent_manager.remove_torrent(hash_string, True)
                        NotificationManager.Instance().add_notification(
                            torrent.name,
                            "Replicator: Done",
                            Expiration(weeks=4)
                        )
                    else:
                        self.logger.error("failed to move %s", torrent.name)
                        NotificationManager.Instance().add_notification(
                            "Move error on %s" % torrent.name,
                            "Replicator: Errors", Expiration(weeks=4)
                        )
                    return success
                else:
                    self.logger.info("%s isn't yet finished", torrent.name)
                    prc = 0
                    try:
                        prc = float(torrent.downloaded) / torrent.size
                    except ZeroDivisionError:
                        pass
                    NotificationManager.Instance().add_notification(
                        "%s %s" % ('{0:.0%}'.format(prc), torrent.name),
                        "Replicator: Downloading", Expiration()
                    )
                    return False
            except Exception as e:
                self.logger.exception("Can't execute action with data: %s" % (data, ))
        return False

    def execute_on_torrent_downloaded_actions(self):
        curs = DatabaseManager.Instance().cursor
        actions = self.actions["onTorrentDownloaded"]
        for id_, data in actions.items():
            id_ = int(id_)
            try:
                self.logger.info("try to execute action id=%d", id_)
                success = self.execute_action(data)
                self.logger.info("action (id=%s) result=%s" % (id_, success))
                delete = success
            except KeyError as e:
                self.logger.exception("error while processing action (id=%d) torrent does not exist" % (id_, ))
                delete = True
            finally:
                pass

            if delete:
                self.logger.info("remove action with id=%s", id_)
                del_query = "DELETE FROM AutomatedActions WHERE id=%s;"
                curs.execute(del_query, (id_,))
                DatabaseManager.Instance().connector.commit()
