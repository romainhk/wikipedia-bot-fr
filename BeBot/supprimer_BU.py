#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, sys
import BeBot
import pywikibot

"""
    Supprime un modèle et ses appels d'inclusion
"""

site = pywikibot.getSite()
nom = "Utilisateur Traduction"
renom = re.compile('{{'+nom+'}}', re.IGNORECASE)
nom2 = "Traduction"
#renom2 = re.compile(u'(\{\{Bo(î|i)te\s*(utilisateur|babel)[^\}]*?)\|\s*'+nom2+u'(\s*|/\w{2})([^\}]*\}\})', re.IGNORECASE|re.UNICODE|re.MULTILINE)
renom2 = re.compile(u'(\{\{Bo(î|i)te\s*(utilisateur|babel)[^\}]*?)\|\s*'+nom2+u'\s*([^\}]*?\}\})', re.IGNORECASE|re.UNICODE|re.MULTILINE)
modele = pywikibot.Page(site, u'Modèle:'+nom)
if not modele.exists():
    pywikibot.error(u"La BU {nom} n'existe pas".format(nom=nom))
    sys.exit(2)

# Retrait des transclusions
for b in modele.getReferences(follow_redirects=False, onlyTemplateInclusion=True, content=True):
    #remp = r''
    remp = r'{{Utilisateur Projet/Traduction}}'
    a = renom.sub(remp, b.text)
    a = renom2.sub(r'\1|Projet/Traduction\4', a)
    b.text = a
    BeBot.save(b, commentaire=u'Retrait du modèle "{nom}" suite à la restructuration du [[Projet:Traduction]]'.format(nom=nom), debug=False)
BeBot.delete(modele, u'Retrait du modèle "{nom}" suite à la restructuration du [[Projet:Traduction]]'.format(nom=nom), debug=True)

