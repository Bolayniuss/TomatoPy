__author__ = 'bolay'

from TomatoPy.Scrapper import *
from TomatoPy.SourceMapper import *

from TomatoPy.TorrentRPC import *

if __name__ == "__main__":
	#TPBScrapper("the mentalist")
	#for item in BetaserieRSSScrapper("bolayniuss").items:
	#	print item.title
	#	TPBScrapper(item.title)
	for file in DirectoryMapper("/Users/bolay/Desktop", FileFilter(".*", ["jpg", "pdf"])).files:
		print file.name

	tc = TransmissionTorrentRPC("192.168.0.11", 8181, "admin", "admin")
	for l in tc.getTorrents():
		print l.hashString, l.name

	for l in tc.getTorrentFiles("e8e09e4e45ad9f56af3a4c8ed0c3e941e9d47712"):
		print l.name


