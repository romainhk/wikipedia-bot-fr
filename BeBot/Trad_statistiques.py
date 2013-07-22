#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Stats_ProjetTraduction:
    """ Stats_ProjetTraduction
        Produit une analyse du Projet:Traduction
    """
    def __init__(self, site):
        self.site = site
        self.resume = u"Calcul de statistiques"
        self.resultats = {
            "nb_pages" : 0}
        self.categories = [ u'Traduction demand\xe9e', u'Traduction en cours', u'Traduction \xe0 relire', u'Traduction termin\xe9e' ]
        self.paravancement = {} # décompte selon l'avancement

    def put_resultats(self):
        """ Affichage des résultats
        """
        total = self.resultats['nb_pages']
        msg = u'== Statistiques ==\nAu %s\n' % datetime.datetime.today().strftime("%d/%m/%Y")
        msg += u"* Nombre total de pages : %i\n" % total
        msg += u"* Par statut:\n"
        for c, nbpages in self.paravancement.items():
            msg += u"** %s : %i\n" % (c, nbpages)
        cat = pywikibot.Category(self.site, u"Catégorie:Projet:Traduction/Articles liés")
        msg += u"* Pages de suivi actives : %i\n" % len(list(cat.articles()))
        msg += u"\n[[Catégorie:Maintenance du Projet Traduction|*]]\n"

        res = pywikibot.Page(self.site, u"Projet:Traduction/Statistiques")
        stats = re.compile(u"^== Statistiques ==[^=]*", re.DOTALL|re.MULTILINE)
        res.text = stats.sub(r'', res.text)
        res.text = res.text + msg
        BeBot.save(res, commentaire=self.resume)

    def run(self):
        for c in self.categories:
            cat = pywikibot.Category(self.site, u"Catégorie:%s" % c)
            nbpages = len(list(cat.articles()))
            self.paravancement[c] = nbpages
            self.resultats["nb_pages"] += nbpages

        self.put_resultats()

def main():
    site = pywikibot.getSite()
    if BeBot.blocage(site):
        sys.exit(7)
    spt = Stats_ProjetTraduction(site)
    spt.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
