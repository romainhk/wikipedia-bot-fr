#!/usr/bin/python
# -*- coding: utf-8  -*-
__version__ = 'ContenuDeQualité 20100609'
import re, datetime, MySQLdb
from MySQLdb.constants import ER
from wikipedia import *
import pagegenerators, catlib

def moistoint(mois):
    " Convertit une chaîne de caractètre correspondant à un mois, en un entier i (1≤i≤12). "
    mois = mois.lower()
    if mois == 'janvier':     return 1
    elif mois == u'février':  return 2
    elif mois == 'mars':      return 3
    elif mois == 'avril':     return 4
    elif mois == 'mai':       return 5
    elif mois == 'juin':      return 6
    elif mois == 'juillet':   return 7
    elif mois == u'août':     return 8
    elif mois == 'septembre':  return 9
    elif mois == 'octobre':    return 10
    elif mois == 'novembre':   return 11
    elif mois == u'décembre':  return 12
    else:
        wikipedia.output(u'Mois « %s » non reconnu' % mois)
    return 0

class PasDeDate(Exception):
    """ Impossible de trouver de date valide dans la page
    """
    def __init__(self, page, contenu):
        self.page = page
        self.contenu = contenu
    def __str__(self):
        return repr(self.page)

class ContenuDeQualite:
    """ Contenu de Qualité
        Tri et sauvegarde les AdQ/BA existants par date.
		(Persistance du nom de l'article, de son espace de nom, de la date de labellisation et de son label.)

        TODO : les intentions de proposition au label.
		TODO : comparer la cat AdQ/BA avec la cat "Maintenance des "
    """
    def __init__(self, site):
        self.resume = u'Repérage du contenu de qualité au ' + datetime.date.today().strftime("%Y-%m-%d")
        self.site = site
        self.qualite = []       # Article promus actuellements
        self.dechu = []         # Articles déchus
        self.db = MySQLdb.connect(db="u_romainhk", read_default_file="/home/romainhk/.my.cnf")

    def __del__(self):
        self.db.close()

    def __str__(self):
        """ Log à publier
        """
        resultat = u"''Contenu de Qualité''\n"
        resultat += str(self.qualite)
        resultat += u"\n''Articles déchus de puis la dernière sauvegarde''\n"
        resultat += str(self.dechu)
        return resultat

    def sauvegarder(self):
        """ Sauvegarder dans une base de données
        """
        c = self.db.cursor()
        for q in self.qualite:
            donnees = u'"' + q[0] + u'", ' + str(q[1]) + u', "' \
                    + q[2].strftime("%Y-%m-%d") + u'", "' + q[3] + u'"'
            req = u"INSERT INTO contenu_de_qualite(page, espacedenom, date, label) VALUES ("+ donnees +")"
            try:
                c.execute(req)
            except MySQLdb.Error, e:
                if e.args[0] == ER.DUP_ENTRY:
                    req = u"UPDATE contenu_de_qualite SET espacedenom=" + str(q[1]) \
                        + ', date="' + q[2].strftime("%Y-%m-%d") + '", label="' + q[3] \
                        + '" WHERE page="' + q[0] + '"'
                    c.execute(req)
                else:
                    print "Erreur %d: %s" % (e.args[0], e.args[1])
                continue

    def charger(self):
        """ Charger la liste de labels depuis une base de données
        """
        c = self.db.cursor()
        req = "SELECT * FROM contenu_de_qualite"
        c.execute(req)
        return c.fetchall()

    def date_label(self, titre):
        """ Donne la date de labellisation d'un article
        """
        try:
            page = wikipedia.Page(self.site, titre).get()
        except pywikibot.exceptions.NoPage:
            raise PasDeDate(titre, u'')
        dateRE = re.compile("\| *date *= *(\d{1,2}) (\w{3,9}) (\d{2,4})", re.LOCALE)
        #TODO : peut mieux faire
        d = dateRE.search(page)
        if d:
            return datetime.date(int(d.group(3)), moistoint(d.group(2)), int(d.group(1)))
        raise PasDeDate(titre, page)

    def run(self):
        connus = self.charger()
        cat_qualite = [ u'Article de qualité',  u'Bon article']
        #cat_qualite = [ u'Article de qualité' ]
        connaitdeja = []
        for cat in cat_qualite:
            c = catlib.Category(self.site, cat)
            cpg = pagegenerators.CategorizedPageGenerator(c, recurse=False)
            #Comparer avec le contenu de la bdd
            for p in cpg:
                prendre = True
                for con in connus:
                    if p.title() == unicode(con[0].decode('latin1')):
                        connaitdeja.append(p.title())
                        prendre = False
                        break
                if prendre:
                    #Prise des dates
                    try:
                        date = self.date_label(p.title())
                    except PasDeDate as pdd:
                        wikipedia.output(u'## Exception : Pas de date pour ' + pdd.page)
                        continue
                    self.qualite.append( [ p.title(), p.namespace(), date, cat ] )
        print u'Connait déjà : ' + ', '.join(connaitdeja)

        c = catlib.Category(self.site, u'Ancien article de qualité')
        cpg = pagegenerators.CategorizedPageGenerator(c, recurse=False)
        for p in cpg:
            for con in connus:
                if p.toggleTalkPage.title() == unicode(con[0].decode('latin1')):
                    self.dechu.append( p.title() )
        """
            for p in cpg:
                try:
                    date = self.date_label(p.title())
                except PasDeDate as pdd:
                    wikipedia.output(u'Exception : Pas de date pour ' + pdd.page)
                    continue
                self.qualite.append( [ p.title(), p.namespace(), date, cat ] )
        self.sauvegarder()
            """

def main():
    site = wikipedia.getSite()
    cdq = ContenuDeQualite(site)
    cdq.run()

    wikipedia.output(unicode(cdq))

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
