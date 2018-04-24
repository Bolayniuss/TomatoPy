# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import six
if six.PY3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse
import requests
import logging

from singleton import Singleton

logger = logging.getLogger(__name__)


class MultiHostError(Exception):
    def __init__(self, hostname):
        super(MultiHostError, self).__init__()
        self.host = hostname

    def __str__(self):
        return "Unable to open MultiHost %s" % self.host

    def __unicode__(self):
        return "Unable to open MultiHost %s" % self.host


class MultiHostHandlerException(Exception):
    def __init__(self, hostname):
        super(MultiHostHandlerException, self).__init__()
        self.host = hostname

    def __str__(self):
        return "Host %s not registered" % self.host

    def __unicode__(self):
        return "Host %s not registered" % self.host


@Singleton
class MultiHostHandler(object):
    def __init__(self):

        self.hosts = {}

    def open_url(self, url, timeout):
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            parsed_url.scheme = "http"
        hosts = self.hosts.get(parsed_url.hostname)
        if hosts:
            return hosts.open_path(parsed_url.path, parsed_url.scheme, timeout)
        else:
            logger.info("No MultiHost registered for url %s." % (url, ))
            return requests.get(url)

    def register_multi_host(self, hostname, extra_hosts):
        """
        :param basestring hostname:
        :param list extra_hosts:
        """
        if not self.hosts.get(hostname):
            self.hosts[hostname] = MultiHost(hostname, extra_hosts)


class Host(object):
    def __init__(self, host):

        self.host = host
        self._last_access_time = 0
        self.is_accessible = True

    def last_access_time(self):
        if self.is_accessible:
            return self._last_access_time
        return 999999

    def open_path(self, path, scheme="http", timeout=10):
        try:
            url = scheme + "://" + self.host + path

            resp = requests.get(url=url, timeout=(2, timeout - 2))

            if resp.status_code in (200, 201):
                data = resp.text
                return data
        except requests.exceptions.RequestException as e:
            logger.exception("error with %s: %s", self.host, e)
            # raise e
        self._last_access_time = 0
        self.is_accessible = False
        return None


class MultiHost(object):
    def __init__(self, original_host, extra_hosts=[]):

        self.original = original_host
        self.hosts = [Host(original_host)]
        for extra_host in extra_hosts:
            self.hosts.append(Host(extra_host))

    def open_path(self, path, scheme="http", timeout=10):
        do_sort = False
        for host in self.hosts:
            data = host.open_path(path, scheme, timeout)
            if data:
                logger.debug("%s used as host for %s", host.host, self.original)
                if do_sort:
                    self.hosts.sort(key=lambda h: h.last_access_time())
                return data
            else:
                logger.debug("%s unusable as host for %s", host.host, self.original)
                do_sort = True
        raise MultiHostError(self.original)
