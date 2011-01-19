#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
#import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class BotWikimag:
    """ Bot Wikimag
        Publie le wikimag de la semaine (à partir de la "Catégorie:Lecteur du Wikimag")
    """
    def __init__(self, site):
        self.site = site
        date = datetime.date.today()
        self.lundi = date - datetime.timedelta(days=date.weekday())
        self.lundi_pre = self.lundi - datetime.timedelta(weeks=1)
        self.semaine = self.lundi_pre.strftime("%W").lstrip('0')

        self.mag = pywikibot.Page(site, u'Wikipédia:Wikimag/%s/%s' % \
                (self.lundi_pre.strftime("%Y"), self.semaine) )
        if self.mag.isRedirectPage():
            self.mag = self.mag.getRedirectTarget()

        self.liste = pywikibot.Category(self.site, u"Lecteur du Wikimag")

    def newsboy(self, lecteur, msg):
        lecteur = lecteur.toggleTalkPage()
        # Donne le mag au lecteur
        try:
            lecteur.put(lecteur.text + msg, comment=u'Wikimag ! Qui veux le Wikimag ? ... 0 cents !', minorEdit=False)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de refourger le mag à %s" % lecteur.title(withNamespace=True) )

    def run(self):
        # Message à distribuer
        msg = u"\n== Wikimag - Semaine %s ==\n" % self.semaine
        msg += u"{{Wiki magazine|%s|%s}} ~~~~" % (self.lundi_pre.strftime("%Y"), self.semaine)
        # Retourne une liste d'abonnés : return list(self.liste.articles())
        for l in self.liste.articles():
            self.newsboy(l, msg)

def main():
    site = pywikibot.getSite()
    bw = BotWikimag(site)
    bw.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
