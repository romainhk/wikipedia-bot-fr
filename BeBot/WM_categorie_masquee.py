#!/usr/bin/python
# -*- coding: utf-8  -*-
import pywikibot, sys, BeBot

class CategorieMasquee:
    """ Categorie Masquée
        Ajoute une catégorie à la fin, entre deux <noinclude>
    """
    def __init__(self, site, categorie):
        self.site = site
        self.categorie = u'<noinclude>\n[[%s]]\n</noinclude>' % categorie
        self.resume = u'Ajout de la [[:Categorie:%s]]' % (categorie)

    def run(self):
        for a in [2007, 2008, 2009, 2010, 2011]:
            for s in range(1,53):
                p = pywikibot.Page(self.site, u'Wikipédia:Wikimag/%d/%d' % (a, s))
                if p.exists() and not p.isRedirectPage():
                    #pywikibot.output(p.title())
                    p.text += self.categorie
                    BeBot.save(p, commentaire=self.resume, minor=True)

def main():
    site = pywikibot.getSite()
    if BeBot.blocage(site):
        sys.exit(7)
    cm = CategorieMasquee(site, u'Catégorie:Numéro du Wikimag')
    cm.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
