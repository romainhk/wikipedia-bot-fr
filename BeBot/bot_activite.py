#!/usr/bin/python
# -*- coding: utf-8  -*-
import re
import datetime
from operator import itemgetter
import BeBot
import pywikibot

"""
    Analyse l'activité des bots
    TODO:
        * total de bot actif / total
        * contribution moyenne
"""

site = pywikibot.Site()
p = pywikibot.Page(site, 'Utilisateur:BeBot/Activité des bots') # Page des résultats
classement = {} # classement par nb de modifs
last = {} # date de dernière modif
lim_jours = 182 # nombre de jours à prendre en compte
peuactifs = {} # bots peu actifs
lim_peu = 10 # limite de modifications pour les bots peu actifs

bots = pywikibot.Category(site, 'Catégorie:Wikipédia:Bot/Autorisé')
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
t = '{{|class=\"wikitable sortable\"\n|+calculé le {date}\n!Nom!!Contribs ces {x} derniers jours!!Timestamp de dernière modif'.format(date=datetime.date.today().isoformat(),x=lim_jours)
for nom, nb in classement:
    t += '\n|-\n|{{u|%s}}||%d||%s' % (nom, nb, last[nom])
t += '\n|}'

t += '\n== Les bots peu actifs (moins de %d modifs) ==\n' % lim_peu
t += '{{début de colonnes|nombre=3}}\n'
for pa in sorted(peuactifs.keys()):
    t += '\n* {{u|%s}}' % pa
t += '{{fin de colonnes}}\n'

p.text = t
BeBot.save(p, commentaire='Recalculationnement du classement', debug=False)
