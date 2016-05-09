#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Stefan Jansen'

from digitalocean import Droplet, Manager

from storm.parsers.ssh_config_parser import ConfigParser as StormParser
from getpass import getuser
from os import environ
import pprint
import requests


class DigitalOcean:
    def __init__(self):
        self.token = environ['DO_API_TOKEN']
        self.ssh_id = self.get_ssh_keys()
        self.ssh_config = StormParser('/users/{}/.ssh/config'.format(getuser()))
        self.droplet = {}
        self.droplet_attrs = ['name', 'disk', 'image', 'size_slug', 'ip_address']

    def update_ssh(self):
        """Update ssh config with new ip address and add missing users"""

        self.ssh_config.load()
        users = {'do': 'root', 'do2': 'kaggle'}
        for host in users.keys():
            if self.ssh_config.search_host(host):
                self.ssh_config.update_host(host, {'user': users[host], 'hostname': self.droplet['ip_address']})
            else:
                self.ssh_config.add_host(host, {'user': users[host], 'hostname': self.droplet['ip_address']})
        self.ssh_config.write_to_ssh_config()

    def launch(self, name='test', region='nyc2', image='ubuntu-16-04-x64', size='512mb'):
        """Launch DigitalOcean droplet instance"""

        with open('cloud-config.txt') as txt:
            user_data = txt.read()

        droplet = Droplet(token=self.token, name=name, region=region, image=image, size_slug=size, backups=False,
                          ssh_keys=self.ssh_id, user_data=user_data)
        droplet.create()

        self.droplet['id'] = droplet.id
        while not self.droplet.get('ip_address', None):
            self.droplet['ip_address'] = droplet.load().ip_address
        self.update_ssh()
        pprint.pprint({a: getattr(droplet, a) for a in self.droplet_attrs})

    def get_droplets(self):
        """Get active droplets"""
        manager = Manager(token=self.token)
        my_droplets = manager.get_all_droplets()
        return my_droplets

    def destroy(self):
        """Destroy all active droplets"""
        my_droplets = self.get_droplets()
        for droplet in my_droplets:
            droplet.destroy()

    def get_ssh_keys(self):
        """Get ssh keys stored with DigitalOcean"""

        do_ssh_url = 'https://api.digitalocean.com/v2/account/keys'
        headers = dict(Authorization='Bearer {}'.format(self.token))
        response = requests.get(url=do_ssh_url, headers=headers)
        ssh_keys = []
        for ssh_key in response.json().get('ssh_keys'):
            ssh_keys.append(ssh_key.get('id'))
        return ssh_keys

if __name__ == '__main__':
    do = DigitalOcean()
    do.destroy()
    # do.launch()
