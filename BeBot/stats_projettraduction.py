#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Stats_ProjetTraduction:
    """ Stats_ProjetTraduction
        Analyse toutes les pages de suivi du Projet:Traduction pour en donner qq stats
    """
    def __init__(self, site):
        self.site = site
        self.resume = u"Calcul de statistiques"
        self.resultats = {
            "nb_pages" => 0,
            "taille" => 0,
            "contrib" => 0,
            "duree" => 0}

    def put_resultats(self, msg):
        """ Resultats
        """
        res = pywikibot.Page(self.site, u"Utilisateur:BeBot/Stats_ProjetTraduction")
        res.text += msg
        try:
            res.save(comment=self.resume, minor=False, async=True)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de modifier la page %s" % res.title(withNamespace=True) )

    def run(self):
        bot = re.compile('bot', re.IGNORE_CASE)
        parstatut = pywikibot.Category(self.site, "Catégorie:Traduction par statut")
        for c in parstatut.subcategories(recurse=False):
            if c.title() != u"Catégorie:Liste des traductions par mois":
                pywikibot.output(c.title())
                for p in c.articles(total=3):
                    taille = BeBot.taille_page(c, 1) # en octet
                    #(oldid, u'2004-07-27T16:15:30Z', u'USER', u'CONTENU')
                    histo = c.getVersionHistory()
                    contrib = 0
                    for h in histo:
                        if not bot.search(h[2]):
                            contrib += 1
                    date_deb = datetime.datetime.strptime(histo[-1][1], '%Y-%m-%dT%H:%M:%SZ')
                    date_fin = datetime.datetime.strptime(histo[0][1], '%Y-%m-%dT%H:%M:%SZ')
                    duree = date_fin - date_deb p
                    duree = duree.days # en jours
                    
                    self.resultats["nb_page"] += 1
                    self.resultats["taille"] += taille
                    self.resultats["duree"] += duree
                    self.resultats["contrib"] += contrib
        #put_resultats()

def main():
    site = pywikibot.getSite()
    spt = Stats_ProjetTraduction(site)
    spt.run()

if __name__ == "__main__":
    try:
        main()
        pywikibot.stopme()
    finally:

