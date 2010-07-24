#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime
from wikipedia import *
import pagegenerators, catlib

class TraductionDeQualite:
    """ Traduction de Qualité
    Trouve les pages qui font l'objet à la fois d'une traduction (Catégorie:Traduction par statut)
    et d'un label sur un autre WP (pages liées à {{Lien AdQ/BA}}).

    Assure un suivi pour les traductions de qualité (remplacement de GrrrrBot)
    """
    def __init__(self, site, log):
        self.resume = u"Recherche et suivi des traductions issues d'un article labellisé"
        self.resumeListing = u"Mise à jour du suivi des traductions issues d'un article labellisé"
        self.site = site
        self.log = log
        self.candidats = []  # Liste des pages de traduction contenant aussi un modele lien + le code langue commun
        self.tradQualite = [] # Les traductions de qualité connues
        
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
            self.tradQualite.append(tion)

        self.ignor_list[self.site.family.name] = {'fr':tmp}

        self.trads = [ [], [], [], [], [], [] ] # Pages de traductions d'articles de qualité classées par statut
        self.term_et_label = [ [], [], [] ]   # Traductions terminés sans label, en attente de label, labellisées

    def __str__(self):
        """
        Log à publier
        """
        resultat =  u'{{Sommaire à droite}}\nActivités de [[Utilisateur:BeBot]] le ' + datetime.date.today().strftime("%A %e %B %Y") \
                + u' concernant les articles associés au Projet:Traduction qui sont labellisés sur un autre Wikipédia.\n'
        resultat += u'== Candidats au suivi ==\n'
        resultat += u'Voici une liste des pages de suivi de traduction dont le paramètre « intérêt » pourrait être mis à "adq" ou "ba".\n\n'
        resultat += unicode(len(self.candidats)) + u' pages sont candidates :\n'
        for p in self.candidats:
            resultat += u'* [[' + p[0].title() + u']] ('+ p[1] +')\n'

        resultat +=  u'\n== Suivi des traductions ==\n'
        resultat +=  u'Mise à jour du suivi des traductions ([[Projet:Suivi des articles de qualité des autres wikipédias/Traduction]]).\n\nStatut : ### en cours de développement ###\n\n'
        resultat +=  u'\nTraductions par statut : ' + str(len(self.trads[1])) + u' demandes, ' \
                + str(len(self.trads[2])) + u' traductions en cours, ' + str(len(self.trads[3])) + u' demandes de relecture, ' \
                + str(len(self.trads[4])) + u' relectures en cours, ' + str(len(self.trads[5])) + u' terminées (' \
                + str(len(self.term_et_label[0])) + u' sans label, ' + str(len(self.term_et_label[2])) + u' labellisées).\n\n'
        # TODO: mettre un petit icone "attention"
        resultat +=  u"=== Traductions sans statut ===\nIl n'a pas été possible de trouver le statut de ces traductions :\n"
        for t in self.trads[0]:
            resultat += u'* [[' + t.title() + u']]\n'

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

    def genererListing(self, liste, simple = False):
        """
        Génère une page-listing prête à publier à partir d'une liste de pages.
        Mettre "simple" à vrai permet d'obtenir un affichage simplifié sous form de liste de liens.
        """
        if simple:
            m = []
            for t in liste:
                m.append(t.title())
            retour = u'[[' + u']], [['.join(m) + u']]'
            return retour
        else:
            retour = u''

        for i, t in enumerate(liste):
            retour += u'* {{' + t.title() + u'}}'
            if i == 12: r += u'<noinclude>'
        retour += u'\n</noinclude>'
        return retour

    def run(self):
        ##################################
        #####     Candidatures
        cats = []
        cats.append(pagegenerators.PageTitleFilterPageGenerator(pagegenerators.ReferringPageGenerator(wikipedia.Page(self.site, u"Modèle:Lien AdQ"), followRedirects=True, withTemplateInclusion=True), self.ignor_list))
        #cats.append(pagegenerators.PageTitleFilterPageGenerator(pagegenerators.ReferringPageGenerator(wikipedia.Page(self.site, u"Modèle:Lien BA"), followRedirects=True, withTemplateInclusion=True), self.ignor_list))
        for m in pagegenerators.CombinedPageGenerator(cats):
            if m.namespace() == 0: # ... alors prendre la page de trad
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

        ##################################
        #####     Mise à jour du suivi
        for tq in self.tradQualite: #Tri par statut
            statut = 0
            for cat in tq.categories(api=True):
#                print cat.title()
                if   cat.title() == u"Catégorie:Article à traduire":  #1
                    statut = 1
                    break
                elif cat.title() == u"Catégorie:Article en cours de traduction": #2
                    statut = 2
                    break
                elif cat.title() == u"Catégorie:Article à relire":    #3
                    statut = 3
                    break
                elif cat.title() == u"Catégorie:Article en cours de relecture":  #4
                    statut = 4
                    break
                elif cat.title() == u"Catégorie:Traduction terminée": #5
                    statut = 5
                    break
            self.trads[statut].append(tq)

        ### Publication des listings
        wikipedia.Page(self.site, u'Projet:Suivi des articles de qualité des autres wikipédias/Traduction/DemandeTraduction').put(self.genererListing(self.trads[1]), comment=self.resumeListing)
        wikipedia.Page(self.site, u'Projet:Suivi des articles de qualité des autres wikipédias/Traduction/EnTraduction').put(self.genererListing(self.trads[2]), comment=self.resumeListing)
#        wikipedia.Page(self.site, u'Projet:Suivi des articles de qualité des autres wikipédias/Traduction/DemandeRelecture').put(self.genererListing(self.trads[3]), comment=self.resumeListing)
#        wikipedia.Page(self.site, u'Projet:Suivi des articles de qualité des autres wikipédias/Traduction/EnRelecture').put(self.genererListing(self.trads[4]), comment=self.resumeListing)

        # Cas de statut 5 (terminé)
        for pt in self.trads[5]:
            for cat in self.togglePageTrad(pt).categories(api=True):
                if cat.title() == u"Catégorie:Article de qualité" or cat.title() == u'Catégorie:Bon article' :  #1
                    self.term_et_label[2].append(pt)
                    break
                self.term_et_label[0].append(pt)

        wikipedia.Page(self.site, u'Projet:Suivi des articles de qualité des autres wikipédias/Traduction/Labellisées').put(self.genererListing(self.term_et_label[2], simple=True), comment=self.resumeListing)
#        wikipedia.Page(self.site, u"Projet:Suivi des articles de qualité des autres wikipédias/Traduction/En attente d'être labellisées").put(self.genererListing(self.term_et_label[1]), comment=self.resumeListing)
        wikipedia.Page(self.site, u'Projet:Suivi des articles de qualité des autres wikipédias/Traduction/Terminées sans label').put(self.genererListing(self.term_et_label[0]), comment=self.resumeListing)

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
