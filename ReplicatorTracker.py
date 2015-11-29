__author__ = 'bolay'

import os
import re
import logging
import base64

import Tools
from DatabaseManager import DatabaseManager
from TomatoPy.TransmissionWrapper import TransmissionTorrentRPC
from Singleton import Singleton


class TrackedTorrent:
    def __init__(self, hash_, name, magnet, torrent_file=None):
        """
        :type torrent : transmissionrpc.Torrent
        :param torrent:
        """
        self.name = name
        self.hash = hash_
        self.torrent_file_data = ''
        self.magnet = magnet
        if torrent_file is not None and os.path.exists(torrent_file):
            f = open(torrent_file, "rb")
            self.torrent_file_data = base64.b64encode(f.read())

    @staticmethod
    def from_sql_query(sqlQuery):
        if len(sqlQuery) >= 4:
            tt = TrackedTorrent(sqlQuery[0], sqlQuery[1], sqlQuery[3])
            tt.torrent_file_data = sqlQuery[2]
            return tt
        return None

    @staticmethod
    def from_torrent(torrent):
        return TrackedTorrent(torrent.hash, torrent.name, torrent.magnetLink, torrent.torrentFilePath)


class InterestingFile:
    def __init__(self, name, torrent_hash, torrent_file_name, hash=None,
                 timeout=2538000):  # default timeout set to 30 days
        self.name = name
        self.timeout = timeout
        self.torrent_hash = torrent_hash
        self.torrent_file_name = torrent_file_name
        self.hash = hash
        if (self.hash is None) or (len(self.hash)) == 0:
            self.hash = Tools.get_hash(self.name)

    def set_timeout(self, timeout=2538000):
        # default timeout set to 30 days
        sql = "UPDATE `TrackedTorrentFiles` SET `timeout`=UNIX_TIMESTAMP()+ %d WHERE `name`=%s;"
        DatabaseManager.Instance().cursor.execute(sql, (timeout, self.name,))
        DatabaseManager.Instance().connector.commit()

    def insert_or_update_in_db(self):
        # if not self.isInDB:
        sql = "INSERT INTO `TrackedTorrentFiles` (`hash`, `name`, `timeout`, `torrentHash`, `torrentFileName`) VALUES (%s, %s, UNIX_TIMESTAMP()+%s, %s, %s) ON DUPLICATE KEY UPDATE timeout=VALUES(timeout);"
        DatabaseManager.Instance().cursor.execute(sql, (self.hash,
                                                        self.name,
                                                        self.timeout,
                                                        self.torrent_hash,
                                                        self.torrent_file_name))
        DatabaseManager.Instance().connector.commit()

    @staticmethod
    def from_sql_query(sqlQuery):
        if len(sqlQuery) >= 5:
            f = InterestingFile(sqlQuery[1], sqlQuery[3], sqlQuery[4], sqlQuery[0], sqlQuery[2])
            # f.isInDB = True
            return f
        # print "Fail to initiate InterestingFile with query : ", sqlQuery
        return None


class DoneTorrentFilter:
    def __init__(self, torrent_manager):
        self.torrent_manager = torrent_manager
        self.filter = RFileFilter("avi|mkv|mp4|wmv")
        self.interesting_files = {}

    def grab_interesting_files(self):
        # Load old from DB
        sql = "SELECT * FROM `TrackedTorrentFiles`;"
        DatabaseManager.Instance().cursor.execute(sql)
        for res in DatabaseManager.Instance().cursor:
            iF = InterestingFile.from_sql_query(res)
            if iF is not None:
                self.interesting_files[iF.name] = iF

        # Get new from torrent manager
        torrents = self.torrent_manager.getTorrents()
        for torrent in torrents:
            if torrent.isFinished:
                torrentFiles = self.torrent_manager.getTorrentFiles(torrent.hash)
                # for each torrentFile in torrent
                for f in torrentFiles:
                    file = File(os.path.join(self.torrent_manager.downloadDirectory, f.name))
                    # if "file" is a valide file
                    if self.filter.test(file):
                        # if file exists
                        if os.path.exists(file.fullPath):
                            iF = InterestingFile(file.fullPath, torrent.hash, f.name)
                            iF.insert_or_update_in_db()  # update timeout in any case
                            if file.fullPath not in self.interesting_files:
                                self.interesting_files[file.fullPath] = iF
                            sql = "INSERT INTO `TrackedTorrents` (`hash`, `name`, `torrentFile`, `magnet`) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE `hash`=VALUES(hash);"
                            t = TrackedTorrent.from_torrent(torrent)
                            DatabaseManager.Instance().cursor.execute(sql, (t.hash,
                                                                            t.name,
                                                                            t.torrent_file_data,
                                                                            t.magnet))
                            DatabaseManager.Instance().connector.commit()

                        # for a, iF in self.interestingFiles.iteritems():
                        #	print iF.hash, iF.name
                        # print ""


