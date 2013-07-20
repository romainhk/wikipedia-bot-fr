#!/usr/bin/python
# -*- coding: utf-8  -*-
import BeBot
import pywikibot

"""
    Supprime les sous-pages d'une page
"""

prefix="Traduction/*/Projet"
espace = 102 # Projet
#espace = 10 # Modèle
site = pywikibot.getSite()
ppg = site.allpages(prefix=prefix, namespace=espace, content=False)
for p in ppg:
    BeBot.delete(p, u'Restructuration du [[Projet:Traduction]]', debug=False)

