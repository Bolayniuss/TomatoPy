# -*- coding: utf-8 -*-
# 
__author__ = 'Michael Bolay'

from urlparse import urlparse
import time
import urllib2
import logging

from Singleton import Singleton

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
        return "Host %s not registered %s" % self.host

    def __unicode__(self):
        return "Host %s not registered %s" % self.host


@Singleton
class MultiHostHandler(object):
    def __init__(self):

        self.hosts = {}

    def openURL(self, url, timeout):
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            parsed_url.scheme = "http"
        hosts = self.hosts.get(parsed_url.hostname)
        if hosts:
            return hosts.open_path(parsed_url.path, parsed_url.scheme, timeout)
        else:
            raise MultiHostHandlerException(parsed_url.hostname)

    def registerMultiHost(self, hostname, extraHosts):
        if not self.hosts.get(hostname):
            self.hosts[hostname] = MultiHost(hostname, extraHosts)


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

            from StringIO import StringIO
            import gzip

            request = urllib2.Request(url)
            request.add_header('Accept-encoding', 'gzip')
            request.add_header('User-Agent',
                               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:33.0) Gecko/20100101 Firefox/33.0')
            t0 = time.time()
            response = urllib2.urlopen(url=request, timeout=timeout)
            t1 = time.time()

            self._last_access_time = t1 - t0
            self.is_accessible = True

            if response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                data = f.read()
            else:
                data = response.read()
            return data
        except urllib2.HTTPError, e:
            pass
        # raise e
        except urllib2.URLError, e:
            pass
        # raise e
        self._last_access_time = 0
        self.is_accessible = False
        return None


class MultiHost(object):
    def __init__(self, original_host, extra_hosts=[]):

        self.original = original_host
        self.hosts = [Host(original_host)]
        for extraHost in extra_hosts:
            self.hosts.append(Host(extraHost))

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
                do_sort = True
        raise MultiHostError(self.original)
