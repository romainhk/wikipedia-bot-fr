#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, MySQLdb, sqlite3
#import BeBot
#from MySQLdb.constants import ER
import pywikibot
from pywikibot import catlib
from textwrap import dedent
locale.setlocale(locale.LC_ALL, '')

class GraphiqueEvaluations:
    """ GraphiqueEvaluations
        Génère un graphique à barres (mensuelles) sur l'évolution des évaluations :
        nombre d'articles d'importance maximum ou élevée et total
    """
    def __init__(self, site):
        self.site = site
        self.date = datetime.date.today()
        self.resume = u'Mise à jour du graphique des évaluations'
        """
        #DB
        self.db = MySQLdb.connect(db="u_romainhk_transient", \
                                read_default_file="/home/romainhk/.my.cnf", \
                                use_unicode=True, charset='utf8')
        self.nom_base = u''
        """

    def run(self):
        # Dénombrement
        l = {}
        for c in catlib.Category(self.site, u"Catégorie:Article par importance").subcategories():
            nom = c.title().split(' ')[-1]
            l[nom] = 0
            for d in c.subcategories():
                pages = self.site.categoryinfo(d)['pages']
                l[nom] += pages
        pywikibot.output(l)
        pywikibot.output('Max + Eleve : %d' % (l[u'élevée'] + l[u'maximum']))
        b = 0
        for a in l.values():
            b += a
        pywikibot.output('Total : %d' % b)

        # Dessin
        msg = dedent("""
<timeline>
Colors=
  id:lightgrey value:gray(0.9)
  id:darkgrey  value:gray(0.7)
  id:sfondo value:rgb(1,1,1)
  id:barra value:rgb(0.7,0.9,0.7) legend:Total
  id:rouge value:rgb(1,0,0) legend:Max+Élevée
  id:gris value:rgb(0.95,0.95,0.95)

ImageSize  = width:600 height:300
PlotArea   = left:50 bottom:50 top:30 right:30
DateFormat = x.y
Period     = from:0 till:15000
TimeAxis   = orientation:vertical
AlignBars  = justify
ScaleMajor = gridcolor:darkgrey increment:1000 start:0
ScaleMinor = gridcolor:lightgrey increment:500 start:0
BackgroundColors = canvas:sfondo

Legend = left:60 top:270

BarData="""[1:] )
        print msg

def main():
    site = pywikibot.getSite()
    ge = GraphiqueEvaluations(site)
    ge.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
