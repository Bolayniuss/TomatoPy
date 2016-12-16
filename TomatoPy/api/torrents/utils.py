# -*- coding: utf-8 -*-
# TomatoPy
from __future__ import print_function, absolute_import, unicode_literals

import bencode
import hashlib
import urllib


def magnet_from_data(torrent_data):
    metadata = bencode.bdecode(torrent_data)

    hash_contents = bencode.bencode(metadata['info'])
    hex_digest = hashlib.sha1(hash_contents).hexdigest()

    params = [
        ("xt", hex_digest),
        ("dn", metadata['info']['name']),
    ]

    announces = metadata["announce"]
    if isinstance(announces, str):
        announces = [announces]

    for an in announces:
        params.append(("tr", an))

    encoded_params = []
    for k, v in params:
        v = urllib.quote_plus(bytes(v), safe=b":")
        if k == "xt":
            v = b'urn:btih:%s' % v
        encoded_params.append("%s=%s" % (k, v))

    magnet_uri = 'magnet:?%s' % "&".join(encoded_params)
    return magnet_uri


def magnet_from_torrent_file(torrent_file):
    with open(torrent_file, "rb") as f:
        return magnet_from_data(f.read())
