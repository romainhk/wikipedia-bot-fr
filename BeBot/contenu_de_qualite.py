#!/usr/bin/python
# -*- coding: utf-8  -*-
__version__ = 'ContenuDeQualité 20100623'
import re, datetime, MySQLdb
from MySQLdb.constants import ER
from wikipedia import *
import pagegenerators, catlib, add_text

def moistoint(mois):
    " Convertit une chaîne de caractètre correspondant à un mois, en un entier i (1≤i≤12). "
    mois = mois.lower()
    if mois == u'janvier':     return 1
    elif mois == u'février':   return 2
    elif mois == u'mars':      return 3
    elif mois == u'avril':     return 4
    elif mois == u'mai':       return 5
    elif mois == u'juin':      return 6
    elif mois == u'juillet':   return 7
    elif mois == u'août':      return 8
    elif mois == u'septembre':  return 9
    elif mois == u'octobre':    return 10
    elif mois == u'novembre':   return 11
    elif mois == u'décembre':   return 12
    else:
        wikipedia.output(u'Mois « %s » non reconnu' % mois)
    return 0

class PasDeDate(Exception):
    """
    Impossible de trouver de date valide dans la page
    """
    def __init__(self, page):
        self.page = page
    def __str__(self):
        return repr(self.page)

class ContenuDeQualite:
    """ Contenu de Qualité
        Tri et sauvegarde les AdQ/BA existants par date.
        (Persistance du nom de l'article, de son espace de nom, de la date de labellisation et de son label.)

        TODO : les intentions de proposition au label.
        TODO : comparer la cat AdQ/BA avec la cat "Maintenance des "
        TODO : les portails/themes de qualité
        TODO : différencer ajout (qualite) et maj (connaitdeja)
    """
    def __init__(self, site, log):
        self.resume = u'Repérage du contenu de qualité au ' + datetime.date.today().strftime("%Y-%m-%d")
        self.site = site
        self.log = log      # Nom de la page de log
        self.page_resultat = wikipedia.Page(site, log)

        self.qualite = []       # Nouveaux articles promus
        self.connaitdeja = []   # Articles déjà listés
        self.pasdedate = []     # Articles de qualité dont la date est inconnue
        self.dechu = []         # Articles déchus
        self.db = MySQLdb.connect(db="u_romainhk", read_default_file="/home/romainhk/.my.cnf", use_unicode=True, charset='utf8')

        rev = self.page_resultat.getVersionHistory(revCount=1)[0][1]
        self.precedent = rev[:10]    # Date de la dernière sauvegarde

    def __del__(self):
        self.db.close()

    def __str__(self):
        """
        Log à publier
        """
        resultat =  u"<center style='font-size:larger;'>'''Log « Contenu de qualité » du " \
                + datetime.date.today().strftime("%A %d %B %Y") + u"'''</center>\n\n"
        resultat += str(len(self.qualite)) + u" nouvels articles labellisés trouvés (plus " \
                + str(len(self.pasdedate)) + u" sans dates). "
        resultat += str(len(self.dechu)) + u" ont été déchus depuis la dernières exécussion.\n"
        resultat += u"\nTotal : " + str(len(self.qualite) + len(self.connaitdeja) + len(self.pasdedate)) + u" articles labellisés.\n"
        resultat += u"\n== Nouveau contenu de qualité ==\n"
        resultat += self.lister_article(self.qualite)
        resultat += u"\n=== Articles sans date de labellisation ===\n"
        resultat += self.lister_article(self.pasdedate)
        resultat += u"\n== Articles déchus depuis la dernière sauvegarde "
        if self.precedent:
            resultat += u"(le " + self.precedent + u" ?) "
        resultat += u"==\n"
        resultat += self.lister_article(self.dechu)
        return resultat

    def lister_article(self, table):
        """ __str__
        Génère une wiki-liste à partir d'un tableau d'articles
        """
        if len(table) > 0:
            r = []
            if type(table[0]) == type(u""):
                for p in table:
                    r.append(u"[[" + unicode(p) + u"]]")
            elif type(table[0]) == type([]):
                for p in table:
                    r.append(u"[[" + unicode(p[0]) + u"]] (" + unicode(p[3]) \
                            + u' depuis le ' + unicode(p[2]) + u')')
            return u'* ' + '\n* '.join(r) + u'\n'
        return u''

    def sauvegarder(self):
        """
        Sauvegarder dans une base de données
        """
        curseur = self.db.cursor()
        for q in self.qualite:
            donnees = u'"' + q[0] + u'", ' + str(q[1]) + u', "' \
                    + q[2].strftime("%Y-%m-%d") + u'", "' + q[3] + u'"'
            req = u"INSERT INTO contenu_de_qualite(page, espacedenom, date, label) VALUES ("+ donnees + u")"
            try:
                curseur.execute(req)
            except MySQLdb.Error, e:
                if e.args[0] == ER.DUP_ENTRY:
                    req = u"UPDATE contenu_de_qualite SET espacedenom=" + str(q[1]) \
                        + ', date="' + q[2].strftime("%Y-%m-%d") + '", label="' + q[3] \
                        + '" WHERE page="' + q[0] + '"'
                    curseur.execute(req)
                else:
                    print "Erreur %d: %s" % (e.args[0], e.args[1])
                continue

        for d in self.dechu:
            req = u"DELETE FROM contenu_de_qualite WHERE page='" + unicode(d) + u"'"
            try:
                curseur.execute(req)
            except:
                wikipedia.output(u"# DELETE échoué sur " + unicode(d))

    def charger(self):
        """
        Charger la liste des articles dont le label est connu depuis une base de données
        """
        curseur = self.db.cursor()
        req = "SELECT * FROM contenu_de_qualite"
        curseur.execute(req)
        return curseur.fetchall()

    def date_labellisation(self, titre):
        """
        Donne la date de labellisation d'un article
        """
        try:
            page = wikipedia.Page(self.site, titre).get()
        except pywikibot.exceptions.NoPage:
            raise PasDeDate(titre)
        dateRE = re.compile(u"\{\{([aA]rticle[ _]de[ _]qualit|[bB]on[ _]article|[aA]dQ[ _]dat)[^\}]*" \
                + u"\| *date *= *\{{0,2}(\d{1,2})[^ 0-9]*\}{0,2} ([^\| \{\}0-9]{3,9}) (\d{2,4})", re.LOCALE)
        d = dateRE.search(page)
        if d:
            mti = moistoint(d.group(3))
            if mti > 0:
                return datetime.date(int(d.group(4)), moistoint(d.group(3)), int(d.group(2)))
        raise PasDeDate(titre)

    def run(self):
        connus = self.charger()
        cat_qualite = [ u'Article de qualité',  u'Bon article']
        for cat in cat_qualite:
            categorie = catlib.Category(self.site, cat)
            cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False, start='T')
            #Comparer avec le contenu de la bdd
            for p in cpg:
                prendre = True
                for con in connus:
                    if p.title() == unicode(con[0].decode('latin1')):
                        self.connaitdeja.append(p.title())
                        prendre = False
                        break
                if prendre:   # Récupération des dates
                    try:
                        date = self.date_labellisation(p.title())
                    except PasDeDate as pdd:
                        self.pasdedate.append(pdd.page)
                        continue
                    self.qualite.append( [ p.title(), p.namespace(), date, cat ] )

        categorie = catlib.Category(self.site, u'Ancien article de qualité')
        cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False)
        for p in cpg:
            if p.namespace == 0:
                pdd = p.toggleTalkPage.title()
                for con in connus:
                    if pdd == unicode(con[0].decode('latin1')):
                        self.dechu.append( p.title() )

        wikipedia.output(u"Total: " + str(len(self.qualite)) + u" ajouts, " \
                + str(len(self.connaitdeja)) + u" déjà connus ; " \
                + str(len(self.dechu)) + u" déchus ; " + str(len(self.pasdedate)) + u" sans date.")

def main():
    site = wikipedia.getSite()
    log = u'Utilisateur:BeBot/Contenu de qualité'

    cdq = ContenuDeQualite(site, log)
    cdq.run()
    
    wikipedia.Page(site, log).put(unicode(cdq), comment=cdq.resume, minorEdit=False)

    choix = wikipedia.inputChoice(u"Sauvegarder dans la base de donnees ?", ['oui', 'non'], ['o', 'n'], 'o')
    if choix == "o" or choix == "oui":
        cdq.sauvegarder()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
