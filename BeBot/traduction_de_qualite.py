#!/usr/bin/python
# -*- coding: utf-8  -*-
import re
from wikipedia import *
import pagegenerators, catlib

class TraductionDeQualite:
    """ Traduction de Qualité
    Trouve les pages qui font l'objet à la fois d'une traduction (Catégorie:Traduction par statut)
    et d'un label sur un autre WP (pages liées à {{Lien AdQ/BA}}).

    Assure un suivi pour les traductions de qualité (remplacement de GrrrrBot)
    """
    def __init__(self, site, log):
        self.resume = u"Log : Recherche et suivi des traductions issues d'un article labellisé"
        self.site = site
        self.log = log
        self.candidats = [] # Liste des pages de traduction contenant aussi un modele lien + le code langue commun
        
        # RE
        self.modeleLienRE = re.compile("\{\{(Lien (AdQ|BA)|Link (FA,BA))\|(\w+)\}\}", re.LOCALE)
        self.modeleTradRE = re.compile("\{\{(Traduction/Suivi|Translation/Information)[^\|\}}]*\|(\w+)\|", re.LOCALE)
        
        self.traductions = [] # Pages en cours de traduction
        cats = []
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article à traduire")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article à relire")))
        #cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article en cours de traduction")))
        #cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article en cours de relecture")))
        for t in pagegenerators.CombinedPageGenerator(cats):
            self.traductions.append(t)
        
        # On ignore les pages qui ont déjà le paramètre adq/ba
        cats = []
        self.ignor_list = {}
        tmp = []
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Traduction d'un Article de Qualité")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Traduction d'un Bon Article")))
        for tion in pagegenerators.CombinedPageGenerator(cats):
            tmp.append(self.togglePageTrad(tion).title())

        self.tradQualite = tmp # Les traductions de qualité connues
        self.ignor_list[self.site.family.name] = {'fr':tmp}

    def __str__(self):
        """
        Log à publier
        """
        resultat =  u'==Traduction de qualité==\n===Candidats===\n'
        resultat += u'Voici une liste des pages de suivi de traduction dont le paramètre « intérêt » pourrait être mis à "adq" ou "ba".\n\n'
        resultat += unicode(len(self.candidats)) + u' pages sont candidates :\n'
        for p in self.candidats:
            resultat += u'* [[' + p[0].title() + u']] ('+ p[1] +')\n'

        resultat +=  u'\n===Suivi des traductions===\n'
        resultat +=  u'Mise à jour du suivi des traductions sur la page [[Projet:Suivi des articles de qualité des autres wikipédias/Traduction]].\nStatut : ### en cours de développement ###'
        return resultat

    def togglePageTrad(self, page):
        """
        Retourne la page de traduction associée à un page, ou la page associée à une traduction
        """
        if (page.namespace() % 2) == 0:
            return wikipedia.Page(self.site, page.toggleTalkPage().title()+"/Traduction")
        else:
            # Espace de discussion
            return wikipedia.Page(self.site, page.toggleTalkPage().title().strip('/Traduction'))

    def langueCible(self, page):
        """
        Détermine la langue ciblée par une traduction et par le modèle {{Lien AdQ/BA}}.

        Retourne une liste de code langue ISO-639.
        """
        if (page.namespace() % 2) == 0:
            # Lien AdQ/BA (plusieurs langues possibles)
            m = []
            for j in self.modeleLienRE.findall(page.get()):
                m.append(j[3])
            return m
        else:
            # Suivi de traduction (une seule possible)
            m = self.modeleTradRE.search(page.get())
            if m:
                return [m.group(2)]
            else:
                return [u'IMPOSSIBLE']

    def run(self):
        # Candidatures
        cats = []
        cats.append(pagegenerators.PageTitleFilterPageGenerator(pagegenerators.ReferringPageGenerator(wikipedia.Page(self.site, u"Modèle:Lien AdQ"), followRedirects=True, withTemplateInclusion=True), self.ignor_list))
        #cats.append(pagegenerators.PageTitleFilterPageGenerator(pagegenerators.ReferringPageGenerator(wikipedia.Page(self.site, u"Modèle:Lien BA"), followRedirects=True, withTemplateInclusion=True), self.ignor_list))
        for m in pagegenerators.CombinedPageGenerator(cats):
            if m.namespace() == 0:
                #Prendre la page de trad
                tradpage = self.togglePageTrad(m)
                for t in self.traductions:
                   if t.title() == tradpage.title():
                        #Vérification de la correspondance des langues cibles
                        #print str(self.langueCible(m)) +"-----"+ str(self.langueCible(tradpage))
                        cibleTrad = self.langueCible(tradpage)[0]
                        for cible in self.langueCible(m):
                            if cibleTrad == cible:
                                self.candidats.append([tradpage, cibleTrad])
                                break;
                        break;

        # Mise à jour du suivi

def main():
    site = wikipedia.getSite()
    log = u'Utilisateur:BeBot/Traduction de qualité'

    tdq = TraductionDeQualite(site, log)
    tdq.run()
    
    wikipedia.Page(site, log).put(unicode(tdq), comment=tdq.resume, minorEdit=False)

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
