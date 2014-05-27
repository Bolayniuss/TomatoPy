__author__ = 'bolay'

import hashlib
import shutil
import grp
import pwd
import os
import logging

from Singleton import Singleton


def getHash(filePath, blocSizeMax=1000000):
	"""

	Get the hash of a file using the nth last bytes. n=min(blockSizeMax, file.size/2). The hash is compute using sha256.
	:type filePath : unicode
	:param filePath: path of the file to hash
	:param blocSizeMax: number of bytes used to compute the hash
	:rtype : str
	"""
	#filePath = unicodedata.normalize('NFKC', unicode(filePath, "utf8"))
	size = os.path.getsize(filePath)
	f = open(filePath, 'rb')
	blocSize = min(blocSizeMax, size / 2)
	f.seek(-blocSize, 2)
	d2 = f.read()
	return hashlib.sha256(d2).hexdigest()


@Singleton
class FileSystemHelper:
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.fsGroup = None
		self.fsUser = None

	def set(self, fsUser=None, fsGroup=None):
		self.fsUser = fsUser
		self.fsGroup = fsGroup

	def move(self, source, destination):
		self.logger.debug("move: %s to %s", source, destination)
		try:
			directory = os.path.dirname(destination)
			self.superMakedirs(directory, 0777)
		except OSError:
			pass
		finally:
			pass
		shutil.move(source, destination)
		os.chmod(destination, 0777)
		try:
			if self.fsUser is not None and self.fsGroup is not None:
				os.chown(destination, pwd.getpwnam(self.fsUser).pw_uid, grp.getgrnam(self.fsGroup).gr_gid)
		except KeyError, e:
			pass
		finally:
			pass
		return True

	def superMakedirs(self, path, mode):
		if not path or os.path.exists(path):
			return []
		(head, tail) = os.path.split(path)
		res = self.superMakedirs(head, mode)
		os.mkdir(path)
		os.chmod(path, mode)
		if self.fsUser is not None and self.fsGroup is not None:
				os.chown(path, pwd.getpwnam(self.fsUser).pw_uid, grp.getgrnam(self.fsGroup).gr_gid)
		res += [path]
		return res