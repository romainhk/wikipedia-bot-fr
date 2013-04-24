#!/usr/bin/python
# -*- coding: utf-8  -*-
import BeBot
import pywikibot

"""
    Supprime les sous-pages d'une page
"""

prefix="Traduction/*/Lang"
espace = 102 # Projet
site = pywikibot.getSite()
ppg = site.allpages(prefix=prefix, namespace=espace, total=10, content=False) 
for p in ppg:
    BeBot.delete(p, u'Restructuration du [[Projet:Traduction]]', debug=True)

