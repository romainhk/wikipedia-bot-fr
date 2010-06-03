#!/usr/bin/python
# -*- coding: utf-8  -*-
__version__ = 'ContenuDeQualité 20100602'
import re, datetime
from wikipedia import *
import pagegenerators, catlib

class ContenuDeQualite:
    """ Contenu de Qualité
        Tri et sauvegarde les AdQ/BA existants par date.
        TODO : les intentions de proposition au label.
    """
    def __init__(self, site):
        self.resume = u'BeBot : Tri du contenu de qualité'
        self.site = site
        self.qualite = []

    def __str__(self):
        resultat = u"''Contenu de Qualité''"
        print self.qualite
        return resultat

    def sauvegarder(self):
        pass
    def charger(self):
        pass

    def date(self, titre):
        try:
            page = wikipedia.Page(self.site, titre).get()
        except pywikibot.exceptions.NoPage:
            return u''
        #TODO : peu faire mieux
        dateRE = re.compile("\|date=(\d{1,2} \w{3,9} \d{2,4})", re.LOCALE)
        d = dateRE.search(page)
        if d:
            return d.group(1)
        return u''

    def run(self):
        cat_qualite = [ u'Article de qualité',  u'Bon article']
        for cat in cat_qualite:
            c = catlib.Category(self.site, cat)
            cpg = pagegenerators.CategorizedPageGenerator(c, recurse=False)
            for p in cpg:
                self.qualite.append( [ p.title(), cat, self.date(p.title()) ] )

def main():
    site = wikipedia.getSite()
    cdq = ContenuDeQualite(site)
    cdq.run()

    wikipedia.output(unicode(cdq))

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
