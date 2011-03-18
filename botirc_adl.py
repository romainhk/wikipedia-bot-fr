#!/usr/bin/python
# -*- coding: utf-8  -*-
import irclib
 
"""
    Bot IRC gérant la chan de l'Atelier de lecture
"""
#Informations
network = 'irc.freenode.net'
port = 6667
channel = '#Adl'
nick = 'BeBot'
name = 'BeBot'
 
#Connection
irc = irclib.IRC()
server = irc.server()
server.connect(network, port, nick, ircname = name)
server.join(channel)
 
irc.process_forever()
