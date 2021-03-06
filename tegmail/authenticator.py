import os
import errno

import apiclient  # noqa
import oauth2client
from oauth2client import client
from oauth2client import tools


class Authenticator(object):

    def __init__(self, scopes, secret, app_name):
        self.SCOPES = scopes
        self.CLIENT_SECRET_FILE = secret
        self.APPLICATION_NAME = app_name

    def get_credentials(self, flags):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.tegmail/credentials')

        # mkdir -p
        try:
            os.makedirs(credential_dir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(credential_dir):
                pass
            else:
                raise

        filenames = []
        for (dirpath, dirnames, fnames) in os.walk(credential_dir):
            filenames.extend(fnames)

        os.system('clear')

        if len(filenames) == 0:
            print('No credentials found!\n')
        else:
            print('Found credentials:\n')
            for filename in filenames:
                print('\t' + filename)

        try:
            user = input('\nEnter credential name: ')
        except KeyboardInterrupt:
            import sys
            sys.exit()

        credential_path = os.path.join(credential_dir,
                                       user)

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE,
                                                  self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatability with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials
