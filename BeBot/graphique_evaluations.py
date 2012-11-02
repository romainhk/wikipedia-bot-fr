#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, math, sqlite3, sys
import pywikibot
import BeBot
from textwrap import dedent
locale.setlocale(locale.LC_ALL, '')

class GraphiqueEvaluations:
    """ Graphique Évaluations
        Génère un graphique à barres sur l'évolution du nombre des évaluations :
        nombre d'articles d'importance maximum ou élevée et total
    """
    def __init__(self, site, bddsqlite):
        self.site = site
        self.date = datetime.date.today()
        self.resume = u'Mise à jour mensuelle du graphique des évaluations'
        #DB
        try:
            self.conn = sqlite3.connect(bddsqlite)
        except:
            pywikibot.output("Impossible d'ouvrir la base sqlite {0}".format(bddsqlite))
            exit(2)
        self.conn.row_factory = sqlite3.Row
        self.nom_base = u'graphique_evaluations'
    def __del__(self):
        self.conn.close()

    def BotSectionEdit(self, match):
        return u'%s\n%s\n%s' % (BeBot.BeginBotSection, self.msg, BeBot.EndBotSection)

    def trouver_stat_mens(self, ressource, mois, annee):
        # Retrouve l'enregistrement d'un mois en particulier
        for i in range(0, len(ressource)):
            d = ressource[i]['date'].split('-')
            month = int(d[1])
            year  = int(d[0])
            if year == annee and month == mois:
                return ressource[i]
        return [ datetime.date(day=1,month=mois,year=annee),0,0,0,0,0,0 ]

    def run(self):
        # Dénombrement
        l = {}
        cat = pywikibot.Category(self.site, u"Catégorie:Article par importance")
        for c in cat.subcategories(recurse=False):
            nom = c.title().split(' ')[-1]
            l[nom] = 0
            for d in c.subcategories():
                pages = self.site.categoryinfo(d)['pages']
                l[nom] += pages
        total = 0
        for a in l.values():
            total += a
        # Sauvegarde
        curseur = self.conn.cursor()
        req = u'INSERT INTO %s' % self.nom_base \
            + u'(date, maximum, élevée, moyenne, faible, inconnue, total) ' \
            + u'VALUES ("%s", %d, %d, %d, %d, %d, %d)' \
            % (self.date.strftime("%Y-%m-%d"), l['maximum'], l[u'élevée'], \
                    l['moyenne'], l['faible'], l['inconnue'], total)
        try:
            curseur.execute(req)
        except:
            pywikibot.error(u"INSERT error pendant la requête :\n%s" % (req))
        self.conn.commit()
        
        # Dessin
        limite = 20 #nombre max de colonnes
        largeur = 600 #largeur du graphique
        maxi = 0 #valeur max en hauteur
        nb_bande = 6
        res = BeBot.charger_bdd(self.conn, self.nom_base, lim=limite, ordre='"date" ASC')
        nb_enregistrement = len(res)
        if nb_enregistrement > nb_bande:
            # Tri des résultats sur les 6 derniers mois
            res2 = []
            ajd = datetime.date.today()
            month = ajd.month
            year = ajd.year
            res2.append(self.trouver_stat_mens(res, month, year))
            for d in range(1,nb_bande):
                month = month-1
                if month <= 0:
                    year = year-1
                    month = 12
                res2.append(self.trouver_stat_mens(res, month, year))
            res2.reverse()
            res = res2
            nb_enregistrement = len(res)

        width = math.ceil(largeur/nb_enregistrement) #largeur d'une bande
        for r in range(0, nb_enregistrement):
            if maxi < res[r]['total']:
                maxi = res[r]['total'] # point le plus haut
        #Majoration du maximum
        t = maxi
        rang = 0
        while t > 1:
            t = math.ceil(t/10)
            rang +=1
        graduation = pow(10, rang-2)
        maxi = maxi + math.floor(graduation/2)
        maxi = int(math.floor(maxi*pow(10,3-rang))*pow(10,rang-3)) # 3 premiers chiffre significatifs
        self.msg = dedent(u"""
<timeline>
Colors=
  id:lightgrey value:gray(0.9)
  id:darkgrey  value:gray(0.7)
  id:sfondo value:rgb(1,1,1)
  id:barra value:rgb(0.7,0.9,0.7) legend:Total
  id:rouge value:rgb(1,0,0) legend:Max+Élevée
  id:gris value:rgb(0.95,0.95,0.95)

ImageSize  = width:%d height:300
Define $width = %d
PlotArea   = left:60 bottom:20 top:20 right:10
DateFormat = x.y
Period     = from:0 till:%d
TimeAxis   = orientation:vertical
AlignBars  = justify
ScaleMajor = gridcolor:darkgrey increment:%d start:0
ScaleMinor = gridcolor:lightgrey increment:%d start:0
BackgroundColors = canvas:sfondo

Legend = left:70 top:295"""[1:] % (largeur, width, maxi, graduation, graduation/2) )
        #Nom des bars
        self.msg += '\nBarData=\n'
        for r in range(0, nb_enregistrement):
            p = ''
            if r % 2 == 1:
                spl = res[r]['date'].split('-')
                p = spl[1] + '/' + spl[0][2:]
            self.msg += '  bar:%d text:%s\n' % (r+1, p)
        #Valeurs : total
        self.msg += '\nPlotData=\n  color:barra width:$width align:left\n\n'
        for r in range(0, nb_enregistrement):
            p = res[r]['total']
            self.msg += '  bar:%d from:0 till: %d\n' % (r+1, p)
        #Valeurs : importants
        self.msg += '\nPlotData=\n  color:rouge width:$width align:left\n\n'
        for r in range(0, nb_enregistrement):
            p = res[r]['maximum'] + res[r][2] # 2 = élevée
            self.msg += '  bar:%d from:0 till: %d\n' % (r+1, p)
        #Labels
        self.msg += '\nPlotData=\n'
        for r in range(0, nb_enregistrement):
            if r % 2 == 1:
                p = res[r]['total']
                self.msg += '  bar:%d at: %d fontsize:S text: %d shift:(-10,5)\n' % (r+1, p, p)
                q = res[r]['maximum'] + res[r][2]
                self.msg += '  bar:%d at: %d fontsize:S text: %d shift:(-10,5)\n' % (r+1, q, q)
        self.msg += '</timeline>'

        # Publication
        page = pywikibot.Page(self.site, u'Projet:Wikipédia_1.0/Évolution')
        page.text = BeBot.ER_BotSection.sub(self.BotSectionEdit, page.text)
        BeBot.save(page, commentaire=self.resume)

def main():
    site = pywikibot.getSite()
    if len(sys.argv) == 2:
        bddsqlite = sys.argv[1]
        ge = GraphiqueEvaluations(site, bddsqlite)
        ge.run()
    else:
        pywikibot.output("Erreur de paramètres : il faut spécifier la base sqlite")
        exit(1)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
