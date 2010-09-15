#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
import BeBot
import pywikibot
from pywikibot import pagegenerators, catlib
locale.setlocale(locale.LC_ALL, '')

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
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article en cours de traduction")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Article en cours de relecture")))
        for t in pagegenerators.CombinedPageGenerator(cats):
            self.traductions.append(t)
        
        cats = []
        self.ignor_list = u'' # On ignore les pages qui ont déjà le paramètre adq/ba
        tmp = []
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Traduction d'un Article de Qualité")))
        cats.append(pagegenerators.CategorizedPageGenerator(catlib.Category(self.site, u"Catégorie:Traduction d'un Bon Article")))
        gen = pagegenerators.DuplicateFilterPageGenerator(pagegenerators.CombinedPageGenerator(cats))
        gen = pagegenerators.PreloadingGenerator(gen, step=125)
        for tion in gen:
            a = BeBot.togglePageTrad(tion).title()
            tmp.append(a.replace('(', '\\x28').replace(')', '\\x29'))
                #Remplacement des parenthèses à cause d'un problème de comparaison de chaine utf-8 ; ex : Timée (Platon)
            self.tradQualite.append(tion)
            self.ignor_list += u' %s ;;' % a

        self.trads = [ [], [], [], [], [], [] ] # Pages de traductions d'articles de qualité classées par statut
        self.term_et_label = [ [], [], [] ]   # Traductions terminées sans label, en attente de label, ou labellisées

    def __str__(self):
        """
        Log à publier
        """
        resultat = u'{{Sommaire à droite}}\nActivités du %s' \
                % unicode(datetime.date.today().strftime("%A %e %B %Y"), "utf-8")
        resultat += u' concernant les articles associés au Projet:Traduction qui sont labellisés sur un autre Wikipédia.\n'
        resultat += u'== Candidats au suivi ==\n'
        resultat += u'Voici une liste des pages de suivi de traduction dont le paramètre « intérêt » pourrait être mis à "adq" ou "ba".\n\n'
        resultat += u'%s pages sont candidates :\n' % unicode(len(self.candidats))
        for p in self.candidats:
            resultat += u'* [[' + p[0].title() + u']] ('+ p[1] +')\n'

        resultat +=  u'\n== Suivi des traductions ==\n'
        resultat +=  u'Mise à jour du suivi des %s traductions sur [[Projet:Suivi des articles de qualité des autres wikipédias/Traduction]].\n\n' \
            % str(len(self.trads[1]) + len(self.trads[2]) + len(self.trads[3]) + len(self.trads[4]) + len(self.trads[5]) )
        resultat +=  u'Par statut : ' + str(len(self.trads[1])) + u' demandes, ' \
                + str(len(self.trads[2])) + u' traductions en cours, ' + str(len(self.trads[3])) + u' demandes de relecture, ' \
                + str(len(self.trads[4])) + u' relectures en cours, ' + str(len(self.trads[5])) + u' terminées (' \
                + str(len(self.term_et_label[0])) + u' sans label, ' + str(len(self.term_et_label[2])) + u' labellisées).\n\n'
        if len(self.trads[0]) > 0:
            resultat +=  u"=== [[Image:Nuvola apps important yellow.svg|30px|À vérifier]] Traductions sans statut ===\nIl n'a pas été possible de trouver le statut de ces traductions :\n"
            for t in self.trads[0]:
                resultat += u'* [[%s]]\n' % t.title()

        return resultat

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
            if m is not None:
                return [m.group(2)]
            else:
                return [u'IMPOSSIBLE']

    def publier(self, souspage, liste, soustableau=0, simple=False):
        """
        Racourci pour publier une liste d'article sur une souspage du P:SAdQaW
        La paramètre « simple » permet d'obtenir un affichage simplifié sous forme d'une liste de liens.
        """
        retour = u'%s pages.\n\n' % str(len(liste[soustableau]))
        if simple:
            m = []
            for t in liste[soustableau]:
                m.append(t.title())
            retour += u'<noinclude>[[' + u']], [['.join(m) + u']].\n</noinclude>\n'
        else:
            noinclude = False
            for i, t in enumerate(liste[soustableau]):
                retour += u'{{%s}}' % t.title()
                if i == 11:
                    retour += u'<noinclude>'
                    noinclude = True
                retour += u'\n'
            if noinclude:
                retour += u'</noinclude>'
        pywikibot.Page(self.site, u'Projet:Suivi des articles de qualité des autres wikipédias/Traduction/' + souspage).put(retour, comment=self.resumeListing)
        
    def run(self):
        ##################################
        #####     Candidatures
        cats = []
        cats.append(pagegenerators.ReferringPageGenerator(pywikibot.Page(self.site, u"Modèle:Lien AdQ"), followRedirects=True, withTemplateInclusion=True))
        cats.append(pagegenerators.ReferringPageGenerator(pywikibot.Page(self.site, u"Modèle:Lien BA"), followRedirects=True, withTemplateInclusion=True))
        gen = pagegenerators.DuplicateFilterPageGenerator(pagegenerators.CombinedPageGenerator(cats))
        gen = pagegenerators.PreloadingGenerator(gen, step=125)
        for m in gen:
            if m.namespace() == 0 and m.title() not in self.ignor_list: # ... alors prendre la page de trad
                tradpage = BeBot.togglePageTrad(m)
                for t in self.traductions:
                   if t.title() == tradpage.title():
                        #Vérification de la correspondance des langues cibles
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
            for cat in tq.categories():
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
        self.publier(u'DemandeTraduction', self.trads, 1)
        self.publier(u'EnTraduction', self.trads, 2)
        self.publier(u'DemandeRelecture', self.trads, 3)
        self.publier(u'EnRelecture', self.trads, 4)

        # Cas de statut 5 (terminé)
        for pt in self.trads[5]:
            etat_label = 0
            for cat in BeBot.togglePageTrad(pt).categories():
                if cat.title() == u"Catégorie:Article de qualité" or cat.title() == u'Catégorie:Bon article' :
                    etat_label = 2
                    break
            self.term_et_label[etat_label].append(pt)

        self.publier(u'Labellisées', self.term_et_label, 2, True)
#        pywikibot.Page(self.site, u"Projet:Suivi des articles de qualité des autres wikipédias/Traduction/En attente d'être labellisées").put(self.genererListing(self.term_et_label[1]), comment=self.resumeListing)
        self.publier(u'Terminées sans label', self.term_et_label, 0, False)

def main():
    site = pywikibot.getSite()
    log = u'Utilisateur:BeBot/Traduction de qualité'

    tdq = TraductionDeQualite(site, log)
    tdq.run()
    
    pywikibot.Page(site, log).put(unicode(tdq), comment=tdq.resume, minorEdit=False)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
