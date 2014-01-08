__author__ = 'bolay'
import os
import hashlib
import shutil
import grp
import pwd
import os
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
		self.fsGroup = None
		self.fsUser = None

	def set(self, fsUser=None, fsGroup=None):
		self.fsUser = fsUser
		self.fsGroup = fsGroup

	def move(self, source, destination):
		print "move: ", source, " to ", destination
		try:
			os.makedirs(os.path.dirname(destination), 0777)
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