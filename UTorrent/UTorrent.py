__author__ = 'bolay'
import sys
import socket
import logging
from base64 import b64encode
from httplib import *
from urllib import quote, quote_plus, urlencode
from constants import *
import json
import re

#        uTorrent
#
#        Provides a handle with fine grained torrent state
#        and file priority methods

# date/timestamp [LEVEL] error message
logging.basicConfig(datefmt='%d %b %Y %H:%M:%S', format='%(asctime)s [%(levelname)s] %(message)s')


class UTorrent:
	username = None
	password = None
	identity = None

	#        will be happy as long as you feed it valid uTorrent WebUI details
	def __init__(self, host='localhost', port='8080', username='default', password='default'):
		#try:
			#HTTPConnection.__init__(self, host, int(port))
			#self.connect()
		#except socket.error, exception:
		#	logging.critical(exception)
		#	logging.shutdown()
		#	sys.exit(1)

		self.port = int(port)
		self.host = host
		self.username = username
		self.password = password
		self.token = None
		self.cookie = None
		if not self.requestToken():
			logging.critical("Not able to request for a token.")
			logging.shutdown()
			sys.exit(1)

	def requestToken(self):
		#self.putrequest("GET", "/gui/token.html")
		#self.putheader('Authorization', 'Basic ' + self.authString)
		conn = HTTPConnection(self.host, self.port)

		conn.request("GET", "/gui/token.html", "", {"Authorization": "Basic " + self.webui_identity()})
		#self.putheader('Authorization', 'Basic ' + self.authString)

		#if headers is not None:
		#	for (name, value) in headers.items():
				#self.putheader(name, value)

		#self.endheaders()

		#if method == r'POST':
		#	self.send(str(data))

		#webui_response = self.getresponse()
		webui_response = conn.getresponse()

		if webui_response.status == 401:
			logging.error('401 Unauthorized Access')

			return None
		print "headers:"
		print webui_response.getheaders()
		#print webui_response
		data = webui_response.read()
		m = re.compile(r"<html><div id='token' style='display:none;'>(.*)</div></html>.*").match(data)
		if m is None:
			return False
		else:
			self.cookie = webui_response.getheader("set-cookie", None)
			self.token = m.group(1)
			print "Request token: success, token =", self.token
		return True
		#return json.loads(data)

	#        creates an HTTP Basic Authentication token
	def webui_identity(self):
		if self.identity is None:
			self.identity = self.username + ':' + self.password
			self.identity = b64encode(self.identity)

		return self.identity

	#        creates and fires off an HTTP request
	#        all webui_ methods return a python object
	def webui_action(self, selector, method='GET', headers={}, data=None):
		selector = urlencode({"token": self.token}) + "&"+selector
		# self.putrequest(method, selector, False, True)
		# self.putheader('Authorization', 'Basic ' + self.authString)
		# self.putheader("Accept-Encoding", "gzip, deflate")
		# self.putheader("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
		# if self.cookie is not None:
		# 	self.putheader("set-cookie", self.cookie)
		#
		# if headers is not None:
		# 	for (name, value) in headers.items():
		# 		self.putheader(name, value)
		#
		# self.endheaders()
		#
		# if method == r'POST':
		# 	self.send(str(data))
		#
		# webui_response = self.getresponse()

		conn = HTTPConnection(self.host, self.port)
		headers["Authorization"] = "Basic " + self.webui_identity()
		#headers["Accept-Encoding"] = "gzip, deflate"
		#headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

		conn.request("GET", "/gui/", selector, headers)
		webui_response = conn.getresponse()
		print(webui_response.status, webui_response.reason)

		if webui_response.status == 401:
			logging.error('401 Unauthorized Access')

			return None
		#print webui_response
		data = webui_response.read()
		print "token =", self.token
		print selector
		#print data
		return json.loads(data)

	#        gets torrent properties
	def webui_get_props(self, torrent_hash):
		return self.webui_action(r'action=getprops&hash=' + torrent_hash)['props']

	#        sets torrent properties
	def webui_set_prop(self, torrent_hash, setting, value):
		setting = quote(setting)
		value = quote(value)

		return self.webui_action(r'action=setsetting&s=' + setting + r'&v=' + value + r'&hash=' + torrent_hash)

	#        sets a uTorrent setting
	def webui_set(self, setting, value):
		setting = quote(setting)
		value = quote(value)

		return self.webui_action(r'action=setsetting&s=' + setting + r'&v=' + value)

	#        gets uTorrent settings
	def webui_get(self):
		return self.webui_action(r'action=getsettings')['settings']

	#        adds a torrent via url
	#        you need to check webui_ls() again *after* you get this result
	#        otherwise, the torrent might not show up and you won't know
	#        if it was successfully added.
	def webui_add_url(self, torrent_url):
		return self.webui_action(r'action=add-url&s=' + quote(torrent_url) + r'&list=1')

	#        adds a torrent via POST
	def webui_add_file(self, torrent_file):
		CRLF = '\r\n'
		method = r'POST'
		boundary = r'---------------------------22385145923439'
		headers = {r'Content-Type': r'multipart/form-data; boundary=' + boundary}
		data = ''

		try:
			torrent = open(torrent_file, 'rb')
			torrent = torrent.read()
		except IOError:
			logging.error('Torrent I/O Error')

			return None

		data += "--%s%s" % (boundary, CRLF)
		data += "Content-Disposition: form-data; name=\"torrent_file\"; filename=\"%s\"%s" % (torrent_file, CRLF)
		data += "Content-Type: application/x-bittorrent%s" % CRLF
		data += "%s" % CRLF
		data += torrent + CRLF
		data += "--%s--%s" % (boundary, CRLF)

		headers['Content-Length'] = str(len(data))

		return self.webui_action(r'action=add-file', method=method, headers=headers, data=data)

	#        removes a torrent
	def webui_remove(self, torrent_hash):
		return self.webui_action(r'action=remove&hash=' + torrent_hash)

	#        removes a torrent and data
	def webui_remove_data(self, torrent_hash):
		return self.webui_action(r'action=removedata&hash=' + torrent_hash)

	#        returns a giant listing of uTorrentness
	def webui_ls(self):
		return self.webui_action(r'list=1')['torrents']

	#        returns a giant listing of uTorrentness files for a given torrent
	def webui_ls_files(self, torrent_hash):
		return self.webui_action(r'/gui/?action=getfiles&hash=' + torrent_hash)

	#        starts a torrent
	def webui_start_torrent(self, torrent_hash):
		return self.webui_action(r'action=start&hash=' + torrent_hash + r'&list=1')

	#        force starts a torrent
	#        don't ever do this. please. this is for the sake of completeness.
	def webui_forcestart_torrent(self, torrent_hash):
		return self.webui_action(r'action=forcestart&hash=' + torrent_hash + r'&list=1')

	#        pause a torrent
	def webui_pause_torrent(self, torrent_hash):
		return self.webui_action(r'action=pause&hash=' + torrent_hash + r'&list=1')

	#        stop a torrent
	def webui_stop_torrent(self, torrent_hash):
		return self.webui_action(r'action=stop&hash=' + torrent_hash + r'&list=1')

	#        set priority on a list of files
	def webui_prio_file(self, torrent_hash, torrent_files, torrent_file_prio):
		webui_cmd_prio = r'action=setprio&hash='
		webui_cmd_prio += torrent_hash
		webui_cmd_prio += r'&p='
		webui_cmd_prio += torrent_file_prio

		for torrent_file_idx in torrent_files:
			webui_cmd_prio += r'&f='
			webui_cmd_prio += torrent_file_idx

		return self.webui_action(webui_cmd_prio)

	#def getTorrents(self):
	#	return self.webui_ls()

	#        returns a dictionary of torrent names and hashes
	def uls_torrents(self):
		raw_torrent_list = self.webui_ls()
		torrent_list = {}

		for torrent in raw_torrent_list:
			torrent_list[torrent[UT_TORRENT_PROP_NAME]] = torrent[UT_TORRENT_PROP_HASH]

		return torrent_list

	def getTorrentFiles(self, hash):
		return self.webui_ls_files(hash)['files'][1:][0]

	#        returns a dictionary of file names mapping tuples of indices and parent torrent hashes
	def uls_files(self, torrent_name=None, torrent_hash=None):
		if (torrent_name is None) and (torrent_hash is None):
			logging.error('Specify torrent_name or torrent_hash')

			return None

		#        faster, will use this if possible
		if torrent_hash is not None:
			raw_file_list = self.webui_ls_files(torrent_hash)['files'][1:]

		#        slow since we need to look up the hash
		else:
			torrent_hash = self.uls_torrents()[torrent_name]
			raw_file_list = self.webui_ls_files(torrent_hash)['files'][1:]

		file_list = {}
		i = 0

		for filename in raw_file_list[0]:
			file_list[filename[0]] = (i, torrent_hash)

			i += 1

		return file_list

	#        sets the current state of a list of torrents
	def uset_torrents_state(self, torrent_state, torrent_list_name=None, torrent_list_hash=None):
		if (torrent_list_name is None) and (torrent_list_hash is None):
			logging.error('Specify torrent_list_name or torrent_list_hash')

			return None

		if torrent_list_hash is None:
			current_torrents = self.uls_torrents()

		if torrent_state == UT_TORRENT_STATE_STOP:
			if torrent_list_hash is not None:
				for torrent in torrent_list_hash:
					self.webui_stop_torrent(torrent)
			else:
				for torrent in torrent_list_name:
					self.webui_stop_torrent(current_torrents[torrent])

			return True

		elif torrent_state == UT_TORRENT_STATE_START:
			if torrent_list_hash is not None:
				for torrent in torrent_list_hash:
					self.webui_start_torrent(torrent)

			else:
				for torrent in torrent_list_name:
					self.webui_start_torrent(current_torrents[torrent])

			return True

		elif torrent_state == UT_TORRENT_STATE_PAUSE:
			if torrent_list_hash is not None:
				for torrent in torrent_list_hash:
					self.webui_pause_torrent(torrent)

			else:
				for torrent in torrent_list_name:
					self.webui_pause_torrent(current_torrents[torrent])

			return True

		elif torrent_state == UT_TORRENT_STATE_FORCESTART:
			if torrent_list_hash is not None:
				for torrent in torrent_list_hash:
					self.webui_forcestart_torrent(torrent)

			else:
				for torrent in torrent_list_name:
					self.webui_forcestart_torrent(current_torrents[torrent])

			return True

		else:
			return False

	#        sets the current priority of a list of files
	def uprio_files(self, file_list, file_prio, torrent_name=None, torrent_hash=None):
		if (torrent_name is None) and (torrent_hash is None):
			logging.error('Specify torrent_name or torrent_hash')

			return None

		#        whee, faster
		if torrent_hash is not None:
			current_files = self.uls_files(torrent_hash=torrent_hash)

		#        slow since we need to look up the hash
		else:
			torrent_list = self.uls_torrents()
			current_files = self.uls_files(torrent_name=torrent_name)

		file_idx_list = []

		for filename in file_list:
			file_idx_list.append(str(current_files[filename][0]))

		#        whee, faster
		if torrent_hash is not None:
			for filename in file_list:
				self.webui_prio_file(torrent_hash, file_idx_list, file_prio)

		#        ew, slower
		else:
			for filename in file_list:
				self.webui_prio_file(torrent_list[torrent_name], file_idx_list, file_prio)