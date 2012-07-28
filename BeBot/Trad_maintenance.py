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
        self.re_trad = re.compile(r'{{Traduction}}', re.IGNORECASE)
        self.re_appel = re.compile('[\[\{]{2}Discussion:\w+?/Traduction[\]\}]{2}', re.LOCALE|re.UNICODE)
        self.re_statut = re.compile('\|\s*status\s*=\s*(\d{1})', re.LOCALE|re.UNICODE)
        
    def supprimer(self, page, backlinks):
    """ Supprime les pages voulues et nettoie les pages liées
    """
        pywikibot.output(backlinks)
        for b in backlinks:
            b.text = self.re_trad.sub(r'', b.text)
            b.text = self.re_appel.sub(r'', b.text)
            pywikibot.output(b.title())
            pywikibot.output(b.text)
            # save b
        #delete page
        
    def clore_traduction(self, page):
        """ Clôt une relecture : statut 3/4 -> 5
        """
        pass

    def run(self):
        ancien = self.date.year - 2
        re_annee = re.compile('Traduction de (\d{4})')
        parannee = pywikibot.Category(self.site, u"Catégorie:Traduction par année")
        for c in parannee.subcategories(recurse=False):
            catTitle = c.title(withNamespace=False)
            m = re_annee.match(catTitle)
            if not m:
                continue
            annee = int(m.group(1))
            if annee <= ancien: # critère d'ancienneté
                for p in c.articles(total=1, content=True):
                    supprimer = False
                    n = self.re_statut.search(p.text)
                    if not n:
                        continue
                    n = int(n.group(1))
                    pywikibot.output(u"%s !! %i" % (p.title(), n))
                    if n == 1:
                        supprimer = True
                        backlinks = []
                        for b in p.backlinks(): # pages liées
                            if b.title()[:19] == u'Projet:Traduction/*': # sera nettoyé automatiquement
                                continue
                            elif b.namespace() == 1: # utilisé comme bandeau de licence
                                supprimer = False
                                continue
                            else:
                                backlinks.append(b)
                    if n == 3 or n == 4:
                        self.clore_traduction(p)
                    if supprimer:
                        self.supprimer(p, backlinks)
                        ## Vérifier aussi les licences

def main():
    site = pywikibot.getSite()
    tm = Trad_maintenance(site)
    tm.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
