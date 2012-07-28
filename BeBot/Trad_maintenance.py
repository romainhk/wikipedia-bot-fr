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
        re_projet = re.compile(r'Projet:Traduction/*')
        parannee = pywikibot.Category(self.site, u"Catégorie:Traduction par année")
        for c in parannee.subcategories(recurse=False):
            catTitle = c.title(withNamespace=False)
            m = re_annee.match(catTitle)
            pywikibot.output(catTitle)
            if not m:
                continue
            annee = int(m.group(1))
            if annee <= ancien: # critère d'ancienneté
                for p in c.articles(total=3):
                    for b in p.backlinks(): # pages liées
                        if b.title()[:19] != u'Projet:Traduction/*':
                            pywikibot.output(b.title())
                        #Supprimer la page
                        # Vérifier aussi les licences
                    #CHanger le status

def main():
    site = pywikibot.getSite()
    tm = Trad_maintenance(site)
    tm.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
