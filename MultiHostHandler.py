# -*- coding: utf-8 -*-
# 
__author__ = 'Michael Bolay'

from urlparse import urlparse
import time
import urllib2
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
		self.hosts = {}

	def openURL(self, url, timeout):
		parsedUrl = urlparse(url, "http")
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

			request = urllib2.Request(url)
			request.add_header('Accept-encoding', 'gzip')
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
		self.original = originalHost
		self.hosts = [Host(originalHost)]
		for extraHost in extraHosts:
			self.hosts.append(Host(extraHost))

	def openPath(self, path, scheme="http", timeout=10):
		data = None
		doSort = False
		for host in self.hosts:
			data = host.openPath(path, scheme, timeout)
			if data:
				break
			else:
				doSort = True
		if doSort:
			self.hosts.sort(key=lambda h: h.lastAccessTime())
		if data:
			return data
		raise MultiHostError