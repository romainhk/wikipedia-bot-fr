#!/usr/bin/python
# -*- coding: utf-8  -*-
__version__ = 'RemplacerParametre 20100521'
import sys, re
#sys.path.append("~/pywikipedia")
from wikipedia import *
import pagegenerators, replace

class RemplacerParametre:
	summary = u'BeBot : Remplacement du paramètre «mémoire morte» par «espace disque» sur les [[Modèle:Configuration recommandée]]'

	def __init__(self, generator):
		self.generator = generator

	def run(self):
#		for page in self.generator:
#			wikipedia.output( ' *'+page.title(), newline=False )
#		wikipedia.output(' ##')
		remplacements = []
		exceptions = {}

		remplacements.append( (ur'\| *mémoire morte *=', '|espace disque   =') )
		replaceBot = replace.ReplaceRobot( self.generator, remplacements, exceptions,
    acceptall=False, editSummary=self.summary )
		replaceBot.run()

def main():
	site = wikipedia.getSite()
	refPage = wikipedia.Page(site, u'Modèle:Configuration recommandée')
#	refPage = wikipedia.Page(site, u'Modèle:Configuration minimum')
	gen = pagegenerators.ReferringPageGenerator(refPage)
	gen = pagegenerators.NamespaceFilterPageGenerator(gen, [0])
#	preloadingGen = pagegenerators.PreloadingGenerator(gen)
#	rp = RemplacerParam(preloadingGen)
	rp = RemplacerParametre(gen)
	rp.run()

if __name__ == "__main__":
	try:
		main()
	finally:
		wikipedia.stopme()
