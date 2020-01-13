from __future__ import absolute_import, print_function, unicode_literals
import TomatoPy.api.torrents.utorrent

torrentManager = TomatoPy.api.torrents.utorrent.UTorrentRPC("nhs.dyndns.info", 9090, "admin", "12081987", "/")

torrents = torrentManager.get_torrents()
for t in torrents:
    print(t.name, "is finished=", t.is_finished)
t = torrentManager.add_torrent_url("magnet:?xt=urn:btih:ce9fbdaa734cfbc160e8ef9d29072646c09958dd&dn=The.Wolf.of.Wall.Street.2013.DVDSCR.XviD-BiDA&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337")
print(t.name)
print(t.hash)
