#!/usr/bin/python
# -*- coding: utf-8  -*-
import re
from operator import itemgetter
import BeBot
import pywikibot

site = pywikibot.getSite()
classement = {} # classement par nb de modifs
last = {} # date de dernière modif
peuactifs = {} # bots peu actifs

bots = pywikibot.Category(site, u'Catégorie:Wikipédia:Bot/Autorisé')
for b in bots.articles(total=5):
    nb, derniere = BeBot.userdailycontribs(site, b.title(), days=365)
    nom = b.title(withNamespace=False)
    if nb > 10:
        classement[nom] = nb
        last[nom] = derniere
    else:
        peuactifs[nom] = nb

classement = sorted(classement.items(), key=itemgetter(1), reverse=True)

# Affichage des résultats
for nom, nb in classement:
    pywikibot.output(u'%s : %i ; %s' % (nom, nb, last[nom]))

pywikibot.output(peuactifs)
