# -*- coding: utf-8 -*-
# 
__author__ = 'Michael Bolay'

from urlparse import urlparse
import time
import urllib2
import logging

from Singleton import Singleton


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
		self.logger = logging.getLogger(__name__)

		self.hosts = {}

	def openURL(self, url, timeout):
		parsedUrl = urlparse(url)
		if not parsedUrl.scheme:
			parsedUrl.scheme = "http"
		hosts = self.hosts.get(parsedUrl.hostname)
		if hosts:
			return hosts.openPath(parsedUrl.path, parsedUrl.scheme, timeout)
		else:
			raise MultiHostHandlerException(parsedUrl.hostname)

	def registerMultiHost(self, hostname, extraHosts):
		if not self.hosts.get(hostname):
			self.hosts[hostname] = MultiHost(hostname, extraHosts)


class Host(object):

	def __init__(self, host):
		self.logger = logging.getLogger(__name__)

		self.host = host
		self.lastAccessTime = 0
		self.isAccessible = True

	def lastAccessTime(self):
		if self.isAccessible:
			return self.lastAccessTime
		return 999999

	def openPath(self, path, scheme="http", timeout=10):
		try:
			url = scheme + "://" + self.host + path

			from StringIO import StringIO
			import gzip

			self.logger.debug(url)

			request = urllib2.Request("Opening url: %s", url)
			request.add_header('Accept-encoding', 'gzip')
			request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:33.0) Gecko/20100101 Firefox/33.0')
			t0 = time.time()
			response = urllib2.urlopen(url=request, timeout=timeout)
			t1 = time.time()

			self.lastAccessTime = t1 - t0
			self.isAccessible = True

			if response.info().get('Content-Encoding') == 'gzip':
				buf = StringIO(response.read())
				f = gzip.GzipFile(fileobj=buf)
				data = f.read()
			else:
				data = response.read()
			#print data
			return data
		except urllib2.HTTPError:
			pass
		except urllib2.URLError:
			pass
		self.lastAccessTime = 0
		self.isAccessible = False
		return None


class MultiHost(object):

	def __init__(self, originalHost, extraHosts=[]):
		self.logger = logging.getLogger(__name__)

		self.original = originalHost
		self.hosts = [Host(originalHost)]
		for extraHost in extraHosts:
			self.hosts.append(Host(extraHost))

	def openPath(self, path, scheme="http", timeout=10):
		doSort = False
		for host in self.hosts:
			data = host.openPath(path, scheme, timeout)
			if data:
				self.logger.debug("%s used as host for %s", host.host, self.original)
				if doSort:
					self.hosts.sort(key=lambda h: h.lastAccessTime)
				return data
				break
			else:
				doSort = True
		raise MultiHostError(self.original)