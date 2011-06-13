#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
#import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class GraphiqueEvaluations:
    """ GraphiqueEvaluations
        Génère un graphique à barres (mensuelles) sur l'évolution des évaluations :
        nombre d'articles d'importance maximum ou élevée et total
    """
    def __init__(self, site):
        self.site = site
        self.date = datetime.date.today()
        self.resume = u'Mise à jour'

    def run(self):
        pass

def main():
    site = pywikibot.getSite()
    ge = GraphiqueEvaluation(site)
    ge.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
