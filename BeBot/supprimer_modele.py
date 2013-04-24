#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, sys
import BeBot
import pywikibot

"""
    Supprime un modèle et ses appels d'inclusion
"""

site = pywikibot.getSite()
if len(sys.argv) != 2:
    pywikibot.warning(u"Nombre de paramètres incorrectes")
    sys.exit(1)
nom = sys.argv[1]
renom = re.compile('{{'+nom+'\|?[^}/]*?}}$?', re.IGNORECASE|re.MULTILINE)
modele = pywikibot.Page(site, u'Modèle:'+nom)
if not modele.exists():
    pywikibot.error(u"Le modèle {nom} n'existe pas".format(nom=nom))
    sys.exit(2)

# Retrait des transclusions
for b in modele.getReferences(follow_redirects=False, onlyTemplateInclusion=True, content=True):
    a = renom.sub(r'', b.text)
    b.text = a
    BeBot.save(b, commentaire=u'Retrait du modèle "{nom}"'.format(nom=nom), debug=False)
BeBot.delete(modele, u'Retrait du modèle "{nom}"'.format(nom=nom), debug=True)

"""
renom  = re.compile(u'\[\[Modèle:'+nom+'([^\}]*?)\]\]', re.UNICODE)
renom2 = re.compile('{{m\|'+nom+'}}')
for b in modele.linkedPages(content=True, total=9):
    a = renom.sub(r'{nom}'.format(nom=nom), b.text)
    a = renom2.sub(r'{nom}'.format(nom=nom), a)
    b.text = a
    BeBot.save(b, commentaire=u'Retrait du modèle {{{nom}}}'.format(nom=nom), debug=True)
"""

