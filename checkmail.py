#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import sys
import os
import gobject
import imaplib
import ConfigParser
from threading import Thread
from datetime import datetime
from email.header import decode_header

class MailAccount:
    def __init__(self, name, url, username, password):
        self.name = name
        self.url = url
        self.username = username
        self.password = password

    def login(self):
        self.M = imaplib.IMAP4_SSL(self.url)
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
                        decodedHeader = ""
                        decodedParts = decode_header(header)
                        for part in decodedParts:
                            if part[1]:
                                decodedHeader += unicode(*part)
                            else:
                                decodedHeader += part[0]

                        allheaders[num].append(decodedHeader)
        return allheaders
    
    def close(self):
        self.M.close()
        self.M.logout()
        del self.M

class MyThread(Thread):
    def __init__(self, tray):
        super(MyThread, self).__init__()
        self.tray = tray

    def run(self):
        status = ''
        totalCount = 0
        for account in self.tray.accounts:
            try:
                account.login()
                headers = account.getHeaders()
                messageCount = len(headers)
                if messageCount:
                    status += account.name + '\n' + '-----------\n'
                for key in headers:
                    status += ('\n'.join(headers[key])) + '\n\n'
                totalCount += messageCount
                account.close()
            except Exception, e:
                print e
                
        if totalCount > 0:
            gobject.idle_add(self.tray.statusIcon.set_from_file, os.path.join(os.path.dirname(__file__), 'gmail-pencil24.png'))
        else:
            gobject.idle_add(self.tray.statusIcon.set_from_file, os.path.join(os.path.dirname(__file__), 'gmail-pencil24-grey.png'))

        status += "Last checked: %s" % (datetime.now().strftime('%H:%M:%S'))
        gobject.idle_add(self.tray.statusIcon.set_tooltip, status)


class CheckMailTray(object):
    def __init__(self):
        self.statusIcon = gtk.StatusIcon()
        self.statusIcon.set_from_file(os.path.join(os.path.dirname(__file__), 'gmail-pencil24-grey.png'))
        self.statusIcon.set_visible(True)

        self.menu = gtk.Menu()

        self.menuItem = gtk.MenuItem('Check mail')
        self.menuItem.connect('activate', self.my_timer)
        self.menu.append(self.menuItem)

        #self.menuItem = gtk.MenuItem('Debug')
        #self.menuItem.connect('activate', self.debug)
        #self.menu.append(self.menuItem)

        self.menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.menuItem.connect('activate', self.quit_cb, self.statusIcon)
        self.menu.append(self.menuItem)

        self.statusIcon.connect('popup-menu', self.popup_menu_cb, self.menu)
        self.statusIcon.set_visible(1)

        gobject.timeout_add_seconds(15*60, self.my_timer)

        self.accounts = []
        config = ConfigParser.RawConfigParser()
        config.read(os.path.expanduser('~/.pw.ini'))
        if config.sections():
            for section in config.sections():
                url = config.get(section, 'url')
                username = config.get(section, 'username')
                password = config.get(section, 'password')
                self.accounts.append(MailAccount(section, url, username, password))
        else:
            print "No config"
            sys.exit()

        self.my_timer()

        gtk.main()


    def my_timer(self, *args):
        self.statusIcon.set_from_file(os.path.join(os.path.dirname(__file__), 'gmail-pencil24-pending.png'))
        #gtk.gdk.flush()
        thread = MyThread(self)
        thread.start()
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
        gtk.main_quit()

    def popup_menu_cb(self, widget, button, time, data = None):
        if button == 3:
            if data:
                data.show_all()
                data.popup(None, None, gtk.status_icon_position_menu,
                           3, time, self.statusIcon)

if __name__ == "__main__":
    gtk.gdk.threads_init()
    tray = CheckMailTray()
