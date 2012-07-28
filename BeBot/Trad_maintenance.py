#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Trad_maintenance:
    """ Trad_maintenance
        Effectue les maintenances du Projet:Traduction :
      * supprimmer les anciennes demandes sans suite
      * clôre les relectures anciennes
    """
    def __init__(self, site):
        self.site = site
        self.resume = u"Maintenance du [[Projet:Traduction]]"
        self.date = datetime.date.today()

    def run(self):
        ancien = self.date.year - 2
        re_annee = re.compile('Traduction de (\d{4})')
        parannee = pywikibot.Category(self.site, u"Catégorie:Traduction par année")
        for c in parannee.subcategories(recurse=False):
            catTitle = c.title(withNamespace=False)
            m = re_annee.match(catTitle)
            if not m:
                continue
            annee = m.group(1)
            if annee <= ancien:
                pywikibot.output(annee)
                for p in c.articles(total=3):
                    for b in p.backlinks():
                        pywikibot.output(b.title())
            #if catTitle == u'Article \xe0 relire':
            #    for p in c.articles():
            # Vérifier aussi les licences

def main():
    site = pywikibot.getSite()
    tm = Trad_maintenance(site)
    tm.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
