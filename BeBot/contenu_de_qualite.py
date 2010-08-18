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
        (Persistance du nom de l'article, de son espace de nom, de la date
        de labellisation, de son label, du nombre de visites...)

    Paramètres :
    * Site wikipedia où travailler
    * Mode de mise à jour : voir "options".
    Options :
    * Mode de mise à jour : en mode strict, les informations des 
    articles déjà connus seront systématiquement mises à jour (UPDATE). 
    Pour l'activer, utiliser l'option "-s".
    Arguments :
    * "Wikis" : une liste de code langue des wiki à analyser (fr par défaut)

    Exemple:
    python contenu_de_qualite.py -s fr de nl 
    >  mise à jour complète pour les wiki francophone, germanophone et néerlandophone.

        TODO : avancement Wikiprojet
        TODO : importance Wikiprojet
        TODO : les intentions de proposition au label -> pas de catégorie associée
        TODO : les portails/themes de qualité
    """
    def __init__(self, site, mode_maj):
        self.resume = u'Repérage du contenu de qualité au ' + datetime.date.today().strftime("%Y-%m-%d")
        self.site = site
        self.langue = self.site.language()
        self.log = log

        self.categories_de_qualite = {
                'fr': [ u'Article de qualité',   u'Bon article' ],
                'en': [ u'Featured articles',    u'Wikipedia good articles' ],
                'de': [ u'Kategorie:Wikipedia:Exzellent',   u'Kategorie:Wikipedia:Lesenswert' ],
                'es': [ u'Categoría:Wikipedia:Artículos destacados',  u'Categoría:Wikipedia:Artículos buenos' ],
                'it': [ u'Voci in vetrina' ],
                'nl': [ u'Categorie:Wikipedia:Etalage-artikelen' ]
                }
        self.cat_qualite = self.categories_de_qualite[self.langue] # Nom des catégories des deux labels
        if mode_maj == "strict":
            self.maj_stricte = True
            wikipedia.output(u'# Mode de mise à jour "strict" actif (toutes les updates seront effectuées)')
        else:
            self.maj_stricte = False

        RE_date = {
            'fr': u"\{\{([aA]rticle[ _]de[ _]qualit|[bB]on[ _]article|[aA]dQ[ _]dat)[^\}]*\| *date *= *\{{0,2}(?P<jour>\d{1,2})[^ 0-9]*\}{0,2} (?P<mois>[^\| \{\}0-9]{3,9}) (?P<annee>\d{2,4})" ,
            'de': u"\{\{([eE]xzellent|[lL]esenswert)[^\}]*\|(?P<jour>\d{1,2})[^ 0-9]*\.? (?P<mois>[^\| \{\}0-9]{3,9}) (?P<annee>\d{2,4})" 
            }
        """
        'en': u"\{\{([fF]eatured[ _]article|[gG]ood article)[^\}]*\| *" ,
        'es': u"\{\{([aA]rtículo[ _]destacado|[aA]rtículo[ _]bueno)[^\}]*\| *" ,
        'it': u"\{\{[vV]etrina[^\}]*\| *" ,           'nl': u"\{\{[eE]talage[^\}]*\| *"
        """
        if RE_date.has_key(self.langue):
            self.dateRE = re.compile(RE_date[self.langue], re.LOCALE)
        else:
            self.dateRE = False
        self.interwikifr = re.compile(u"\[\[fr:(?P<iw>[^\]]+)\]\]", re.LOCALE)

        self.nouveau = []       # Nouveaux articles promus
        self.connaitdeja = []   # Articles déjà listés
        self.pasdedate = []     # Articles de qualité dont la date est inconnue
        self.dechu = []         # Articles déchus
        self.db = MySQLdb.connect(db="u_romainhk", read_default_file="/home/romainhk/.my.cnf", use_unicode=True, charset='utf8')
        #self.nom_base = u'contenu_de_qualite_%s' % self.langue
        self.nom_base = u'contenu_de_qualite'

    def __del__(self):
        self.db.close()

    def __str__(self):
        """
        Log des modifications à apporter à la bdd
        """
        resu = u'== Sur WP:%s ==\n' % self.langue
        resu += u"%s nouveaux articles labellisés trouvés : %s AdQ" \
            % (str(len(self.nouveau)), str(self.denombrer(self.cat_qualite[0], [self.nouveau])))
        if len(self.cat_qualite) > 1:
            resu += u" et %s BA" % str(self.denombrer(self.cat_qualite[1], [self.nouveau]))
        resu += u". (Total après sauvegarde : %s articles, %s AdQ" \
                % ( str( len(self.nouveau) + len(self.connaitdeja) ),\
                str(self.denombrer( self.cat_qualite[0], [self.nouveau, self.connaitdeja])) )
        if len(self.cat_qualite) > 1:
            resu += u' et %s BA' % str(self.denombrer( self.cat_qualite[1], [self.nouveau, self.connaitdeja]))
        resu += u")\n\nAu reste, il y a %s articles déchus depuis la dernière vérification, %s sans date précisée, et %s déjà connus." \
                % ( str(len(self.dechu)), str(len(self.pasdedate)), str(len(self.connaitdeja)) )
        resu += u"\n=== Nouveau contenu de qualité ===\n"
        resu += self.lister_article(self.nouveau)
        resu += u"\n=== Articles sans date de labellisation ===\n"
        resu += u"{{Boîte déroulante début |titre=%s articles}}" % len(self.pasdedate)
        resu += u"%s\n{{Boîte déroulante fin}}" % self.lister_article(self.pasdedate)
        resu += u"\n=== Articles déchus depuis la dernière sauvegarde ===\n"
        resu += self.lister_article(self.dechu)
        return resu

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
                plus = u''
                if self.langue != 'fr':
                    plus = u'%s:' % self.langue
                for p in table:
                    r.append(u"[[%s%s]]" % ( plus, unicode(p)) )
            elif type(table[0]) == type([]):
                for p in table:
                    r.append(u"[[%s]] %s" % ( unicode(p[0]), unicode(p[2]) ) )
            return u'* ' + '\n* '.join(r) + u'\n'
        return u''

    def sauvegarder(self):
        """
        Sauvegarder dans une base de données
        """
        wikipedia.output(u'# Sauvegarde dans la base pour la langue « %s ».' % self.langue)
        curseur = self.db.cursor()
        for q in self.nouveau:
            req = u'INSERT INTO %s(langue, page, espacedenom, date, label, taille, consultations, traduction)' \
                    + u'VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s", %s)' \
                    % ( self.nom_base, self.langue, unicode2html(q[0], 'ascii'),  str(q[1]),\
                    q[2].strftime("%Y-%m-%d"), q[3], str(q[4]), str(q[5]), self._put_null(q[6]) )
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
            req = u'DELETE FROM %s WHERE page="%s"' % ( self.nom_base, unicode(d) )
            try:
                curseur.execute(req)
            except:
                wikipedia.output(u"# DELETE échoué sur " + unicode(d))

    def sauvegarde_update(self, curseur, q):
        """
        Mise à jour un champ de la base de données
        """
        req = u'UPDATE %s SET espacedenom="%s", date="%s", label="%s", taille="%s", consultations="%s", traduction=%s WHERE langue="%s" AND page="%s"' \
            % (self.nom_base, str(q[1]), q[2].strftime("%Y-%m-%d"), q[3], str(q[4]), \
            str(q[5]), self._put_null(q[6]), self.langue, unicode2html(q[0], 'ascii'))
        try:
            curseur.execute(req)
        except MySQLdb.Error, e:
            print "Update error %d: %s" % (e.args[0], e.args[1])

    def _put_null(self, obj):
        if obj:
            return u'"%s"' % unicode2html(obj, 'ascii')
        else:
            return u'NULL'

    def charger(self):
        """
        Charger la liste des articles dont le label est connu depuis une base de données
        """
        curseur = self.db.cursor()
        req = "SELECT * FROM %s" % self.nom_base
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
        if self.dateRE:
            d = self.dateRE.search(page)
            if d:
                mti = BeBot.moistoint(d.group('mois'))
                if mti > 0:
                    return datetime.date(int(d.group('annee')), \
                        BeBot.moistoint(d.group('mois')), int(d.group('jour')))
        else:
            #TODO: Recherche dans l'historique l'ajout du modèle -> fullVersionHistory() !! lourd
            pass

        #if self.langue in "fr de":
        if self.langue in "fr": # Trop peu de label avec dates sur DE
            raise PasDeDate(titre)
        else:
            return datetime.date(1970, 1, 1) #Epoch

    def traduction(self, page):
        """
        Donne la page de suivi ou l'interwiki vers fr
        """
        if self.langue == 'fr':
            pt = BeBot.togglePageTrad(self.site, page)
            if pt.exists():
                return pt.title()
            else:
                return None
        else:
            for p in page.interwiki():
                res = self.interwikifr.search(p.title())
                if res:
                    return res.group('iw')
            return None

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
                        date = self.date_labellisation(p.title())  # Récupération de la date
                    except PasDeDate as pdd:
                        self.pasdedate.append(pdd.page)
                        continue
                    infos = [ p.title(), p.namespace(), date, cat, BeBot.taille_page(p),\
                            BeBot.stat_consultations(p, codelangue=self.langue), self.traduction(p) ]
                    if article_connu:
                        self.connaitdeja.append(infos)
                    else:
                        self.nouveau.append(infos)
                else:
                    self.connaitdeja.append( [ p.title(), p.namespace(), '1970-01-01', cat, 0, 0, None ] )

        categorie = catlib.Category(self.site, u'Ancien article de qualité')
        # Vérifier parfois avec : Wikipédia:Articles de qualité/Justification de leur rejet
        cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False)
        for p in cpg:
            if p.namespace == 0:
                pdd = p.toggleTalkPage.title()
                for con in connus:
                    if pdd == html2unicode(con[0]):
                        self.dechu.append( p.title() )

        wikipedia.output( u"Total: %s ajouts ; %s déjà connus ; %s déchus ; %s sans date." \
                % (str(len(self.nouveau)), str(len(self.connaitdeja)), \
                str(len(self.dechu)), str(len(self.pasdedate))) )

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

    log =  u"<center style='font-size:larger;'>'''Log « Contenu de qualité »''' ; exécussion du %s </center>\n\n" \
            % unicode(datetime.date.today().strftime("%A %e %B %Y"), "utf-8")
    for cl in wikis:
        wikipedia.output( u"== WP:%s ..." % cl )
        cdq = ContenuDeQualite(wikipedia.Site(cl), mode)
        cdq.run()
        log += unicode(cdq)
        cdq.sauvegarder()
    wikipedia.Page(wikipedia.Site('fr'), u'Utilisateur:BeBot/Contenu de qualité').put(log, comment=cdq.resume, minorEdit=False)

#    choix = wikipedia.inputChoice(u"Sauvegarder dans la base de donnees ?", ['oui', 'non'], ['o', 'n'], 'o')
#    if choix == "o" or choix == "oui":
#        cdq.sauvegarder()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
