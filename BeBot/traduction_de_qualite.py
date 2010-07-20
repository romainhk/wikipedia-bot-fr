#!/usr/bin/python
# -*- coding: utf-8  -*-
import re
from wikipedia import *
import pagegenerators, catlib

class TraductionDeQualite:
    """ Traduction de Qualité
    Trouve les pages qui font l'objet à la fois d'une traduction (Catégorie:Traduction par statut)
    et d'un label sur un autre WP (pages liées à {{Lien AdQ/BA}}).
    """
    def __init__(self, site, log):
        self.resume = u"Recherche des traductions issues d'un article labellisé"
        self.site = site
        self.log = log
        self.page_resultat = wikipedia.Page(site, log)
        self.pages = [] # Liste des pages de traduction contenant un modele lien

        """
        self.traductions = [] # Pages en cours de traduction
        cats = []
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article à traduire")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article à relire")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article en cours de traduction")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article en cours de relecture")))
        for t in pagegenerators.CombinedPageGenerator(cats):
            self.traductions.append(t)
        """

    def __str__(self):
        """
        Log à publier
        """
        resultat = u'' + unicode(self.pages)
        return resultat

    def run(self):
        cats = []
        cats.append(pagegenerators.ReferringPageGenerator(wikipedia.Page(self.site, u"Modèle:Lien AdQ"), followRedirects=True, withTemplateInclusion=True))
        cats.append(pagegenerators.ReferringPageGenerator(wikipedia.Page(self.site, u"Modèle:Lien BA"), followRedirects=True, withTemplateInclusion=True))
        for m in pagegenerators.CombinedPageGenerator(cats):
            if m.namespace == 0:
                #Prendre la page de trad
                m = m.toggleTalkPage()
                tradpage = wikipedia.Page(self.site, m.title()+"/Traduction")
                if tradpage.exist():
                   self.pages.append(tradpage)
                   # for t in self.traductions:
                   #    if t == m:
                   #         self.pages.append(tradpage)
                   #         break;

def main():
    site = wikipedia.getSite()
    log = u'Utilisateur:BeBot/Traduction de qualité'

    cdq = TraductionDeQualite(site, log)
    cdq.run()
    
    print unicode(cdq)
    #wikipedia.Page(site, log).put(unicode(cdq), comment=cdq.resume, minorEdit=False)

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
