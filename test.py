import XbmcLibraryManager

__author__ = 'bolay'

from TomatoPy.TorrentRPC import *
from TomatoPy.TvShowManager import *
from DatabaseManager import DatabaseManager
from XbmcLibraryManager import XbmcLibraryManager

if __name__ == "__main__":
	DatabaseManager.Instance().connect("replicator", "root", None, "127.0.0.1")
	torrentMng = TransmissionTorrentRPC()
	tvShowMng = TvShowManager(torrentMng)
	print "Look for new downloads"
	tvShowMng.addNewToTorrentManager(torrentMng)
	print "Look for finished downloads"
	tvShowMng.executeOnTorrentDownloadedActions()
	print "Execute XBMC Library Manager pending requests"
	XbmcLibraryManager.Instance().executePendingRequests()
	print "End of script"



