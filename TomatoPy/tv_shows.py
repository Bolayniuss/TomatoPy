# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import logging
import os
import re
import time

import rarfile

import tools
from TomatoPy.api.torrents import TorrentFile
from TomatoPy.automated_action import AutomatedActionsExecutor
from TomatoPy.scrappers import BetaserieRSSScrapper, TPBScrapper, T411Scrapper
from TomatoPy.scrappers.items import EpisodeItem
from TomatoPy.source_mapper import DirectoryMapper, TorrentFilter, FileFilter, FileItem
from database import DatabaseManager
from kodi_api import XbmcLibraryManager
from multi_host import MultiHostError
from notifications import NotificationManager, Expiration


DEFAULT_TORRENT_PROVIDER = "TPB"


class TrackedTvShow(object):
    def __init__(self, title, torrent_filter, search_string="", preferred_torrent_provider=None):
        self.title = title
        self.torrent_filter = torrent_filter
        self.search_string = search_string or title

        self.preferred_torrent_provider = preferred_torrent_provider

    def __str__(self):
        return "%s - %s|%s" % (self.title, self.search_string, self.preferred_torrent_provider)


class TrackedEpisode(EpisodeItem):
    def __init__(self, episode_item, tracked_tv_show):
        """

        :param episode_item:
        :param tracked_tv_show:
        :type episode_item: EpisodeItem
        :type tracked_tv_show: TrackedTvShow
        :return:
        """

        super(TrackedEpisode, self).__init__(title=episode_item.title,
                                             tv_show=episode_item.tv_show,
                                             season=episode_item.season,
                                             episode_number=episode_item.episode_number,
                                             torrent_item=episode_item.torrent_item)

        self.tracked_tv_show = tracked_tv_show

    def __str__(self):
        return "%s, %s" % (super(TrackedEpisode, self), self.tracked_tv_show)


