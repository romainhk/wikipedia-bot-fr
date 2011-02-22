#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class BotWikimag:
    """ Bot Wikimag
        Publie le wikimag de la semaine sur la page de discussion des abonnées
    """
    def __init__(self, site):
        self.site = site
        date = datetime.date.today()
        self.lundi = date - datetime.timedelta(days=date.weekday())
        self.lundi_pre = self.lundi - datetime.timedelta(weeks=1)
        self.semaine = self.lundi_pre.strftime("%W").lstrip('0')

    def newsboy(self, lecteur, msg):
        lecteur = pywikibot.Page(self.site, u"Utilisateur:"+lecteur).toggleTalkPage()
        if lecteur.isRedirectPage():
            lecteur = lecteur.getRedirectTarget()
        # Donne le mag au lecteur
        try:
            lecteur.put_async(lecteur.text + msg, comment=u'Demandez Cannes Midi. Le tueur de Cannes frappe encore... 5 cents', minorEdit=False)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de refourger le mag à %s" % lecteur.title(withNamespace=True) )

    def run(self):
        # Message à distribuer
        msg = u"\n== Wikimag - Semaine %s ==\n" % self.semaine
        msg += u"{{Wiki magazine|%s|%s}} ~~~~" % (self.lundi_pre.strftime("%Y"), self.semaine)

        r = re.compile(u"\*\* \{\{u\|(.+?)\}\}", re.LOCALE|re.UNICODE)
        liste = []
        for i in BeBot.page_ligne_par_ligne(self.site, u"Wikipédia:Wikimag/Abonnement"):
            m = r.search(i)
            if m is not None:
                liste.append(m.group(1))
        # Pour chaque abonné
        for l in liste:
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
