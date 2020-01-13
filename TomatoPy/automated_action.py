# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function
from database import DatabaseManager


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
            joined = self.type + delimiter + joined
        return joined

    @staticmethod
    def from_string(str_):
        data = str_.split("&&")
        if len(data[0]) > 0:
            type_ = data.pop(0)
            return AutomatedAction(type_, data)
        return None


class AutomatedActionsExecutor(object):
    def __init__(self, action_notifier_name):
        self.actionNotifierName = action_notifier_name
        self.actions = {"onBegin": {}, "onTorrentDownloaded": {}, "onEnd": {}}
        self.actionsLoaded = False

    def load_actions(self, reload_=False):
        if not self.actionsLoaded or reload_:
            curs = DatabaseManager.Instance().cursor
            query = "SELECT id, `trigger`, data FROM AutomatedActions WHERE notifier=%s;"
            curs.execute(query, (self.actionNotifierName,))
            for action in curs:
                data = str(action[2]).split("&&")
                self.actions[str(action[1])][str(action[0])] = data
            self.actionsLoaded = True