class TvShowManager(AutomatedActionsExecutor):
    """
    Provide functions to:
        - grab new tv shows episodes from registered episode providers
        - grab magnet link from registered torrent providers
        - add new download tasks to torrent manager (utorrent, transmission)
        - move episode file to the right place when downloaded
        - notify each event to a notification service
        - update XBMC library if needed
    """

    def __init__(self, torrent_manager):
        super(TvShowManager, self).__init__("TvShowManager")

        self.logger = logging.getLogger("TvShowManager")

        dbm = DatabaseManager.Instance()
        self.torrent_manager = torrent_manager

        self.tracked_tv_shows = []  # tv shows that can be downloaded // Get them form db

        query = "SELECT parameters FROM Parameters WHERE name='TvShowManager' LIMIT 1"
        dbm.cursor.execute(query)
        (parametersString,) = dbm.cursor.fetchone()
        parameters = parametersString.split("&&")
        self.beta_user = parameters[1]
        self.tv_show_directory = u"" + parameters[0]
        self.file_system_encoding = None
        if len(parameters) > 2:
            self.file_system_encoding = parameters[2]

        query = "SELECT title, filter, authorFilter, sizeLimits, episodeProviderSearchString, preferredTorrentProvider FROM TrackedTvShows;"
        dbm.cursor.execute(query)

        for (title, name_filter, author_filter, size_limits, search_string, preferred_torrent_provider) in dbm.cursor:

            size_limits = str(size_limits)

            sizes = {}
            size_limits = size_limits.split(":")
            if len(size_limits[0]) > 0:
                sizes["gt"] = int(size_limits[0])
            if len(size_limits) > 1:
                if len(size_limits[1]) > 0:
                    sizes["lt"] = int(size_limits[1])
            filter_ = TorrentFilter(name_filter.split(":"), author_filter, sizes)
            self.tracked_tv_shows.append(TrackedTvShow(title, filter_, search_string, preferred_torrent_provider))
        dbm.connector.commit()

        # TODO: Change
        self.registered_episode_providers = [BetaserieRSSScrapper(self.beta_user)]
        self.registered_torrent_providers = {
            "TPB": TPBScrapper(),
            #"T411": T411Scrapper("bolay", "12081987")
        }

        self.directory_mapper = DirectoryMapper(self.tv_show_directory, r"(.*)\.(mkv|avi|mp4|wmv)$",
                                                self.file_system_encoding)

        self.load_actions()

    def get_tracked_tv_show(self, episode):
        """
        Returns the associate tracked tv show if it exists, otherwise return None
        :param episode: the episode to test
        :type episode: EpisodeItem
        :return: The associate tracked tv show if exists, otherwise return None
        :rtype: TrackedTvShow
        """
        if episode.tv_show:
            for tracked_tv_show in self.tracked_tv_shows:
                if episode.tv_show.lower() == tracked_tv_show.title.lower():
                    return tracked_tv_show
        return None

    def get_new_episodes(self):
        """
        Returns a list of episodes ready to download
        :return: a list of episodes ready to download
        :rtype: list of Episode
        """
        # TODO: move content of first "for loop" in EpisodeProvider.getNewEpisode(trackedTvShows). Keep verification on torrent manager
        # TODO: move deleteBadChars to Tools module
        episodes = []
        for episode_provider in self.registered_episode_providers:
            try:
                episode_provided = episode_provider.get_episodes()
                for episode in episode_provided:
                    added = False
                    for e in episodes:
                        if e.tv_show == episode.tv_show and e.season == episode.season and e.episode_number == episode.episode_number:
                            added = True
                            break
                    if not added:
                        # self.logger.debug("Episode : %s (%s)", episode.title, episode.tvShow)

                        tracked_tv_show = self.get_tracked_tv_show(episode)
                        if tracked_tv_show:
                            # self.logger.debug("is in tracked tv shows")

                            if not self.directory_mapper.file_exists(episode.title):
                                # self.logger.debug("%s ,is not in source directory", episode.title)

                                torrent_search_string = "%s S%02dE%02d" % (
                                    tracked_tv_show.search_string, episode.season, episode.episode_number)
                                pattern = tools.delete_bad_chars(torrent_search_string)
                                pattern = pattern.replace(" ", ".*")
                                if not self.torrent_manager.search_in_torrents(pattern):
                                    # self.logger.debug("%s doesn't exists in torrentManager.torrents", episode.title)

                                    episodes.append(TrackedEpisode(episode, tracked_tv_show))
                                    self.logger.info("%s flagged as new.", episode.title)
                                else:
                                    self.logger.debug("%s not added, already in the downloads list.", episode.title)
                            else:
                                self.logger.debug("%s not added, already in the downloaded list.", episode.title)
                        else:
                            self.logger.debug("%s not added, not a tracked TvShow.", episode.title)
                    else:
                        self.logger.debug("%s not added, already in the added list.", episode.title)
            except Exception:
                self.logger.exception("Error while getting new episodes")
        return episodes

    def add_new_to_torrent_manager(self, episodes=None):
        """
        :param episodes:
        :type episodes: list of TrackedEpisode
        :return:
        """
        if not episodes:
            episodes = self.get_new_episodes()
        self.logger.info("Episodes ready for download:")
        for episode in episodes:
            torrent_items = []
            if episode.torrent_provided:
                torrent_items.append(episode.torrent_item)
            else:
                provider_name = episode.tracked_tv_show.preferred_torrent_provider or DEFAULT_TORRENT_PROVIDER

                torrent_providers = [self.registered_torrent_providers[provider_name]] + [v for k, v in self.registered_torrent_providers.items()if k != provider_name]

                for torrentProvider in torrent_providers:
                    torrent_search_string = ("%s S%02dE%02d" % (
                        episode.tracked_tv_show.search_string, episode.season, episode.episode_number))
                    try:
                        torrent_items = torrentProvider.get_torrents(torrent_search_string, episode.tracked_tv_show.torrent_filter)
                    except MultiHostError as e:
                        self.logger.exception(e.message)
                    if torrent_items:
                        break

            if len(torrent_items) > 0:
                success = True
                torrent_data = torrent_items[0].content
                if torrent_data is not None:
                    new_torrent = self.torrent_manager.add_torrent(torrent_data)
                    if new_torrent:
                        self.add_automated_actions(new_torrent.hash, episode.tracked_tv_show.title, episode.title)
                        self.logger.info("New torrent added for episode %s", episode.title)
                        NotificationManager.Instance().add_notification(
                            episode.title,
                            "TvShowManager: New",
                            Expiration(weeks=4)
                        )
                    else:
                        success = False
                else:
                    success = False
                if not success:
                    self.logger.info("No torrent added for %s", episode.title)
                    NotificationManager.Instance().add_notification(
                        "Unable to add %s to TM" % episode.title,
                        "TvShowManager: Error",
                        Expiration()
                    )
            else:
                NotificationManager.Instance().add_notification(
                    "No torrent found for %s" % episode.title,
                    "TvShowManager: Error", Expiration()
                )
                self.logger.info("No torrent found for %s", episode.title)

    def add_automated_actions(self, torrent_id, tv_show, episode_name):
        self.logger.debug("addAutomatedActions | new (%s, %s, %s)", torrent_id, tv_show, episode_name)
        data = "&&".join(["move", torrent_id, tv_show, episode_name])
        query = "INSERT INTO `AutomatedActions` (`notifier`, `trigger`, `data`) VALUES ('TvShowManager', 'onTorrentDownloaded', %s);"
        self.logger.info("add automated action, quest=%s, data=%s", query, data)
        DatabaseManager.Instance().cursor.execute(query, (data, ))
        DatabaseManager.Instance().connector.commit()

    def get_episode_final_path(self, file_, tv_show, episode_name):
        """
        :param file_: file to move
        :type file_ : FileItem
        :param tv_show: tv show name
        :type tv_show: unicode
        :param episode_name: episode name (e.g. {tvShow} S01E01)
        :type episode_name: unicode
        :return: The final destination path for this episode
        :rtype: unicode
        """

        season = self.get_season_from_title(episode_name)
        dst = os.path.join(
            self.tv_show_directory,
            tv_show,
            "Saison %d" % season,
            "%s.%s" % (episode_name, file_.extension)
        )
        return dst

    def get_tv_show_file_from_torrent(self, torrent, filter_):
        """
        :param torrent:
        :type torrent: TorrentObject
        :param filter_:
        :type filter_: FileFilter
        :rtype FileItem:
        """
        files = self.torrent_manager.get_torrent_files(torrent.hash)
        rar_filter = FileFilter(".*", ["rar"])
        valid_files = []
        for file_ in files:
            file_item = FileItem.from_filename(file_.name, "")
            if filter_.test(file_item):
                valid_files.append(file_)
            elif rar_filter.test(file_item):
                extracted_file = self.extract_from_rar(
                    filter_,
                    self.torrent_manager.get_torrent_file_path(torrent.name, file_.name)
                )
                if extracted_file is not None:
                    valid_files.append(extracted_file)

        if len(valid_files) == 0:
            # TODO: Make filter parameter "extensions" not hardcoded
            media_filter = FileFilter(".*", ["mkv", "mp4", "avi"])
            for file_ in files:
                if media_filter.test(FileItem.from_filename(file_.name, "")):
                    valid_files.append(file_)
        if len(valid_files) == 0:
            self.logger.info("No valid files found")
            return None
        id_ = 0
        i = 1
        while i < len(valid_files):
            if valid_files[i].size > valid_files[id_].size:
                id_ = i
            i += 1
        self.logger.debug("validFile id_=%d, name=%s", id_, valid_files[id_].name)
        try:
            complete_path = self.torrent_manager.get_torrent_file_path(torrent.name, valid_files[id_].name)
        except IOError as e:
            raise
        file_ = FileItem.from_complete_path(complete_path)
        return file_

    def execute_action(self, action_data):
        """
        Execute generic action

        :param list action_data: list
        :return: success
        :rtype bool:
        """
        data = action_data

        hash_string = data[1]
        tv_show = data[2]
        episode_name = data[3]
        try:
            torrent = self.torrent_manager.get_torrent(hash_string)
            if torrent.is_finished:
                pattern = tools.delete_bad_chars(episode_name)
                pattern = pattern.replace(" ", ".")
                filter_ = FileFilter(pattern, ["mkv", "avi", "mp4"])
                if data[0] == "move":
                    self.logger.info("move action")
                    try:
                        file_to_move = self.get_tv_show_file_from_torrent(torrent, filter_)
                        if file_to_move:
                            success = False
                            destination_path = self.get_episode_final_path(file_to_move, tv_show, episode_name)
                            source_file_path = file_to_move.get_full_path()
                            self.logger.info("try to move %s* to %s", source_file_path, destination_path)
                            if len(source_file_path) > 0:
                                success = tools.FileSystemHelper.Instance().move(source_file_path, destination_path)
                            if success:
                                self.logger.info("move succeed")
                                time.sleep(0.5)
                                XbmcLibraryManager.Instance().scan_video_library(
                                    tools.PathSubstitution.Instance().substitute(os.path.dirname(os.path.dirname(destination_path)))
                                )
                                self.logger.info("delete associated torrent")
                                self.torrent_manager.remove_torrent(hash_string, True)
                                NotificationManager.Instance().add_notification(
                                    torrent.name,
                                    "TvShowManager: Done", Expiration(weeks=4)
                                )
                                return True
                            # else
                            self.logger.warn("Failed to move %s", torrent.name)
                            NotificationManager.Instance().add_notification(
                                "Move failure in %s" % torrent.name,
                                "TvShowManager: Errors", Expiration()
                            )
                        else:
                            self.logger.warn("No valid file found in %s", torrent.name)
                            NotificationManager.Instance().add_notification(
                                "No valid file found in %s" % torrent.name,
                                "TvShowManager: Errors", Expiration()
                            )
                        return False
                    except IOError:
                        self.logger.error("error while moving file, file does not exists.")
                        NotificationManager.Instance().add_notification(
                            "File doesn't exists %s" % torrent.name,
                            "TvShowManager: Errors", Expiration()
                        )
            else:
                self.logger.info("Torrent %s isn't yet finished", torrent.name)
                prc = 0 if not torrent.size else float(torrent.downloaded) / torrent.size
                NotificationManager.Instance().add_notification(
                    "%s %s" % ('{0:.0%}'.format(prc), torrent.name),
                    "TvShowManager: Downloading", Expiration()
                )
                return False
        except:
            self.logger.exception("Error while executing action %s", action_data)
        finally:
            pass
        return False

    def execute_on_torrent_downloaded_actions(self):
        """
        Execute onTorrentDownloaded action
        """
        curs = DatabaseManager.Instance().cursor
        # "SELECT id, data FROM AutomatedActions WHERE `trigger`='onTorrentDownloaded' AND notifier='TvShowManager';"
        actions = self.actions["onTorrentDownloaded"]
        for a in curs:
            actions.append(a)
        for id_, data in actions.items():
            try:
                self.logger.info("try to execute action id=%d", id_)
                success = self.execute_action(data)
                self.logger.info("action (id=%d) result=%d", id_, success)
                delete = success
            except KeyError:
                self.logger.info("error while processing action (id=%d) torrent does not exist", id_)
                delete = True
            finally:
                pass

            if delete:
                self.logger.info("remove action with id=%d", id_)
                delete_query = "DELETE FROM AutomatedActions WHERE id=%s;"
                curs.execute(delete_query, (id_, ))
                DatabaseManager.Instance().connector.commit()

    def extract_from_rar(self, filter_, file_):
        """
        Extract valid files from RAR file
        :param filter_: valid file filter
        :type filter_: FileFilter
        :param file_: rar file path
        :type file_: unicode
        """
        possible_files = []
        rar = rarfile.RarFile(file_)
        for f in rar.infolist():
            if filter_.test(FileItem.from_filename(f.filename, "")):
                possible_files.append(f)
        if len(possible_files) != 0:
            the_file = possible_files[0]
            for f in possible_files:
                if f.file_size > the_file.file_size:
                    the_file = f
            rar.extract(the_file, os.path.split(file_)[0])
            self.logger.info("extract file, %s --- %s from rar, %s", os.path.split(file_)[0], the_file.filename, file_)
            fake_torrent_file = TorrentFile()
            fake_torrent_file.name = the_file.filename
            fake_torrent_file.size = the_file.file_size
            return fake_torrent_file
        return None

    @staticmethod
    def get_season_from_title(title):
        """
        Static method to get tv show season number from file name (title)
        :param title:
        :type title: unicode
        :rtype: int or None
        """
        res = re.match(r".*S0?(\d+)E.*", title, re.IGNORECASE)
        if res is not None:
            return int(res.group(1))
        return None