class RFileFilter:
    def __init__(self, extensionPattern):
        self.extension = extensionPattern

    def test(self, file):
        """
        :type file : File
        :param file:
        :return:
        """
        if file.extension is None:
            return False
        if file.name[0] == ".":
            return False
        return re.search(self.extension, file.extension, re.IGNORECASE) is not None


@Singleton
class DestinationManager:
    def __init__(self):
        self.destinations = {}

    def add(self, destination):
        """
        :type destination : Destination
        :param destination: the destination to add
        :return:
        """
        if destination.name not in self.destinations:
            self.destinations[destination.name] = destination

    def get(self, name):
        return self.destinations[name]


class Destination:
    def __init__(self, path, name, filter):
        """
        Constructor

        :type path: str
        :type name: str
        :type filter: TomatoPy.Filters.FileFilter
        :param path: path of the destination directory
        :param name: name of the destination
        """
        self.path = path
        self.name = name
        self.files = {}
        self.validInterestingFiles = []
        self.filter = filter

        self.logger = logging.getLogger("Destination")

        DestinationManager.Instance().add(self)

    def getRelativePath(self, path):
        """
        :type path: str
        :param path: absolute path
        """
        return os.path.relpath(path, self.path)

    def map(self, clean=False):
        """
        Build the list of files in this destination

        :type clean: bool
        :param clean: do we clean the database before
        :return:
        """
        self.files = {}
        curs = DatabaseManager.Instance().cursor
        if clean:
            curs.execute("DELETE FROM DestinationsFilesList WHERE `destinationName`=%s;", (self.name,))
            DatabaseManager.Instance().connector.commit()
        for root, dir, files in os.walk(self.path):

            for file in files:
                path = os.path.join(root, file)
                relativePath = self.getRelativePath(path)
                if self.filter.test(File(path)):
                    fwh = None
                    if not clean:
                        sql = "SELECT * FROM DestinationsFilesList WHERE `path`=%s AND `destinationName`=%s LIMIT 1;"
                        curs.execute(sql, (relativePath, self.name))
                        res = curs.fetchone()
                        # curs.fetchall()
                        if res is not None:
                            # file already in DB, so use it
                            fwh = FileWithHash.from_sql_query(res)
                    if fwh is None:
                        fwh = FileWithHash(path, self.name, None, relativePath)
                        sql2 = "INSERT INTO DestinationsFilesList (`hash`, `path`, `destinationName`) VALUES(%s, %s, %s);"
                        # self.logger.info("%s add: %s", [self.name, relativePath]
                        curs.execute(sql2, (fwh.hash, relativePath, fwh.destination_name))
                        DatabaseManager.Instance().connector.commit()
                    self.files[fwh.hash] = fwh

    def look_for_interesting_files(self, ifList):
        """
        Build the list of all interesting
        :param ifList:
        :return:
        """
        self.validInterestingFiles = []
        for i, f in ifList.iteritems():
            if f.hash in self.files:
                self.logger.info("New interesting file : %s", f.name)
                self.validInterestingFiles.append((f, self.files[f.hash]))

    @staticmethod
    def from_sql_query(query):
        if len(query) >= 3:
            if not isinstance(query[1], unicode):
                query[1] = unicode(query[1])
            return Destination(query[1], query[0], RFileFilter(query[2]))
        return None


class File:
    def __init__(self, path):
        """

        :param path:
        """
        self.fullPath = path
        self.path = os.path.dirname(path)
        self.name = os.path.basename(path)
        self.simpleName = self.name
        self.extension = None
        # if os.path.isfile(self.fullPath):
        m = re.compile(r"(.*)\.([^.]*)").match(self.name)
        if m is not None:
            self.simpleName = m.group(1)
            self.extension = m.group(2)


class FileWithHash(File):
    """
    FileWithHash represent files present in destination directories

    """

    def __init__(self, path, destination_name, hash=None, relative_path=None):
        """

        :type destination_name : str
        :type hash : str
        :param hash: hash of the file, if None the hash is computed
        :param path: Path of the file
        :param destination_name: destination name
        """
        File.__init__(self, path)
        self.id = None
        self.hash = hash
        self.destination_name = destination_name
        if hash is None:
            self.hash = Tools.get_hash(self.fullPath)
        self.relativePath = path
        if relative_path is not None:
            self.relativePath = relative_path

    @staticmethod
    def from_sql_query(sql_query):
        if (sql_query is not None) and (len(sql_query) >= 3):
            f = FileWithHash(sql_query[3], sql_query[2], sql_query[1])
            f.id = sql_query[0]
            return f
        return None


