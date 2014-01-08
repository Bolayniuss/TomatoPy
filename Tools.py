__author__ = 'bolay'
import os
import hashlib


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
