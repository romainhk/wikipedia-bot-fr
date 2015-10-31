#!/usr/bin/python
# -*- coding: utf-8  -*-
import re
from textwrap import dedent
from pyparsing import *
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

    ply ? nltk ? pyparsing ?
    http://nedbatchelder.com/text/python-parsers.html

    GRAMMAIRE
<modele> ::= "{{" <nom> "|" <elem> ... "}}"
<nom> ::= [^|{}]
<val> ::= [^|=]
<param> ::= [^=|{}]
<elem> ::= ( <val> | <param>"="<val> | <elem> )
    """
    def __init__(self, site, exemple):
        self.site = site
        self.exemple = exemple
        self.dic = self.modeletodic(self.exemple)
        #self.nom = self.dic[0]
        self.nom = 'Infobox Logiciel'
        self.modele = pywikibot.Page(site, u'Modèle:'+self.nom)
        self.RE_modele = re.compile("(\{\{\s*%s.*\}\})" % self.nom, re.IGNORECASE|re.MULTILINE|re.DOTALL)
        self.summary = u'Conformation du modèle {0}'.format(self.modele.title())

    def modeletodic(self, espace, nom=''):
        #elem = nestedExpr(opener="{{", closer="}}", ignoreExpr=Word('|= '))
        elem = nestedExpr(opener="{{", closer="}}", ignoreExpr=Word('|'))
        print( elem.parseString(espace)[0] )
        dictionnaire = {}
        index = 0
        acc = 'param'
        param = u''
        val = u''
        for a in elem.parseString(espace)[0]:
            if type(a) is str:
                b = a.strip(' ')
                if b == u'|':
                    # nouveau paramètre
                    if acc == 'param': # paramètre anonyme
                        dictionnaire[index] = val
                        index += 1
                    else:
                        dictionnaire[param] = val
                        acc = 'param'
                    param = u''
                    val = u''
                elif b == u'=':
                    # nouvelle valeur
                    acc = 'valeur'
                else:
                    # par défaut : accumulation
                    if acc == 'param':
                        param += u' '+b
                    elif acc == 'valeur':
                        val += u' '+b
        #print(dictionnaire)
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(espace[598:])
        #contenu = Word(printables + alphas8bit + ' \n' - '}')
        #modele = Literal("{{") + contenu + Literal("}}")
        #modele.setDebug()
        #print(modele.parseString(espace))
    """
    def modeletodic(self, espace, nom=''):
    #def modeletodic(self, espace):
        " Transforme un chaine "modèle" en tableau
        convention : r[0] est le nom du modèle
        NB: pyparsing doit fournir une méthode plus pratique que de dénombrer les ouvrants/fermants
        "
        REmodele = re.compile("(\{\{\s*%s.*\}\})" % nom, re.IGNORECASE|re.MULTILINE|re.DOTALL)
        m = REmodele.search(espace)
        res = {}
        acc = '' # accumulateur
        if not m:
            pywikibot.error(u"modeletodic() : il a été impossible de délimiter le modèle '{0}'".format(nom))
            return res
        else:
            for a in m.group(1).split('}'):
                acc = acc+a+'}'
                if acc.count('{') - acc.count('}') == 0: # = autant d'ouvrant que de fermant
                    # On a trouvé l'expression du modèle 
                    break
            # Découpage des paramètres
            chaine = acc.replace('\n', '').lstrip('{').rstrip('}')
            pos = 0 # ordinal du paramètre
            for l in chaine.split("|"):
                if pos == 0:
                    res[0] = l.strip() # nom du modèle (premier paramètre positionnel)
                    pos = 1
                else:
                    l = acc+l
                    if l.count('[') - l.count(']') == 0: # = autant d'ouvrant que de fermant dans l
                        acc = ''
                        a = l.split("=")
                        b = a[0].strip()
                        if len(a) > 1:
                            res[b] = a[1].strip()
                        else: # paramètre positionnel
                            res[pos] = b
                            pos +=1
                    else:
                        # Il y a trop d'ouvrants -> on fusionne avec le suivant
                        acc = l+'|'
        return res
    """
    def comparer_params(self, modele):
        pass

    def run(self):
        pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(self.dic)
        for r in self.modele.getReferences(total=2, content=True, onlyTemplateInclusion=True):
            m = self.RE_modele.search(r.text)
            if m:
                pass
                #self.modeletodic(m.group(1), self.nom)
                #pp.pprint(self.modeletodic(m.group(1), self.nom))

def main():
    site = pywikibot.getSite()
    exemple = dedent(u"""
{{Infobox Logiciel
 | couleur boîte            = <!-- pour adapter la couleur de la boîte au logo -->
 | nom                      = 
|logo=blatagueule
 | image                    =[[File:titi.jpg|thumb|30px|Et le gros]]|description=tata 
 | développeur              = 
 | date de première version = 
 | dernière version         = 
 | date de dernière version = 
 | version avancée          = 
 | date de version avancée  = 
 | langage de programmation = 
 | environnement            = 
 | langue                   = {{lang|en|toto}}
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
