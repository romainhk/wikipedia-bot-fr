#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, sys
import BeBot
import pywikibot

"""
    Supprime une catégorie et ses sous catégories
"""

site = pywikibot.getSite()
if len(sys.argv) != 2:
    pywikibot.warning(u"Nombre de paramètres incorrectes")
    sys.exit(1)
nom = sys.argv[1]
cat = pywikibot.Category(site, nom)
if not cat.exists():
    pywikibot.error(u"La catégorie {nom} n'existe pas".format(nom=nom))
    sys.exit(2)

comment = u'Suppression de la catégorie "{nom}"'
debug=True

# Retrait des transclusions
def suppr_cat(cat):
    for b in cat.subcategories():
        suppr_cat(b)
    BeBot.delete(cat, comment.format(nom=cat.title()), debug=debug)

suppr_cat(cat)

