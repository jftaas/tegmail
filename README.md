# tegmail

tegmail is a command-line interface for managing your Gmail account.  
It uses the Gmail API as opposed to the conventional IMAP to access your mail.

## Alpha

tegmail is still in alpha, and may remain in alpha for an indefinite amount of time.  
It was written with a quick-and-dirty approach to create a simple command-line interface  
for Gmail accounts.

## Installation and Usage

Simply clone the repository then enter `pip install -e .`.  
This creates a binary file which you can call using `tegmail`.

tegmail requires the user to create their own project that uses Gmail API  
in order to get a client secret file, which, in turn, will be used by `tegmail`.

