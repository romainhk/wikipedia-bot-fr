#!/usr/bin/python
# -*- coding: utf-8  -*-
import datetime, locale
#import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class ListeDeSuivi:
    """ Liste De Suivi
        Ajoute des pages à une liste de suivi
    """
    def __init__(self, site):
        self.site = site
        self.debut = 20
        annee = datetime.date.today().strftime("%Y")
        self.page = u'Wikipédia:Wikimag/%s/' % annee
        self.nbsemaine = datetime.date(int(annee), 12, 31).strftime("%W")

    def run(self):
        for d in range(self.debut, self.nbsemaine+1):
            p = self.page+str(d)
            r = self.site.watchpage(pywikibot.Page(self.site, p))
            if r:
                pywikibot.warning(u"%s n'a pas été ajouté" % p)

def main():
    site = pywikibot.getSite()
    lds = ListeDeSuivi(site)
    lds.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
