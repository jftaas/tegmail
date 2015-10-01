from apiclient import errors
from apiclient.http import BatchHttpRequest


class Gmail(object):

    def __init__(self, http, service):
        self.connected = False
        self.labels = {}
        self.events = {
            'on_message': []
        }

        self._http = http
        self._service = service
        self._users = service.users()
        self._labels = self._get_labels()

        self._start()
        self.connected = True

    def _start(self):
        for label in self._labels:
            self.labels[label['id']] = label['name']

    def _get_labels(self):
        try:
            results = self._users.labels().list(userId='me').execute()
            labels = results.get('labels', [])
        except errors.HttpError:
            labels = {}

        return labels

    def _get_message_ids(self, max_results, label_ids, page_token):
        try:
            if not page_token:
                response = self._users.messages().list(userId='me',
                                                       labelIds=label_ids,
                                                       maxResults=max_results
                                                       ).execute()
            else:
                response = self._users.messages().list(userId='me',
                                                       labelIds=label_ids,
                                                       maxResults=max_results,
                                                       pageToken=page_token
                                                       ).execute()

            return response
        except errors.HttpError:
            return None

    def get_messages(self, max_results=10, request_format=None,
                     label_ids=[], page_token=None):
        response = self._get_message_ids(max_results, label_ids, page_token)
        if not response:
            return []

        if not request_format:
            request_format = 'metadata'

        messages = []

        def on_get_message(request_id, response, exception):
            if exception is not None:
                return

            messages.append(response)

        batch = BatchHttpRequest(callback=on_get_message)
        try:
            for message in response['messages']:
                # message_ids.append(message['id'])
                batch.add(self._users.messages().get(id=message['id'],
                                                     userId='me',
                                                     format=request_format))
            batch.execute(http=self._http)
        except KeyError:
            return messages

        return messages

    def get_message_raw(self, message_id):
        response = self._users.messages().get(id=message_id,
                                              userId='me',
                                              format='raw').execute()
        return response['raw']

    def modify_message(self, message_id, removeLabelIds=[], addLabelIds=[]):
        try:
            body = {'addLabelIds': addLabelIds,
                    'removeLabelIds': removeLabelIds}
            response = self._users.messages().modify(id=message_id,
                                                     userId='me',
                                                     body=body).execute()
            return response
        except errors.HttpError as error:
            print(error)

    def trash_message(self, message_id):
        try:
            self._users.messages().trash(id=message_id,
                                         userId='me').execute()
        except errors.HttpError as error:
            print(error)
