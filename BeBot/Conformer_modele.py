#!/usr/bin/python
# -*- coding: utf-8  -*-
import re
from textwrap import dedent
import BeBot, pywikibot
import pprint

class ConformerModele:
    """
    Ce script parcours les pages où est inclus un modèle, vérifie que la syntaxe est conforme
    puis effectue les corrections nécessaires.
    TODO:
    * annoncer les différences et proposer une correction
    * mode interactif
    * mode migration de paramètre (paramètre qui change de nom)
    * mettre l'exemple sur une sous-page de bebot
    * renvoyer modeletodic dans BeBot et maj des scripts liés
    """
    def __init__(self, site, exemple):
        self.site = site
        self.exemple = exemple
        self.dic = self.modeletodic(self.exemple)
        self.nom = self.dic[0]
        self.modele = pywikibot.Page(site, u'Modèle:'+self.nom)
        self.RE_modele = re.compile("(\{\{\s*%s.*?\}\})" % self.nom, re.IGNORECASE|re.MULTILINE|re.DOTALL)
        self.summary = u'Conformation du modèle {0}'.format(self.modele.title())

    #def modeletodic(self, nom, espace):
    def modeletodic(self, modele):
        """ Transforme un chaine "modèle" en tableau
        convention : r[0] est le nom du modèle
        NB: pyparsing doit fournir une méthode plus pratique que de dénombrer les ouvrants/fermants
        """
        RE_Modele = re.compile('\{\{(.+?)\}\}', re.IGNORECASE|re.LOCALE|re.DOTALL|re.MULTILINE)
        r = {}
        acc = '' # accumulation si un | ne correspond pas à la séparation d'un paramètre
        m = RE_Modele.search(modele)
        if m:
            chaine = m.group(1).replace('\n', '')
            pos = 0 # ordinal du paramètre
            for l in chaine.split("|"):
                if pos == 0:
                    r[0] = l.strip() # nom du modèle (premier paramètre positionnel)
                    pos = 1
                else:
                    l = acc+l
                    if l.count('[') - l.count(']') == 0: # = autant d'ouvrant que de fermant dans l
                        acc = ''
                        a = l.split("=")
                        b = a[0].strip()
                        if len(a) > 1:
                            r[b] = a[1].strip()
                        else: # paramètre positionnel
                            r[pos] = b
                            pos +=1
                    else:
                        # Il y a trop d'ouvrants -> on fusionne avec le suivant
                        acc = l+'|'
        else:
            pywikibot.warning(u"BeBot.modeletodic() ; il a été impossible de lire le modèle suivant\n%s" % modele)
        return r

    def comparer_params(self, modele):
        pass

    def run(self):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.dic)
        for r in self.modele.getReferences(total=2, content=True, onlyTemplateInclusion=True):
            m = self.RE_modele.search(r.text)
            if m:
                pp.pprint(self.modeletodic(m.group(1)))

def main():
    site = pywikibot.getSite()
    exemple = dedent(u"""
{{Infobox Logiciel
 | couleur boîte            = <!-- pour adapter la couleur de la boîte au logo -->
 | nom                      = 
 | logo                     = 
 | image                    = 
 | description              = 
 | développeur              = 
 | date de première version = 
 | dernière version         = 
 | date de dernière version = 
 | version avancée          = 
 | date de version avancée  = 
 | langage de programmation = 
 | environnement            = 
 | langue                   = 
 | type                     = 
 | licence                  = 
 | site web                 = 
}}"""[1:] )
    cm = ConformerModele(site, exemple)
    cm.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
