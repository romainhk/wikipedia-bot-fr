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

        # On retire ceux qui ont déjà le paramètre adq/ba
        cats = []
        self.ignor_list = {}
        tmp = []
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Traduction d'un Article de Qualité")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Traduction d'un Bon Article")))
        for tion in pagegenerators.CombinedPageGenerator(cats):
            tmp.append(tion.toggleTalkPage().title().strip('/Traduction'))
        self.ignor_list[self.site.family.name] = {'fr':tmp}

        self.traductions = [] # Pages en cours de traduction
        cats = []
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article à traduire")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article à relire")))
        #cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article en cours de traduction")))
        #cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article en cours de relecture")))
        for t in pagegenerators.CombinedPageGenerator(cats):
            self.traductions.append(t)

    def __str__(self):
        """
        Log à publier
        """
        resultat = unicode(len(self.pages)) + u' candidats :'
        for p in self.pages:
            resultat += u', ' + p.title()
        return resultat

    def run(self):
        cats = []
        cats.append(pagegenerators.PageTitleFilterPageGenerator(pagegenerators.ReferringPageGenerator(wikipedia.Page(self.site, u"Modèle:Lien AdQ"), followRedirects=True, withTemplateInclusion=True), self.ignor_list))
        cats.append(pagegenerators.PageTitleFilterPageGenerator(pagegenerators.ReferringPageGenerator(wikipedia.Page(self.site, u"Modèle:Lien BA"), followRedirects=True, withTemplateInclusion=True), self.ignor_list))
        for m in pagegenerators.CombinedPageGenerator(cats):
            if m.namespace() == 0:
                #Prendre la page de trad
                tradpage = wikipedia.Page(self.site, m.toggleTalkPage().title()+"/Traduction")
                for t in self.traductions:
                   if t.title() == tradpage.title():
                        self.pages.append(tradpage)
                        break;
         #TODO: Vérifier que les langues cible correspondent

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
