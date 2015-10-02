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

    def __init__(self, flags, debug=False):
        self.debug_mode = debug
        self.messages = []
        self.states = {
            'home': 0,
            'message': 1
        }

        self.currentState = self.states['home']
        self._flags = flags  # for client restart

        SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
        CLIENT_SECRET_FILE = 'client_secret.json'
        APPLICATION_NAME = 'Gmail API Python Quickstart'

        authenticator = tegmail.Authenticator(SCOPES, CLIENT_SECRET_FILE,
                                              APPLICATION_NAME)
        credentials = authenticator.get_credentials(flags)

        self.interface = tegmail.Interface()
        self.interface.on_key_event.append(self._on_key_event)
        self.interface.print_text('Connecting...\n')

        self.gmail = self._authenticate(credentials)
        self.messages = self.get_messages(self.interface.
                                          main_box.getmaxyx()[0] - 1)
        self.interface.clear()
        self.print_messages(self.messages)
        self.update()

    def _authenticate(self, credentials):
        """Retrieves credentials and authenticates.

        :return: The :class:`Gmail` retrieved from authentication.
        """
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

        return tegmail.Gmail(http, service)

    def _on_key_event(self, key):
        if self.currentState == self.states['home']:
            self._home_keys(key)
        elif self.currentState == self.states['message']:
            self._message_keys(key)

    # hotkeys in home state
    def _home_keys(self, key):
        if not self.gmail.connected:
            return

        if key == 'KEY_ESCAPE' or key == 'q':
            self.interface.close()
            self.__init__(self._flags)
        elif key == 'KEY_ENTER':
            self.currentState = self.states['message']
            index = self.interface.get_cursor_pos()[0]

            self.interface.clear()
            message = self.read_message(self.messages[index])
            self.messages[index] = message  # update client-side unread flag
        elif key == 'd':
            index = self.interface.get_cursor_pos()[0]
            self.gmail.trash_message(self.messages[index]['id'])
            self.interface.add_char(index, 5, ord('D'))
        elif key == 'j' or key == 'k':
            direction = 1 if key == 'j' else -1
            curpos = self.interface.get_cursor_pos()
            if (curpos[0] + direction < 0 or
                    curpos[0] + direction > len(self.messages) - 1):
                    return

            self.interface.move_cursor(direction)
        elif key == 'KEY_BACKSPACE' or key == 'r':
            self.interface.print_text('Retrieving mail...',
                                      self.interface.info_box)
            self.messages = self.get_messages(self.interface.
                                              main_box.getmaxyx()[0] - 1)
            self.interface.clear(self.interface.info_box)
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

        try:
            date = (datetime.datetime.
                    strptime(date, '%a, %d %b %Y %H:%M:%S'))
        except ValueError:
            date = (datetime.datetime.
                    strptime(date, '%d %b %Y %H:%M:%S %z'))

        return date

    def get_messages(self, max_results):
        messages = []
        results = self.gmail.get_messages(max_results, label_ids=['INBOX'])
        for message in results:
            messages.append(message)

        return messages

    def print_messages(self, messages):
        """Displays all messages."""
        index = 0
        for message in messages:
            message_headers = {}
            for header in message['payload']['headers']:
                message_headers[header['name']] = header['value']

            msg = str(index + 1).rjust(4) + ' '
            self.interface.print_text(msg)

            # read boolean
            msg = ('N' if 'UNREAD' in message['labelIds'] else ' ').ljust(4)
            self.interface.print_text(msg)

            # date
            date = self._parse_date(message_headers['Date'])
            msg = date.strftime('%b %d ')
            self.interface.print_text(msg)

            # message sender
            msg = re.sub('<.*?>', '', message_headers['From'])
            msg = (msg[:16] if len(msg) > 16 else msg).ljust(20)
            self.interface.print_text(msg)

            # message subject
            self.interface.print_text(message_headers['Subject'] + '\n')
            index = index + 1

        self.interface.move_cursor(0, 0)

    def read_message(self, message):
        """Displays message contents."""
        self.gmail.modify_message(message['id'], removeLabelIds=['UNREAD'])
        try:
            message['labelIds'].remove('UNREAD')
        except ValueError:
            pass

        message_headers = {}
        for header in message['payload']['headers']:
            message_headers[header['name']] = header['value']

        self.interface.print_text('Date: ' + message_headers['Date'] + '\n')
        self.interface.print_text('From: ' + message_headers['From'] + '\n')
        self.interface.print_text('To: ' + message_headers['To'] + '\n\n\n\n')

        data = self.gmail.get_message_raw(message['id'])
        data = base64.urlsafe_b64decode(data).decode('utf-8')

        email_message = email.message_from_string(data)
        for part in email_message.walk():
            if (part.get_content_type() == "multipart/alternative" or
                    'text/' not in part.get_content_type()):
                continue

            try:
                text = part.get_payload(decode=True).decode('utf-8')
            except UnicodeDecodeError:
                text = part.get_payload(decode=True).decode('latin-1')

            text = text.replace('\r\n', '\n')

            if part.get_content_type() == 'text/html':
                h = html2text.HTML2Text()
                text = h.handle(text)

            text = text.replace('\n', '\n\t')
            self.interface.print_text('\t' + text)

        return message

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
