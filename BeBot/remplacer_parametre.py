#!/usr/bin/python
# -*- coding: utf-8  -*-
__version__ = 'RemplacerParametre 20100521'
import sys, re
from wikipedia import *
import pagegenerators, replace

class RemplacerParametre:
    summary = u'Remplacement du paramètre «mémoire morte» par «espace disque» sur les [[' + modele + u']]'

    def __init__(self, generator, modele):
        self.generator = generator
        self.modele = modele

    def run(self):
        remplacements = []
        exceptions = {}

        remplacements.append( (ur'\| *mémoire morte *=', '|espace disque   =') )
        replaceBot = replace.ReplaceRobot( self.generator, remplacements, exceptions,
    acceptall=False, editSummary=self.summary )
        replaceBot.run()

def main():
    site = wikipedia.getSite()
    modele = u'Modèle:Configuration recommandée'
#    modele = u'Modèle:Configuration minimum'
    refPage = wikipedia.Page(site, modele)
    gen = pagegenerators.ReferringPageGenerator(refPage)
    gen = pagegenerators.NamespaceFilterPageGenerator(gen, [0])
    rp = RemplacerParametre(gen)
    rp.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
