#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import imaplib
import ConfigParser
from datetime import datetime

class MailAccount:
    def __init__(self, url, username, password):
        self.M = imaplib.IMAP4_SSL(url)
        self.username = username
        self.password = password
        self.login()

    def login(self):
        self.M.login(self.username, self.password)

    def checkMail(self):
        """ return list of msgids or None """
        self.M.select()
        typ, data = self.M.search(None, 'UNSEEN')
        if data[0]: # unseen mail arrived
            return data[0].split()
        
    def getHeaders(self):
        allheaders = {}
        msgnums = self.checkMail()
        if msgnums:
            for num in msgnums:
                allheaders[num] = []
                typ, data = self.M.fetch(num, '(RFC822.HEADER)')
                headers = data[0][1].split('\r\n')
                for header in headers:
                    if header.startswith('Subject:') or header.startswith('From:'):
                        allheaders[num].append(header)
        return allheaders

class CheckMailTray:
    def __init__(self):
        self.statusIcon = gtk.StatusIcon()
        self.statusIcon.set_from_file('gmail-pencil24-grey.png')
        self.statusIcon.set_visible(True)

        self.menu = gtk.Menu()
        self.menuItem = gtk.MenuItem('Check mail')
        self.menuItem.connect('activate', self.my_timer)
        self.menu.append(self.menuItem)
        self.menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.menuItem.connect('activate', self.quit_cb, self.statusIcon)
        self.menu.append(self.menuItem)
        self.statusIcon.connect('popup-menu', self.popup_menu_cb, self.menu)
        self.statusIcon.set_visible(1)

        gobject.timeout_add_seconds(7*60, self.my_timer)

        self.accounts = []
        config = ConfigParser.RawConfigParser()
        config.read('pw.ini')
        for section in config.sections():
            url = config.get(section, 'url')
            username = config.get(section, 'username')
            password = config.get(section, 'password')
            self.accounts.append(MailAccount(url, username, password))

        self.my_timer()

        gtk.main()

    def my_timer(self, *args):
        messageCount = 0
        status = ''
        for account in self.accounts:
            headers = account.getHeaders()
            messageCount += len(headers)
            for key in headers:
                status += ('\n'.join(headers[key])) + '\n\n'
            
        if messageCount > 0:
            self.statusIcon.set_from_file('gmail-pencil24.png')
        else:
            self.statusIcon.set_from_file('gmail-pencil24-grey.png')

        status += "Last checked: %s" % (datetime.now().strftime('%H:%M:%S'))
        self.statusIcon.set_tooltip(status)

        return True # to requeue the timer

    #def execute_cb(self, widget, event, data = None):
        #window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #window.set_border_width(10)
        #button = gtk.Button("Hello World")
        #button.connect_object("clicked", gtk.Widget.destroy, window)
        #window.add(button)
        #button.show()
        #window.show()

    def quit_cb(self, widget, data = None):
        self.M.close()
        self.M.logout()
        gtk.main_quit()

    def popup_menu_cb(self, widget, button, time, data = None):
        if button == 3:
            if data:
                data.show_all()
                data.popup(None, None, gtk.status_icon_position_menu,
                           3, time, self.statusIcon)

if __name__ == "__main__":
    tray = CheckMailTray()