#!/usr/bin/python
# -*- coding: utf-8  -*-
import re
from operator import itemgetter
import BeBot
import pywikibot

"""
    Analyse l'activité des bots
"""

site = pywikibot.getSite()
p = pywikibot.Page(site, u'Utilisateur:BeBot/Activité des bots') # Page des résultats
classement = {} # classement par nb de modifs
last = {} # date de dernière modif
lim_jours = 182 # nombre de jours à prendre en compte
peuactifs = {} # bots peu actifs
lim_peu = 10 # limite de modifications pour les bots peu actifs

bots = pywikibot.Category(site, u'Catégorie:Wikipédia:Bot/Autorisé')
for b in bots.articles():
    nb, derniere = BeBot.userdailycontribs(site, b.title(), days=lim_jours)
    nom = b.title(withNamespace=False)
    if nb > lim_peu:
        classement[nom] = nb
        last[nom] = derniere
    else:
        peuactifs[nom] = nb

classement = sorted(classement.items(), key=itemgetter(1), reverse=True)

# Affichage des résultats
t = u'{|class=\"wikitable sortable\"\n!Nom!!Contribs ces %i derniers jours!!Date de dernière activitée' % lim_jours
for nom, nb in classement:
    t += u'\n|-\n|{{u|%s}}||%d||%s' % (nom, nb, last[nom])
t += u'\n|}'

t += u'\n== Les bots peu actifs (moins de %d modifs) ==\n' % lim_peu
t += u'{{début de colonnes|nombre=3}}\n'
for pa in sorted(peuactifs.keys()):
    t += u'\n* {{u|%s}}' % pa
t += u'{{fin de colonnes}}\n'

p.text = t
BeBot.save(p, commentaire='Recalculationnement du classement', debug=False)
