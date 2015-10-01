import base64
import datetime
import email
import httplib2
import os
import re
import sys

import html2text
from apiclient import discovery
from oauth2client import tools

import tegmail


class Client(object):
    """Represents a client that handles communications
    between the Gmail API and the interface.

    Instance attributes:

     .. attribute:: gmail

        A :class:`Gmail` that represents the Gmail API handler.
     .. attribute:: interface

        A :class:`Interface` that represents user interface handler.
    """

    def __init__(self, flags, debug):

        self.debug_mode = debug
        self.messages = []
        self.states = {
            'home': 0,
            'message': 1
        }

        self.currentState = self.states['home']

        self.interface = tegmail.Interface()
        self.interface.on_key_event.append(self._on_key_event)
        self.interface.print_text('Connecting...\n')
        self.gmail = self._authenticate(flags)

        self.messages = self.get_messages(self.interface.
                                          main_box.getmaxyx()[0] - 1)

        self.interface.clear()
        self.print_messages(self.messages)

        self.update()

    def _authenticate(self, flags):
        """Retrieves credentials and authenticates.

        :return: The :class:`Gmail` retrieved from authentication.
        """
        SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
        CLIENT_SECRET_FILE = 'client_secret.json'
        APPLICATION_NAME = 'Gmail API Python Quickstart'

        authenticator = tegmail.Authenticator(SCOPES, CLIENT_SECRET_FILE,
                                              APPLICATION_NAME)
        credentials = authenticator.get_credentials(flags)
        http = credentials.authorize(httplib2.Http())

        # connection loop
        while True:
            try:
                service = discovery.build('gmail', 'v1', http=http)
                break
            except httplib2.ServerNotFoundError:
                self.interface.print_text('Server not found! Retrying...\n')
            except KeyboardInterrupt:
                self.interface.close()
                sys.exit()

        gmail = tegmail.Gmail(http, service)

        return gmail

    def _on_key_event(self, key):
        if self.currentState == self.states['home']:
            self._home_keys(key)
        elif self.currentState == self.states['message']:
            self._message_keys(key)

    # hotkeys in home state
    def _home_keys(self, key):
        if key == 'KEY_ENTER':
            self.currentState = self.states['message']
            index = self.interface.get_cursor_pos()[0]
            message = self.messages[index]

            self.interface.clear()
            self.print_message(message)
        elif key == 'j' or key == 'k':
            if not self.gmail.connected:
                return

            direction = 1 if key == 'j' else -1
            curpos = self.interface.get_cursor_pos()
            if (curpos[0] + direction < 0 or
                    curpos[0] + direction > len(self.messages) - 1):
                    return

            self.interface.move_cursor(direction)
        elif key == 'KEY_BACKSPACE':
            self.messages = self.get_messages(self.interface.
                                              main_box.getmaxyx()[0] - 1)
            self.interface.clear()
            self.print_messages(self.messages)

    # hotkeys in message state
    def _message_keys(self, key):
        if key == 'KEY_BACKSPACE':
            self.currentState = self.states['home']
            self.interface.clear()
            self.print_messages(self.messages)

    # parses date formats in payload header
    # and returns a datetime object
    def _parse_date(self, date):
        date = date.split(' ')
        date = date[:5]
        date = " ".join(date)

        date = (datetime.datetime.
                strptime(date, '%a, %d %b %Y %H:%M:%S'))

        return date

    def get_messages(self, max_results):
        messages = []
        results = self.gmail.get_messages(max_results, label_ids=['INBOX'])
        for message in results:
            messages.append(message)

        return messages

    def print_messages(self, messages):
        index = 0
        for message in messages:
            message_headers = {}
            for header in message['payload']['headers']:
                message_headers[header['name']] = header['value']

            self.interface.print_text(str(index + 1).rjust(4) + ' ')

            # read boolean
            msg = ''
            if 'UNREAD' in message['labelIds']:
                msg = 'N'
            msg = msg.ljust(4)
            self.interface.print_text(msg)

            # date
            date = self._parse_date(message_headers['Date'])

            msg = date.strftime('%b %d ')
            self.interface.print_text(msg)

            # message sender
            msg = re.sub('<.*?>', '', message_headers['From'])
            msg = msg[:16] if len(msg) > 16 else msg
            msg = msg.ljust(20)
            self.interface.print_text(msg)

            # message subject
            self.interface.print_text(message_headers['Subject'] + '\n')
            index = index + 1

        self.interface.move_cursor(0, 0)

    def print_message(self, message):
        message_headers = {}
        for header in message['payload']['headers']:
            message_headers[header['name']] = header['value']

        self.interface.print_text('Date: ' + message_headers['Date'] + '\n')
        self.interface.print_text('From: ' + message_headers['From'] + '\n')
        self.interface.print_text('To: ' + message_headers['To'] + '\n\n\n\n')

        data = self.gmail.get_message_raw(message['id'])
        data = base64.urlsafe_b64decode(data).decode('utf-8')

        message = email.message_from_string(data)
        for part in message.walk():
            if part.get_content_type() == "multipart/alternative":
                continue

            text = part.get_payload(decode=True).decode('utf-8')
            text = text.replace('\r\n', '\n')
            if part.get_content_type() == 'text/html':
                h = html2text.HTML2Text()
                text = h.handle(text)

            text = text.replace('\n', '\n\t')

            self.interface.print_text('\t' + text)

    def update(self):
        try:
            while True:
                self.interface.update()
        except KeyboardInterrupt:
            self.interface.close()

    def debug(self, text):
        if self.debug_mode:
            target = open(os.path.expanduser("~") + '/.tegmail.log', 'w')
            self.interface.clear(win=self.interface.info_box)
            self.interface.print_text('[DEBUG] ' + text,
                                      win=self.interface.info_box)
            target.write(text + '\n')
            target.close()


def main():
    try:
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None

    Client(flags, True)
