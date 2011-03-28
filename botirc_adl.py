#!/usr/bin/python
# -*- coding: utf-8  -*-
import sys
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
from ircbot import SingleServerIRCBot
#import pywikibot
 
"""
    Bot IRC gérant le chan de l'Atelier de lecture

    stats       -- Affiche des infos sur le chan
    disconnect  -- Déconnecte le bot, qui se reconnecte au bout de 60 secondes.
    die         -- Détruit le bot
"""

class Bot(SingleServerIRCBot):
    def __init__(self, channel, nickname, realname, server, port=6667):
        self.server = SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
        self.channel = channel
        #self.site = pywikibot.getSite()
        #self.page = pywikibot.Page(self.site, "Utilisateur:BeBot/Statut_Chan_Adl")
        self.total = 0
        self.modele = u"{| class=\"wikitable\"\n|-\n" \
            + u"|[http://webchat.freenode.net/?channels=#Adl Chan #Adl]\n|-\n|%d connectés\n|}"

    def on_join(self, serv, e):
        serv.execute_delayed(5, self.nb_connect)

    def nb_connect(self):
        c = self.channels.items()[0][1]
        total = len(c.users()) + len(c.opers()) + len(c.voiced())
        if self.total != total:
            # Publier sur le serveur web et récupérer en ajax depuis le gadget
            """
            try:
                self.page.put(self.modele % total, comment=u'Maj du status', minorEdit=True)
            except pywikibot.Error, e:
                pywikibot.warning(u"Impossible de donner le statut")
            """
            self.total = total
        self.connection.execute_delayed(30, self.nb_connect)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments()[0])

    def on_pubmsg(self, c, e):
        a = e.arguments()[0].split(":", 1)
        if len(a) > 1 and irc_lower(a[0]) == irc_lower(self.connection.get_nickname()):
            self.do_command(e, a[1].strip())
        return

    def do_command(self, e, cmd):
        nick = nm_to_n(e.source())
        c = self.connection

        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd == "stats":
            for chname, chobj in self.channels.items():
                c.notice(nick, "--- Statistiques du Chan ---")
                c.notice(nick, "Channel: " + chname)
                users = chobj.users()
                users.sort()
                c.notice(nick, "Users : " + ", ".join(users))
                opers = chobj.opers()
                opers.sort()
                c.notice(nick, "Opers : " + ", ".join(opers))
                voiced = chobj.voiced()
                voiced.sort()
                c.notice(nick, "Voiced: " + ", ".join(voiced))
                total = len(users) + len(opers) + len(voiced)
                c.notice(nick, "Total : " + str(total))
        else:
            c.notice(nick, "Command inconnue: " + cmd)

def main():
    # Informations
    server = 'irc.freenode.net'
    port = 6667
    channel = '#Adl'
    nickname = 'BeBot'
    realname = 'Romainhk Bot'
 
    # Connection
    bot = Bot(channel, nickname, realname, server, port)
    bot.start()

if __name__ == "__main__":
    main()

