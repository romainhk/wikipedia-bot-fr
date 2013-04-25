#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, sys
import BeBot
import pywikibot

"""
    Supprime un modèle et ses appels d'inclusion
"""

site = pywikibot.getSite()
nom = "Utilisateur Relecteur"
renom = re.compile('{{'+nom+'}}', re.IGNORECASE)
nom2 = "Relecteur"
renom2 = re.compile('{{Boîte utilisateur\|[^\}]*?'+nom2+'[^\}]*}}', re.IGNORECASE)
modele = pywikibot.Page(site, u'Modèle:'+nom)
if not modele.exists():
    pywikibot.error(u"Le modèle {nom} n'existe pas".format(nom=nom))
    sys.exit(2)

# Retrait des transclusions
#for b in modele.getReferences(follow_redirects=False, onlyTemplateInclusion=True, content=True, total=8):
for b in modele.getReferences(follow_redirects=False, onlyTemplateInclusion=True, content=True):
    remp = r''
    #remp = r'{{Utilisateur Projet/Traduction}}'
    a = renom.sub(remp, b.text)
    a = renom2.sub(remp, a)
    b.text = a
    BeBot.save(b, commentaire=u'Retrait du modèle "{nom}"'.format(nom=nom), debug=False)
BeBot.delete(modele, u'Retrait du modèle "{nom}"'.format(nom=nom), debug=True)