class FileTracer:
    def __init__(self):

        self.logger = logging.getLogger("FileTracer ")

        # create useful objects
        self.dbm = DatabaseManager.Instance()
        self.torrent_manager = TransmissionTorrentRPC()

        # Load parameters
        # Load destinations
        self.destinations = []
        self.dbm.cursor.execute("SELECT * FROM `TrackedDestinations`;")
        for res in self.dbm.cursor:
            d = Destination.from_sql_query(res)
            if d is not None:
                self.destinations.append(d)

        # init DoneTorrentFilter
        self.dtf = DoneTorrentFilter(self.torrent_manager)

    def run(self):
        # get interesting files
        self.dtf.grab_interesting_files()

        if len(self.dtf.interesting_files) > 0:
            # Map all sources
            for d in self.destinations:
                d.map()
                d.look_for_interesting_files(self.dtf.interesting_files)
        self.dbm.connector.commit()
        # For each destinations
        for destination in self.destinations:
            # For each tuple (trackedFile, destinationFile) in interestingFiles
            for trackedFile, destinationFile in destination.validInterestingFiles:
                sql = "SELECT * FROM `TrackedTorrents` WHERE `hash`=%s LIMIT 1;"
                self.dbm.cursor.execute(sql, (trackedFile.torrentHash,))
                res = self.dbm.cursor.fetchone()
                # If torrent is in TrackedTorrents DB
                if res is not None:
                    tt = TrackedTorrent.from_sql_query(res)
                    if tt is not None:
                        sql = "SELECT count(1) FROM ReplicatorActions WHERE `torrentName`=%s AND `torrentFileName`=%s LIMIT 1;"
                        self.dbm.cursor.execute(sql, (tt.name, trackedFile.torrentFileName))
                        if not self.dbm.cursor.fetchone()[0]:
                            self.logger.info("New replicator action with file: %s", trackedFile.torrentFileName)
                            sql = "INSERT INTO `ReplicatorActions` (torrentName, torrentFileName, torrentData, destinationName, destinationRelativePath) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE torrentFileName=torrentFileName;"
                            self.dbm.cursor.execute(sql, (tt.name,
                                                          trackedFile.torrentFileName,
                                                          tt.magnet, destination.name,
                                                          destinationFile.relativePath))
                            self.dbm.connector.commit()
                        else:
                            self.logger.warn("This action already exists in the database.")
                        # Remove File from TrackedTorrentFiles DB
                        # self.logger.info("Remove TrackedTorrentFile %s", trackedFile.name)
                        # sql = "DELETE FROM `TrackedTorrentFiles` WHERE `hash`=%s;"
                        # self.dbm.cursor.execute(sql, (trackedFile.hash, ))
                        # self.dbm.connector.commit()
                    else:
                        self.logger.error("Unable to create TrackedTorrent with query %s", res)
                else:
                    self.logger.error("res is None for hash=%s", trackedFile.torrentHash)

    def clean(self):
        # self.dbm.cursor.execute("DELETE FROM TrackedTorrentFiles WHERE timeout<UNIX_TIMESTAMP()")
        self.logger.debug("Beginning Clean up.")
        torrents = {}
        for torrent in self.torrent_manager.getTorrents():
            torrents[torrent.hash] = 1

        delete_tt_sql = "DELETE FROM `TrackedTorrents` WHERE `hash`=%s;"
        get_ttf_with_torrent_hash_sql = "SELECT COUNT(1) FROM `TrackedTorrentFiles` WHERE `torrentHash`=%s LIMIT 1;"
        for iF in self.dtf.interesting_files.itervalues():
            # Clean up TrackedTorrentFiles DB
            delete = False
            # Remove if file does not exist (deleted, moved)
            if not os.path.exists(iF.name) and iF.torrentHash not in torrents:
                delete = True
            # Remove if associated torrent does not exists
            # if not (iF.torrentHash in torrents):
            #	delete = True
            if delete:
                self.logger.info("Remove TrackedTorrentFile %s", iF.name)
                self.dbm.cursor.execute("DELETE FROM `TrackedTorrentFiles` WHERE `name`=%s", (iF.name,))
                self.dbm.connector.commit()

            # Clean up TrackedTorrents DB
            sql = "SELECT `hash` FROM `TrackedTorrents`;"
            self.dbm.cursor.execute(sql)
            tracked_torrents = []
            for res in self.dbm.cursor:
                tracked_torrents.append(res[0])

            for hashStr in tracked_torrents:
                # No TrackedTorrentFile associated with this TrackedTorrent => remove
                self.dbm.cursor.execute(get_ttf_with_torrent_hash_sql, (hashStr,))
                if not self.dbm.cursor.fetchone()[0]:
                    self.logger.info("Remove TrackedTorrent with hash=%s", hashStr)
                    self.dbm.cursor.execute(delete_tt_sql, (hashStr,))
                    self.dbm.connector.commit()

        self.logger.debug("End Clean up.")
