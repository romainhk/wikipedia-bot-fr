#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, MySQLdb, getopt, sys
from MySQLdb.constants import ER
import BeBot
from wikipedia import *
import pagegenerators, catlib

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

    Paramètres:
    * Site wikipedia où travailler
    * Mode de mise à jour : voir plus bas.

    Options / Arguments :
    * Option "Mode de mise à jour" : en mode strict, les informations des articles déjà connus seront systématiquement mises à jour (UPDATE). Pour l'activer, utiliser l'option "-s".
    * Arguments "Wikis" : une liste de code langue des wiki à analyser (fr par défaut)

    Exemple:
    contenu_de_qualite.py -s fr de nl  >  mise à jour complète pour les wiki francophone, germanophone et néerlandophone.

        TODO : internationalisation : ajouter un champ "langue" et une liste de wiki à analyser
            * ajouter un champ "article équivalent français"
        TODO : la sous-page de traduction, si elle existe
        TODO : infos sur l'article (nombre inclusions, de contributeurs -> contributingUsers()...)
        TODO : les intentions de proposition au label.
        TODO : les portails/themes de qualité
    """
    def __init__(self, site, mode_maj):
        self.resume = u'Repérage du contenu de qualité au ' + datetime.date.today().strftime("%Y-%m-%d")
        self.site = site
        self.langue = self.site.language()
        self.log = log

        self.categories_de_qualite = {
                'fr': [ u'Article de qualité',   u'Bon article'],
                'en': [ u'Featured articles',    u'Wikipedia good articles'],
                'de': [ u'Wikipedia:Exzellent',  u'Wikipedia:Lesenswert'],
                'es': [ u'Wikipedia:Artículos destacados',  u'Wikipedia:Artículos buenos'],
                'it': [ u'Voci in vetrina',      u''],
                'nl': [ u'Wikipedia:Etalage-artikelen',     u'']
                }
        self.cat_qualite = self.categories_de_qualite[self.langue] # Nom des catégories des deux labels
        if mode_maj == "strict":
            self.maj_stricte = True
            wikipedia.output(u'# Mode de mise à jour "strict" actif (toutes les updates seront effectuées)')
        else:
            self.maj_stricte = False

        RE_dates = {
                'fr': u"\{\{([aA]rticle[ _]de[ _]qualit|[bB]on[ _]article|[aA]dQ[ _]dat)[^\}]*\| *date *= *\{{0,2}(?P<jour>\d{1,2})[^ 0-9]*\}{0,2} (?P<mois>[^\| \{\}0-9]{3,9}) (?P<annee>\d{2,4})" ,
                'de': u"\{\{([eE]xzellent|[lL]esenswert)[^\}]*\|(?P<jour>\d{1,2})[^ 0-9]*. (?P<mois>[^\| \{\}0-9]{3,9}) (?P<annee>\d{2,4})" ,
                'en': u"", 'es': u"", 'it': u"", 'nl': u""
                }
        """
        'en': u"\{\{([fF]eatured[ _]article|[gG]ood article)[^\}]*\| *" ,
        'es': u"\{\{([aA]rtículo[ _]destacado|[aA]rtículo[ _]bueno)[^\}]*\| *" ,
        'it': u"\{\{[vV]etrina[^\}]*\| *" ,           'nl': u"\{\{[eE]talage[^\}]*\| *"
        """
        self.dateRE = re.compile(RE_dates[self.langue], re.LOCALE)

        self.nouveau = []       # Nouveaux articles promus
        self.connaitdeja = []   # Articles déjà listés
        self.pasdedate = []     # Articles de qualité dont la date est inconnue
        self.dechu = []         # Articles déchus
        self.db = MySQLdb.connect(db="u_romainhk", read_default_file="/home/romainhk/.my.cnf", use_unicode=True, charset='utf8')

    def __del__(self):
        self.db.close()

    def __str__(self):
        """
        Log des modifications à apporter à la bdd
        """
        resultat = u'== Sur WP:%s ==\n' % self.langue
        resultat += u"%s nouveaux articles labellisés trouvés : %s AdQ et %s BA." \
            % (str(len(self.nouveau)), str(self.denombrer(self.cat_qualite[0], [self.nouveau])), str(self.denombrer(self.cat_qualite[1], [self.nouveau])))
        resultat += u" (Total après sauvegarde : %s articles, %s AdQ et %s BA)\n\n" \
                % ( str( len(self.nouveau) + len(self.connaitdeja) ),\
                str(self.denombrer( self.cat_qualite[0], [self.nouveau, self.connaitdeja]) ),\
                str(self.denombrer( self.cat_qualite[1], [self.nouveau, self.connaitdeja]) ) ) 
        resultat += u"Au reste, il y a %s articles déchus depuis la dernière vérification, %s sans date précisée, et %s déjà connus." \
                % ( str(len(self.dechu)), str(len(self.pasdedate)), str(len(self.connaitdeja)) )
        resultat += u"\n=== Nouveau contenu de qualité ===\n"
        resultat += self.lister_article(self.nouveau)
        resultat += u"\n=== Articles sans date de labellisation ===\n"
        resultat += self.lister_article(self.pasdedate)
        resultat += u"\n=== Articles déchus depuis la dernière sauvegarde ===\n"
        resultat += self.lister_article(self.dechu)
        return resultat

    def denombrer(self, label, tab):
        """
        Dénombre les articles (contenus dans les tableaux de tab) correspondants à un label
        """
        i = 0
        for l in tab:
            for n in l:
                if n[3] == label:
                    i += 1
        return i

    def lister_article(self, table):
        """ __str__
        Génère une wiki-liste à partir d'un tableau d'articles
        """
        if len(table) > 0:
            r = []
            if type(table[0]) == type(u""):
                for p in table:
                    r.append(u"[[%s]]" % unicode(p) )
            elif type(table[0]) == type([]):
                for p in table:
                    r.append(u"[[%s]] %s" % ( unicode(p[0]), unicode(p[2]) ) )
            return u'* ' + '\n* '.join(r) + u'\n'
        return u''

    def sauvegarder(self):
        """
        Sauvegarder dans une base de données
        """
        wikipedia.output(u'# Sauvegarde dans la base.')
        curseur = self.db.cursor()
        for q in self.nouveau:
            req = u'INSERT INTO contenu_de_qualite(langue, page, espacedenom, date, label, taille, consultations)' \
                    + u'VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s")' \
                    % ( self.langue, unicode2html(q[0], 'ascii'),  str(q[1]), q[2].strftime("%Y-%m-%d"), q[3], str(q[4]), str(q[5]) )
            try:
                curseur.execute(req)
            except MySQLdb.Error, e:
                if e.args[0] == ER.DUP_ENTRY:
                    self.sauvegarde_update(curseur, q)
                else:
                    print "Erreur %d: %s" % (e.args[0], e.args[1])
                continue

        if self.maj_stricte:
            for q in self.connaitdeja:
                self.sauvegarde_update(curseur, q)

        for d in self.dechu:
            req = u'DELETE FROM contenu_de_qualite WHERE page="%s"' % unicode(d)
            try:
                curseur.execute(req)
            except:
                wikipedia.output(u"# DELETE échoué sur " + unicode(d))

    def sauvegarde_update(self, curseur, q):
        """
        Mise à jour un champ de la base de données
        """
        req = u'UPDATE contenu_de_qualite SET espacedenom="%s", date="%s", label="%s", taille="%s", consultations="%s" WHERE langue="%s" AND page="%s"' \
            % (str(q[1]), q[2].strftime("%Y-%m-%d"), q[3], str(q[4]), str(q[5]), self.langue, unicode2html(q[0], 'ascii'))
        try:
            curseur.execute(req)
        except MySQLdb.Error, e:
            print "Update error %d: %s" % (e.args[0], e.args[1])

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
        d = self.dateRE.search(page)
        if d:
            mti = BeBot.moistoint(d.group('mois'))
            if mti > 0:
                return datetime.date(int(d.group('annee')), BeBot.moistoint(d.group('mois')), int(d.group('jour')))
        else:
            #TODO: Recherche dans l'historique l'ajout du modèle -> fullVersionHistory() !! lourd
            pass

        if self.langue in "fr de":
            raise PasDeDate(titre)
        else:
            return '1970-01-01'

    def run(self):
        connus = self.charger()
        for cat in self.cat_qualite:
            categorie = catlib.Category(self.site, cat)
            cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False)
            #Comparer avec le contenu de la bdd
            for p in cpg:
                article_connu = False
                for con in connus:
                    if p.title() == html2unicode(con[1]): #con[1]=page
                        article_connu = True
                        break
                if not article_connu or self.maj_stricte:
                    try:
                        date = self.date_labellisation(p.title())   # Récupération de la date
                    except PasDeDate as pdd:
                        self.pasdedate.append(pdd.page)
                        continue
                    infos = [ p.title(), p.namespace(), date, cat, BeBot.taille_page(p), BeBot.stat_consultations(p, self.langue) ]
                    if article_connu:
                        self.connaitdeja.append(infos)
                    else:
                        self.nouveau.append(infos)
                else:
                    self.connaitdeja.append( [ p.title(), p.namespace(), '1970-01-01', cat, 0, 0 ] )

        categorie = catlib.Category(self.site, u'Ancien article de qualité')
        cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False)
        for p in cpg:
            if p.namespace == 0:
                pdd = p.toggleTalkPage.title()
                for con in connus:
                    if pdd == html2unicode(con[0]):
                        self.dechu.append( p.title() )

        wikipedia.output( u"Total: %s ajouts ; %s déjà connus ; %s déchus ; %s sans date." \
                % (str(len(self.nouveau)), str(len(self.connaitdeja)), str(len(self.dechu)), str(len(self.pasdedate))) )

def main():
    mode = u'nouveaux-seulement'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "s")
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == '-s':
            mode = "strict"
    if args:
        wikis = args
    else:
        wikis = ['fr']
    print wikis

    site = wikipedia.getSite()
    pagelog = u'Utilisateur:BeBot/Contenu de qualité'

    log =  u"<center style='font-size:larger;'>'''Log « Contenu de qualité »''' ; exécussion du %s </center>\n\n" \
            % unicode(datetime.date.today().strftime("%A %e %B %Y"), "utf-8")
    for cl in wikis:
        cdq = ContenuDeQualite(wikipedia.Site(cl), mode)
        cdq.run()
        log += unicode(cdq)
        cdq.sauvegarder()
    wikipedia.Page(site, pagelog).put(log, comment=cdq.resume, minorEdit=False)

#    choix = wikipedia.inputChoice(u"Sauvegarder dans la base de donnees ?", ['oui', 'non'], ['o', 'n'], 'o')
#    if choix == "o" or choix == "oui":
#        cdq.sauvegarder()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
