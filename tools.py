__author__ = 'bolay'

import hashlib
import shutil
import grp
import pwd
import os
import logging
import re

from singleton import Singleton


def get_hash(file_path, bloc_size_max=1000000):
    """

    Get the hash of a file using the nth last bytes. n=min(blockSizeMax, file.size/2). The hash is compute using sha256.
    :type file_path : unicode
    :param file_path: path of the file to hash
    :param bloc_size_max: number of bytes used to compute the hash
    :rtype : str
    """
    # filePath = unicodedata.normalize('NFKC', unicode(filePath, "utf8"))
    size = os.path.getsize(file_path)
    f = open(file_path, 'rb')
    bloc_size = min(bloc_size_max, size / 2)
    f.seek(-bloc_size, 2)
    d2 = f.read()
    return hashlib.sha256(d2).hexdigest()


@Singleton
class FileSystemHelper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fs_group = None
        self.fs_user = None

    def set(self, fs_user=None, fs_group=None):
        self.fs_user = fs_user
        self.fs_group = fs_group

    def move(self, source, destination):
        self.logger.info("move: %s to %s", source, destination)
        try:
            directory = os.path.dirname(destination)
            self.super_makedirs(directory, 0777)
        except OSError:
            pass
        finally:
            pass
        shutil.move(source, destination)
        os.chmod(destination, 0777)
        try:
            if self.fs_user is not None and self.fs_group is not None:
                os.chown(destination, pwd.getpwnam(self.fs_user).pw_uid, grp.getgrnam(self.fs_group).gr_gid)
        except KeyError as e:
            pass
        finally:
            pass
        return True

    def super_makedirs(self, path, mode):
        if not path or os.path.exists(path):
            return []
        (head, tail) = os.path.split(path)
        res = self.super_makedirs(head, mode)
        os.mkdir(path)
        os.chmod(path, mode)
        if self.fs_user is not None and self.fs_group is not None:
            os.chown(path, pwd.getpwnam(self.fs_user).pw_uid, grp.getgrnam(self.fs_group).gr_gid)
        res += [path]
        return res


@Singleton
class PathSubstitution:
    def __init__(self, substitution_peers_array=None):
        """

        :param list of list substitution_peers_array:
        :return:
        """
        self.substitutions = []
        if substitution_peers_array:
            for peer in substitution_peers_array:
                if len(peer) == 2:
                    self.substitutions.append((peer[0], peer[1],))

    def add_substitution(self, lookup_regexp, substitution):
        self.substitutions.append((lookup_regexp, substitution,))

    def substitute(self, source):
        s = source
        for peer in self.substitutions:
            source = re.sub(peer[0], peer[1], source)
        logging.debug("Substitute %s to %s", s, source)
        return source


def delete_bad_chars(inp):
    """
    Remove bad characters from inp. Useful when we want to use inp as a regex pattern.
    :param unicode inp:
    :return:
    :rtype unicode:
    """
    bad_chars = '(){}<>[]*'
    bad_chars_dict = dict((ord(char), None) for char in bad_chars)
    pattern = inp.translate(bad_chars_dict)
    return pattern
