# jKnockr - Jitsi Drive-by Script

## ⚠️ Warning: Use this script responsibly and only on servers and rooms that you own or have explicit permission to test. Unauthorized use on public servers or rooms may violate terms of service and laws. The developer is not liable for any misuse of this script.

## Overview

jKnockr is a Python script designed to stress test Jitsi Meet servers by simulating multiple clients performing various actions such as messaging, hand raising, nickname changes, and video sharing. This tool helps administrators evaluate the performance and stability of their Jitsi servers under load.

## Features

- **Concurrent Clients:** Simulate multiple clients joining a room using threading.
- **Messaging:** Send custom messages to the room.
- **Crash Test:** Option to send large messages containing thousands of fake URLs to test client-side handling.
- **Hand Raising:** Simulate clients raising and lowering their hands.
- **Nickname Changes:** Change nicknames dynamically during the session.
- **YouTube Video Sharing:** Share a YouTube video in the room.

## Usage

### Prerequisites

- Python 3.x
- No external libraries are required; uses only standard Python libraries.

### Command-Line Syntax

```bash
python3 jknockr.py <target> [options]
```

- `<target>`: The room URL (e.g., `https://meet.jit.si/roomname` or `https://yourserver.com/yourroom`).

### Options

- `--crash`: Enable crash test by sending large messages with random fake URLs.
- `--message "Your message"`: Send a custom message to the room.
- `--hand`: Enable hand raising simulation.
- `--nick` or `--nick "Nickname"`: Enable nickname changes. Optionally provide a base nickname.
- `--youtube "YouTube URL"`: Share a YouTube video in the room.
- `--threads N`: Number of client threads to simulate (default is 100).

### Examples

- **Stress Test with Crash and Hand Raising:**

  ```bash
  python3 jknockr.py https://yourserver.com/yourroom --crash --hand --threads 30
  ```

- **Send Custom Message with Nickname Changes:**

  ```bash
  python3 jknockr.py https://meet.jit.si/roomname --message "Hello World" --nick --threads 5
  ```

- **Share a YouTube Video with Custom Nickname:**

  ```bash
  python3 jknockr.py https://yourserver.com/yourroom --youtube "https://www.youtube.com/watch?v=21lma6hU3mk" --nick "Tester" --threads 3
  ```

## How It Works

- **Client Simulation:** The script creates multiple threads, each simulating a client that connects to the specified Jitsi room.
- **Session Establishment:** Each client establishes a session with the server using BOSH (Bidirectional-streams Over Synchronous HTTP).
- **Actions:** Depending on the options provided, clients perform actions like sending messages, changing nicknames, raising hands, and sharing videos.
- **Crash Test:** When `--crash` is enabled, clients send large messages containing thousands of fake URLs to test the server's handling of heavy message loads.

## Important Notes

- **Ethical Use:** This script is intended for testing purposes on servers and rooms that you own or manage. Do not use it to disrupt public Jitsi Meet instances or rooms without permission.
- **Server Impact:** Running this script can significantly impact server performance. Monitor your server resources during testing.
- **Legal Responsibility:** You are responsible for ensuring that your use of this script complies with all applicable laws and terms of service.

## Interesting Finds
- Sending a [U+0010](https://unicode-explorer.com/c/0010) *( DATA LINK ESCAPE)* character disconnects you from the room. Same with using as your name.
- Client DOS possible from javascript parsing links, unicode & emojis in the chat messages.
	- Unicode in a URL is converted to puny code. *(`𓆨.中国` only 4 characters you send to the chat & itll convert to `xn--907d.xn--fiqs8s`)*
	- Using @ in a URL converts it to a `mailto://`
	- Using `ftp://` works for making clickable links also.
	- Certain text converts to an emojis *(`:)` converts to `😃`)*

___

###### Mirrors for this repository: [acid.vegas](https://git.acid.vegas/jknockr) • [SuperNETs](https://git.supernets.org/acidvegas/jknockr) • [GitHub](https://github.com/acidvegas/jknockr) • [GitLab](https://gitlab.com/acidvegas/jknockr) • [Codeberg](https://codeberg.org/acidvegas/jknockr)
