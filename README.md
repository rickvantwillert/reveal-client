# reveal-client

## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [User guide](#user-guide)
* [Developer guide](#developer-guide)

## General info
The reveaul-client project provides a command line interface tool specifically
targetted at users with a visual impairment.
It's setup in a modular fashion, so modules for specific applications can be
added. By default a module for Atlassian Confluence is included.
	
## Technologies
Project is created with:
* Python 3.9.6
* [html2text](https://pypi.org/project/html2text/)
* [atlassian-python-api](https://atlassian-python-api.readthedocs.io/)
	
## Setup
To install this client, install it locally using git clone and install the
dependencies using pip:

```
$ git clone https://github.com/rickvantwillert/reveal-client.git
$ python -m pip install html2text,atlassian-python-api
```

## User guide

### Start the tool
Navigate to the installation directory and run `python reveal.py`

### Using the tool
After starting the app, it will ask you the following:
1. To which service (app) you would like to connect. Enter the number of choice
and hit Enter.
2. If you want to use a new connection or one you have been using earlier. Once
a new connection is created it will be saved and listed for quick access.
Credentials are stored in your OS account's keyring.
3. If connected succesfully, you can type `menu` for the main menu options or
`?` for the help menu (context sensitive).

Whenever an option is preceded by a number, type the number and hit Enter to
open it. In all other cases, the available commands for the current context are
avalable by typing `?` or `help`.

### Connecting to a new app/service
When selecting to connect to a new service:
1. First enter the URL of the service,
for example: `https://example.atlassian.net`
2. Next enter you username. In case of Confluence, this should be your
email address
3. Lastly, enter your password or API Token. In case of Confluence, enter your
API token.
[More info](https://id.atlassian.com/manage-profile/security/api-tokens)

NOTE: To update your credentials for an existing saved connection, create a new
connection for the same service/app.

## Developers guide
TBD - Details on how to develop a module for an application will be added soon.