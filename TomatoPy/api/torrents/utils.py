# -*- coding: utf-8 -*-
# TomatoPy
from __future__ import print_function, absolute_import, unicode_literals

import bencode
import hashlib
import base64
import urllib


def magnet_from_data(torrent_data):
    metadata = bencode.bdecode(torrent_data)

    hash_contents = bencode.bencode(metadata['info'])
    digest = hashlib.sha1(hash_contents).digest()
    hex_digest = hashlib.sha1(hash_contents).hexdigest()
    #b32hash = base64.b32encode(digest)

    print(hex_digest)
    import json
    print(json.dumps(metadata, indent=4, ensure_ascii=False))

    params = [
        ("xt", hex_digest),
        ("dn", metadata['info']['name']),
        #("xl", metadata['info']['length'])
    ]

    announces = metadata["announce"]
    if isinstance(announces, str):
        announces = [announces]

    for an in announces:
        params.append(("tr", an))

    print(params)

    encoded_params = []
    for k, v in params:
        v = urllib.quote_plus(bytes(v), safe=b":")
        if k == "xt":
            v = b'urn:btih:%s' % v
        encoded_params.append("%s=%s" % (k, v))

    #param_str = urllib.urlencode(params)
    magnet_uri = 'magnet:?%s' % "&".join(encoded_params)
    return magnet_uri


def magnet_from_torrent_file(torrent_file):
    with open(torrent_file, "rb") as f:
        return magnet_from_data(f.read())
