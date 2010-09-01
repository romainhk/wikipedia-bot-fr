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
    * Site (wikipedia) où travailler
    * Mode de mise à jour : voir "options".
    Options :
    * Mode de mise à jour : en mode strict, les informations des 
    articles déjà connus seront systématiquement mises à jour (UPDATE) et
    les articles déchus retirés. 
    Pour l'activer, utiliser l'option "-s".
    Arguments :
    * "Wikis" : une liste de code langue des wiki à analyser (fr par défaut)

    Exemple:
    python contenu_de_qualite.py -s fr de nl 
    >  mise à jour complète pour les wiki francophone, germanophone et néerlandophone.

        TODO : les intentions de proposition au label -> pas de catégorie associée
        TODO : les portails/themes de qualité
    """
    def __init__(self, site, mode_maj):
        self.resume = u'Repérage du contenu de qualité au ' + datetime.date.today().strftime("%Y-%m-%d")
        self.site = site
        self.langue = self.site.language()
        if mode_maj == "strict":
            self.maj_stricte = True
            wikipedia.output(u'# Mode "strict" actif (toutes les updates seront effectuées et la base vidée)')
        else:
            self.maj_stricte = False
        self.total_avant = 0

        self.categories_de_qualite = {
                'fr': [ u'Article de qualité',   u'Bon article' ],
                'en': [ u'Featured articles',    u'Wikipedia good articles' ],
                'de': [ u'Kategorie:Wikipedia:Exzellent',   u'Kategorie:Wikipedia:Lesenswert' ],
                'es': [ u'Categoría:Wikipedia:Artículos destacados',  u'Categoría:Wikipedia:Artículos buenos' ],
       # pas celle-ci        'it': [ u'Voci in vetrina' ],
                'nl': [ u'Categorie:Wikipedia:Etalage-artikelen' ]
                }
        self.cat_qualite = self.categories_de_qualite[self.langue]
            # Nom des catégories correspondant aux deux labels

        # REs
        RE_date = {
            'fr': u"\{\{([aA]rticle[ _]de[ _]qualit|[bB]on[ _]article|[aA]dQ[ _]dat)[^\}]*\| *date *= *\{{0,2}(?P<jour>\d{1,2})[^ 0-9]*\}{0,2} (?P<mois>[^\| \{\}0-9]{3,9}) (?P<annee>\d{2,4})" ,
            'de': u"\{\{([eE]xzellent|[lL]esenswert)[^\}]*\|(?P<jour>\d{1,2})[^ 0-9]*\.? (?P<mois>[^\| \{\}0-9]{3,9}) (?P<annee>\d{2,4})" 
            }
        if RE_date.has_key(self.langue):
            self.dateRE = re.compile(RE_date[self.langue], re.LOCALE)
        else:
            self.dateRE = None
        self.interwikifrRE = re.compile(u"\[\[fr:(?P<iw>[^\]]+)\]\]", re.LOCALE)
        #Wikiprojet _-_ par langue : regexp des cat wikiprojet, ordre de suppression si plusieurs
        importance_wikiprojet = {
                'fr': [ u'Article.*importance (?P<importance>[\wé]+)$',
                        [ u'inconnue', u'faible', u'moyenne', u'élevée' ] ], # maximum
                'en': [ u'(?P<importance>[\w]+)-importance',
                        [ 'NA', 'No', 'Bottom', 'Unknown', 'Low', 'Mid', 'High' ] ] # Top
                }
        self.importanceER = None
        self.retrait_importance = []
        if importance_wikiprojet.has_key(self.langue):
            self.importanceER = re.compile(importance_wikiprojet[self.langue][0], re.LOCALE)
            self.retrait_importance = importance_wikiprojet[self.langue][1]

        # Principaux conteneurs
        self.nouveau = []       # Nouveaux articles promus
        self.connaitdeja = []   # Articles déjà listés
        """ Structure des éléments de "nouveau" et "connaitdeja" :
        { 'page': html'',   'espacedenom': int,     'date': date,
          'label': u'',     'taille': int,          'consultations': int,
          'traduction': html'',     'importance': u'' }
        """
        self.pasdedate = []     # Articles de qualité dont la date est inconnue
        # DB
        self.db = MySQLdb.connect(db="u_romainhk", \
                                read_default_file="/home/romainhk/.my.cnf", \
                                use_unicode=True, charset='utf8')
        self.nom_base = u'contenu_de_qualite_%s' % self.langue

    def __del__(self):
        self.db.close()

    #######################################
    ### __str__
    def __str__(self):
        """
        Log des modifications à apporter à la bdd
        """
        resu = u'== Sur WP:%s ==\n' % self.langue
        resu += u"%s nouveaux articles labellisés trouvés : %s AdQ" \
            % (str(len(self.nouveau)), str(self.nb_label(self.cat_qualite[0], [self.nouveau])))
        if len(self.cat_qualite) > 1:
            resu += u" et %s BA" % str(self.nb_label(self.cat_qualite[1], [self.nouveau]))
        resu += u". (Total avant sauvegarde : %s articles. Après : %s articles ; %s AdQ" \
                % ( str(self.total_avant), str(len(self.nouveau) + len(self.connaitdeja)),\
                str(self.nb_label( self.cat_qualite[0], [self.nouveau, self.connaitdeja])) )
        if len(self.cat_qualite) > 1:
            resu += u' et %s BA' % str(self.nb_label( self.cat_qualite[1], [self.nouveau, self.connaitdeja]))
        resu += u")\n\nAu reste, il y a %s articles sans date précisée, et %s déjà connus." \
                % ( str(len(self.pasdedate)), str(len(self.connaitdeja)) )
        if len(self.nouveau) > 0 and not self.mode_stricte:
            resu += u"\n=== Nouveau contenu de qualité ===\n"
            resu += self.lister_article(self.nouveau)
#            if self.maj_stricte:
#                resu += u'mode stricte :\n%s' % self.lister_article(self.connaitdeja)
        if BeBot.hasDateLabel(self.langue) and len(self.pasdedate) > 0:
            resu += u"\n=== Articles sans date de labellisation ===\n"
            resu += u"{{Boîte déroulante début |titre=%s articles}}" % len(self.pasdedate)
            resu += u"%s\n{{Boîte déroulante fin}}" % self.lister_article(self.pasdedate)
        return resu

    def nb_label(self, label, tab):
        """
        Dénombre les articles (contenus dans les tableaux de tab) correspondants à un label
        """
        i = 0
        for l in tab:
            for n in l:
                if n['label'] == label:
                    i += 1
        return i

    def lister_article(self, table):
        """ __str__
        Génère une wiki-liste à partir d'un tableau d'articles
        """
        if len(table) > 0:
            plus = u''
            if not self.langue == 'fr':
                plus = u':%s:' % self.langue
            r = []
            if BeBot.hasDateLabel(self.langue):
                for p in table:
                    r.append(u"[[%s%s]] %s" % ( plus, html2unicode(p['page']), unicode(p['date']) ) )
            else:
                for p in table:
                    r.append(u"[[%s%s]]" % ( plus, html2unicode(p['page'])) )
            return u'* ' + '\n* '.join(r) + u'\n'
        return u''

    #######################################
    ### db
    def sauvegarder(self):
        """
        Sauvegarder dans une base de données
        """
        wikipedia.output(u'# Sauvegarde dans la base pour la langue "%s".' % self.langue)
        curseur = self.db.cursor()
        if self.maj_stricte:
            self.vider_base(curseur)
            for q in self.connaitdeja:
                self.req_bdd(curseur, q, 'insert')

        for q in self.nouveau:
            self.req_bdd(curseur, q, 'insert')

    def req_bdd(self, curseur, q, mode):
        """
        Ajout ou Mise à jour d'un champ de la base de données
        * "mode" est dans ( 'insert', 'update', 'delete' )
        """
        if mode == 'insert':
            req = u'INSERT INTO %s' % self.nom_base \
                + '(page, espacedenom, date, label, taille, consultations, traduction, importance) ' \
                + u'VALUES ("%s", "%s", "%s", "%s", "%s", "%s", %s, %s)' \
                % ( unicode2html(q['page'], 'ascii'),  str(q['espacedenom']), \
                q['date'].strftime("%Y-%m-%d"), q['label'], str(q['taille']), \
                str(q['consultations']), self._put_null(q['traduction']), \
                self._put_null(q['importance']) )
        elif mode == 'update':
            req = u'UPDATE %s SET espacedenom="%s", date="%s", label="%s", taille="%s", consultations="%s", traduction=%s, importance=%s WHERE page="%s"' \
                % (self.nom_base, str(q['espacedenom']), q['date'].strftime("%Y-%m-%d"), \
                q['label'], str(q['taille']), str(q['consultations']), \
                self._put_null(q['traduction']), self._put_null(q['importance']), \
                unicode2html(q['page'], 'ascii') )
        elif mode == 'delete':
            req = u'DELETE FROM %s WHERE page="%s"' % ( self.nom_base, unicode(q) )
        else:
            wikipedia.output(u'~ Mode de sauvegarde "%s" non reconnu.' % mode)
            return
        try:
            curseur.execute(req)
        except MySQLdb.Error, e:
            if e.args[0] == ER.DUP_ENTRY:
                self.req_bdd(curseur, q, 'update')
            else:
                wikipedia.output(u"~ %s error %d: %s.\nReq : %s" \
                        % (mode.capitalize(), e.args[0], e.args[1], req) )

    def _put_null(self, obj):
        if obj:
            return u'"%s"' % unicode2html(obj, 'ascii')
        else:
            return u'NULL'

    def vider_base(self, curseur):
        """
        Vide la base de donnée associée (pour retirer les déchus)
        """
        wikipedia.output(u"# Vidage de la base de donnée")
        req = u'TRUNCATE TABLE %s' % self.nom_base
        try:
            curseur.execute(req)
        except MySQLdb.Error, e:
            print "Truncate error %d: %s" % (e.args[0], e.args[1])
    
    #######################################
    ### recherche d'infos
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

        if BeBot.hasDateLabel(self.langue):
            raise PasDeDate(titre)
        else:
            return datetime.date(1970, 1, 1) #Epoch

    def traduction(self, page):
        """
        Donne la page de suivi ou l'interwiki vers fr
        """
        if self.langue == 'fr':
            pt = BeBot.togglePageTrad(page)
            if pt.exists():
                return pt.title()
            else:
                return None
        else:
            for p in page.interwiki():
                res = self.interwikifrRE.search(p.title())
                if res:
                    return res.group('iw')
            return None

    def get_infos(self, page, cat):
        """
        Recherche toutes les informations nécessaires associées à une page
        """
        try:
            date = self.date_labellisation(page.title())
        except PasDeDate as pdd:
            self.pasdedate.append( {'page': pdd.page, 'date': u''} )
            return None
        infos = {
    'page': page.title(),    'espacedenom': page.namespace(),     'date': date, \
    'label': cat,         'taille': BeBot.taille_page(page), \
    'consultations':BeBot.stat_consultations(page, codelangue=self.langue), \
    'traduction': self.traduction(page), \
    'importance': BeBot.info_wikiprojet(page, self.importanceER, 'importance', self.retrait_importance)
            }
        return infos

    def run(self):
        connus = BeBot.charger_bdd(self.db, self.nom_base)
        self.total_avant = len(connus)
        for cat in self.cat_qualite:
            categorie = catlib.Category(self.site, cat)
            cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False)
            cpg = pagegenerators.PreloadingGenerator(cpg, pageNumber=125)
            for p in cpg:
                if p.namespace() == 0:
                    page = p
                elif p.namespace() == 1: # Pour EN:GA et IT:FA
                    page = p.toggleTalkPage()
                else:
                    continue
                article_connu = False
                for con in connus: #Comparaison avec le contenu de la bdd
                    if page.title() == html2unicode(con[0]): #con[0]=page
                        article_connu = True
                        break
                if not article_connu:
                    infos = self.get_infos(page, cat)
                    if infos:
                        self.nouveau.append(infos)
                elif self.maj_stricte:
                    infos = self.get_infos(page, cat)
                    if infos:
                        self.connaitdeja.append(infos)
                else:
                    self.connaitdeja.append( { 'page': page.title(), \
                          'espacedenom': page.namespace(),    'label': cat, \
                          'importance': None } ) # Ils ne seront pas ajoutés

        wikipedia.output( u"Total: %s ajouts ; %s déjà connus ; %s sans date." \
                % (str(len(self.nouveau)), str(len(self.connaitdeja)), \
                str(len(self.pasdedate))) )

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

    log =  u"<center style='font-size:larger;'>'''Log « Contenu de qualité »'''" \
            + u" ; exécution du %s</center>\n{{Sommaire à droite}}\n\n" \
            % unicode(datetime.date.today().strftime("%A %e %B %Y"), "utf-8")
    for cl in wikis:
        wikipedia.output( u"== WP:%s ..." % cl )
        cdq = ContenuDeQualite(wikipedia.Site(cl), mode)
        cdq.run()
        log += unicode(cdq)
        cdq.sauvegarder()
    wikipedia.Page(wikipedia.Site('fr'), u'Utilisateur:BeBot/Contenu de qualité').put(log, \
            comment=cdq.resume, minorEdit=False)

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
