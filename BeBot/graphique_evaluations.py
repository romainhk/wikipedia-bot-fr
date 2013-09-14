#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, dateutil, locale, math, sqlite3, sys
from dateutil.relativedelta import relativedelta
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
        self.groupe = re.compile('(.*\d)(\d{3}.*)', re.IGNORECASE|re.LOCALE)
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

    def nombreverschaine(self, nombre):
        """ Convertit un grand nombre en une chaine "par paquets"
            ex: 1489321 => 1 489 321
        """
        s = unicode(nombre)
        m = self.groupe.search(s)
        while m:
            s = m.group(1) + u" " + m.group(2)
            m = self.groupe.search(s)
        return s

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
        except sqlite3.Error as e:
            pywikibot.error(u"Erreur lors de l'INSERT :\n%s" % (e.args[0]))
        self.conn.commit()
        
        # Dessin
        largeur = 600 #largeur du graphique
        maxi = 0 #valeur max en hauteur
        nb_bande = 6 #nombre max de colonnes
        #on suppose ici un enregistrement par mois
        res = BeBot.charger_bdd(self.conn, self.nom_base, lim=nb_bande, ordre='"date" DESC')
        width = math.ceil(largeur/nb_bande) #largeur d'une bande

        # Liste des mois à traiter
        mois = []
        for j in range(0, nb_bande):
            d = self.date + relativedelta(months=-j)
            mois.append(d.strftime(u"%Y-%m"))
        # Récupération et tri des valeurs
        vals = []
        ri = 0 # ressource index : index sur les enregistrements utilisés
        for m in mois:
            val = {}
            if m != res[ri]['date'][0:7]:
                for k in res[ri].keys():
                    val[k] = 0
                val['date'] = m + u"-02"
            else:
                for k in res[ri].keys():
                    val[k] = res[ri][k]
                if maxi < val['total']:
                    maxi = val['total'] # point le plus haut
                ri += 1
            vals.append(val)
        vals.reverse()
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
        for r in range(0, nb_bande):
            p = ''
            if r % 2 == 1:
                spl = vals[r]['date'].split('-')
                p = spl[1] + '/' + spl[0][2:]
            self.msg += '  bar:%d text:%s\n' % (r+1, p)
        #Valeurs : total
        self.msg += '\nPlotData=\n  color:barra width:$width align:left\n\n'
        for r in range(0, nb_bande):
            p = vals[r]['total']
            self.msg += '  bar:%d from:0 till: %d\n' % (r+1, p)
        #Valeurs : importants
        self.msg += '\nPlotData=\n  color:rouge width:$width align:left\n\n'
        for r in range(0, nb_bande):
            p = vals[r]['maximum'] + vals[r]['\xc3\xa9lev\xc3\xa9e'] # = élevée
            self.msg += '  bar:%d from:0 till: %d\n' % (r+1, p)
        #Labels
        self.msg += '\nPlotData=\n'
        for r in range(0, nb_bande):
            if r % 2 == 1:
                p = vals[r]['total']
                s = self.nombreverschaine(p)
                self.msg += '  bar:%d at: %d fontsize:S text:"%s" shift:(-20,5)\n' % (r+1, p, s)
                q = vals[r]['maximum'] + vals[r]['\xc3\xa9lev\xc3\xa9e']
                s = self.nombreverschaine(q)
                self.msg += '  bar:%d at: %d fontsize:S text:"%s" shift:(-20,5)\n' % (r+1, q, s)
        self.msg += '</timeline>'

        # Publication
        page = pywikibot.Page(self.site, u'Projet:Évaluation/Évolution')
        page.text = BeBot.ER_BotSection.sub(self.BotSectionEdit, page.text)
        BeBot.save(page, commentaire=self.resume, debug=False)

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
