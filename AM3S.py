#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Asterisk Manager/Monitor Multiple Server With Python
#   Copyright (C) 2017  cacaddv@gmail.com (Petruknisme a.k.a Aan Wahyu)
#   Version 0.1-dev

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import os, sys, signal, socket
from plugins.logger import Logger
import ConfigParser

# Console color
G = '\033[92m'  # green
Y = '\033[93m'  # yellow
B = '\033[94m'  # blue
R = '\033[91m'  # red
W = '\033[0m'   # white

log = Logger()
am3s_config_file = "am3s.conf"

class AM3S(object):
    def __init__(self):
         # Passing arguments
        parser = argparse.ArgumentParser(description='=[ AM3S v0.1-dev by Petruknisme]')
        parser.add_argument('--version', action='version', version='=[ AM3S v0.1-dev by Petruknisme]')
        results = parser.parse_args()

        # Asterisk Manager Interface
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverip = '127.0.0.1'
        self.serverport = 5038

        self.show_banner()

        log.console_log(G + "[*] Starting AM3S Client..." + W)

        # - Starting AM3S Client
        # - Reading config file
        # - No config file found, maybe this is the first time you are using am3s
        # - Spesify asterisk config file, user
        # - Save to config file
        # - Reading asterisk config file
        # - Try to connect to asterisk
        # - Binding port for am3s

        if not os.path.isfile(am3s_config_file):
            log.console_log(Y + "[-] No AM3S Config File Found. Will setting up for you..." + W)
            ami_config_file = raw_input("Please Specify Asterisk Manager Config Location[/etc/asterisk/manager.conf]:") or "/etc/asterisk/manager.conf"
            ami_user = raw_input("Please Specify Asterisk Manager Username:")

            log.console_log(Y + "[+] Checking Secret for Asterisk Manager..." + W, 0)
            ami_config = ConfigParser.ConfigParser()
            ami_config.read(ami_config_file)
            try:
                ami_pass = ami_config.get(ami_user, 'secret')
                if ami_pass is not None:
                    log.console_log(G + " OK!" + W)
                    log.console_log(Y + "[+] Saving Configuration to AM3S Config File. Please restart!" + W)
                    self.create_config("manager", conf_file=ami_config_file, username=ami_user, password=ami_pass)
            except:
                log.console_log(R + "Username not found on Asterisk Manager Config!" + W)

            sys.exit()
        else:
            am3s_config = ConfigParser.ConfigParser()
            am3s_config.read(am3s_config_file)
            am3s_user = am3s_config.get('manager', 'username')
            am3s_conf = am3s_config.get('manager', 'conf_file')
            am3s_pass = am3s_config.get('manager', 'password')

            log.console_log(G + "[*] Loaded Data from Configuration File..." + W)
            log.console_log("[+] Will be using " + G + am3s_conf + W + " as config file and " + G + am3s_user + W + " as user")

            log.console_log(G + "[*] Connecting to Asterisk Manager..." + W)
            self.ami_socket_connect()
            ret = self.send_command("login", Username=am3s_user, Secret=am3s_pass, Events="OFF")

            if 'Response: Success' in ret:
                    log.console_log(Y + "[+] Successfuly Connected!" + W)
            else:
                    log.console_log(R + "[-] Connect failed!" + W)

        # TODO Socket Listening on 2038
        log.console_log(G + "[*] AM3S Listening From Manager on port 2038" + W)
        self.listen_connection()

    def show_banner(self):
        banner = """
          /$$$$$$  /$$      /$$  /$$$$$$   /$$$$$$
         /$$__  $$| $$$    /$$$ /$$__  $$ /$$__  $$
        | $$  \ $$| $$$$  /$$$$|__/  \ $$| $$  \__/
        | $$$$$$$$| $$ $$/$$ $$   /$$$$$/|  $$$$$$
        | $$__  $$| $$  $$$| $$  |___  $$ \____  $$
        | $$  | $$| $$\  $ | $$ /$$  \ $$ /$$  \ $$
        | $$  | $$| $$ \/  | $$|  $$$$$$/|  $$$$$$/
        |__/  |__/|__/     |__/ \______/  \______/

        =[ AM3S v0.1-dev by Petruknisme]=
        + -- --=[ Asterisk Manager/Monitor Multiple Server ]=-- -- +
        + -- --=[ https://petruknisme.com ]=-- -- +

        """

        log.console_log(G + banner + W)

    def create_config(self, section_name, **args):
        am3s_config = ConfigParser.RawConfigParser()
        am3s_config.add_section(section_name)
        for key, value in args.items():
            am3s_config.set(section_name, key, value)

        with open(am3s_config_file, 'wb') as configfile:
            am3s_config.write(configfile)

    def ami_socket_connect(self):
        self.sock.connect((self.serverip, self.serverport))

    def send_command(self, action_name, **args):
        self.sock.send("Action: %s\r\n" % action_name)
        for key, value in args.items():
                self.sock.send("%s: %s\r\n" % (key,value))
        self.sock.send("\r\n")
        data = []
        while '\r\n\r\n' not in ''.join(data)[-4:]:
                buf = self.sock.recv(1)
                data.append(buf)
        l = ''.join(data).split('\r\n')
        return l

    def listen_connection(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = ('', 2038)
        sock.bind(server_address)
        sock.listen(1)

        while True:
            connection, client_address = sock.accept()
            try:
                print >>sys.stderr, 'client connected:', client_address
                while True:
                    data = connection.recv(16)
                    print >>sys.stderr, 'received "%s"' % data
                    if data:
                        connection.sendall(data)
                    else:
                        break
            finally:
                connection.close()

if __name__ == '__main__':
    AM3SApp = AM3S()
    AM3SApp
