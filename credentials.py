import configparser # https://docs.python.org/3/library/configparser.html / https://stackoverflow.com/questions/8884188/how-to-read-and-write-ini-file-with-python3
import keyring # https://martinheinz.dev/blog/59
from os.path import exists



class Credentials():
    def __init__(self):
        self.credentials_file = "connections.ini"
        self.config = configparser.ConfigParser()
        self.section = "DEFAULT"

    def get_sites(self):
        if exists(self.credentials_file):
            self.config.read(self.credentials_file)
            return self.config.sections()
        return None

    def get_credentials(self):
        sites = self.get_sites()
        credentials = {}
        for site in sites:
            credentials[site] = self.get_username(site)
        return credentials

    def get_secret(self, site, username):
        return keyring.get_password(self.strip_site(site), username)
    
    def store_secret(self, site, username, secret):
        keyring.set_password(self.strip_site(site), username, secret)

    def store_site(self, site, username):
        self.config[self.strip_site(site)] = { "username": username }
        with open(self.credentials_file, 'w') as configfile:    # save
            self.config.write(configfile)

    def get_username(self, site):
        site = self.strip_site(site)
        if self.config.has_option(site, "username"):
            return self.config.get(site, "username")
        return None

    def save_credentials(self, site, username, secret):
        site = self.strip_site(site)
        self.store_secret(site, username, secret)
        if self.get_secret(site, username):
            self.store_site(site, username)
            return self.get_username(site)
        return None

    def strip_site(self, site):
        site = site.strip()
        site = site.replace("https://", "")
        site = site.replace("http://", "")
        if site[-1] == "/":
            site = site[:-1]
        return site

    def get_credentials_list(self):
        sites = self.get_sites()
        credentials = []
        if sites:
            for site in sites:
                credentials.append(f'{site} as {self.get_username(site)}')
        return credentials

