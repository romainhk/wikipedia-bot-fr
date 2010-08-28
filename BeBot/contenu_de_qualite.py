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
    articles déjà connus seront systématiquement mises à jour (UPDATE). 
    Pour l'activer, utiliser l'option "-s".
    Arguments :
    * "Wikis" : une liste de code langue des wiki à analyser (fr par défaut)

    Exemple:
    python contenu_de_qualite.py -s fr de nl 
    >  mise à jour complète pour les wiki francophone, germanophone et néerlandophone.

        TODO : les intentions de proposition au label -> pas de catégorie associée
        TODO : les portails/themes de qualité
        TODO : propositions d'apposition pour Lien AdQ|Lien BA
        todo: voir quand plusieurs fois la même importance wikiprojet
    """
    def __init__(self, site, mode_maj):
        self.resume = u'Repérage du contenu de qualité au ' + datetime.date.today().strftime("%Y-%m-%d")
        self.site = site
        self.langue = self.site.language()
        self.log = log
        if mode_maj == "strict":
            self.maj_stricte = True
            wikipedia.output(u'# Mode "strict" actif (toutes les updates seront effectuées)')
        else:
            self.maj_stricte = False

        self.categories_de_qualite = {
                'fr': [ u'Article de qualité',   u'Bon article' ],
                'en': [ u'Featured articles',    u'Wikipedia good articles' ],
                'de': [ u'Kategorie:Wikipedia:Exzellent',   u'Kategorie:Wikipedia:Lesenswert' ],
                'es': [ u'Categoría:Wikipedia:Artículos destacados',  u'Categoría:Wikipedia:Artículos buenos' ],
                'it': [ u'Voci in vetrina' ],
                'nl': [ u'Categorie:Wikipedia:Etalage-artikelen' ]
                }
        self.cat_qualite = self.categories_de_qualite[self.langue] # Nom des catégories des deux labels
        cat_dechu = {
                'fr': u'Ancien article de qualité',
                'en': u'Wikipedia former featured articles', # prendre ceux après « # »
                'es': u'Categoría:Wikipedia:Artículos anteriormente destacados'
                }
        self.categorie_dechu = None
        if cat_dechu.has_key(self.langue):
            self.categorie_dechu = cat_dechu[self.langue]

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
                'fr': [ u'Article.*importance (?P<importance>[\w]+)$',
                        [ u'inconnue', u'faible', u'moyenne', u'élevée' ] ], # maximum
                'en': [ u'(?P<importance>[\w]+)-importance .* articles$',
                        [ 'NA', 'No', 'Bottom', 'Unknown', 'Low', 'Mid', 'High' ] ] # Top
                }
        self.importanceRE = None
        self.retrait_importance = []
        if importance_wikiprojet.has_key(self.langue):
            self.importanceRE = re.compile(importance_wikiprojet[self.langue][0], re.LOCALE)
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
        self.dechu = []         # Articles déchus
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
        resu += u". (Total après sauvegarde : %s articles, %s AdQ" \
                % ( str( len(self.nouveau) + len(self.connaitdeja) ),\
                str(self.nb_label( self.cat_qualite[0], [self.nouveau, self.connaitdeja])) )
        if len(self.cat_qualite) > 1:
            resu += u' et %s BA' % str(self.nb_label( self.cat_qualite[1], [self.nouveau, self.connaitdeja]))
        resu += u")\n\nAu reste, il y a %s articles déchus depuis la dernière vérification, %s sans date précisée, et %s déjà connus." \
                % ( str(len(self.dechu)), str(len(self.pasdedate)), str(len(self.connaitdeja)) )
        resu += u"\n=== Nouveau contenu de qualité ===\n"
        resu += self.lister_article(self.nouveau)
  #      if self.maj_stricte:
  #          resu += u'mode stricte :\n%s' % self.lister_article(self.connaitdeja)
        if BeBot.hasDateLabel(self.langue) and len(self.pasdedate) > 0:
            resu += u"\n=== Articles sans date de labellisation ===\n"
            resu += u"{{Boîte déroulante début |titre=%s articles}}" % len(self.pasdedate)
            resu += u"%s\n{{Boîte déroulante fin}}" % self.lister_article(self.pasdedate)
        if self.categorie_dechu:
            resu += u"\n=== Articles déchus depuis la dernière sauvegarde ===\n"
            resu += self.lister_article(self.dechu)
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
        wikipedia.output(u'# Sauvegarde dans la base pour la langue « %s ».' % self.langue)
        curseur = self.db.cursor()
        mode_connaitdeja = u'update'
        if self.maj_stricte and not self.categorie_dechu:
            self.vider_base(curseur)
            mode_connaitdeja = u'insert'

        for q in self.nouveau:
            self.sauvegarde_req(curseur, q, u'insert')

        if self.maj_stricte:
            for q in self.connaitdeja:
                self.sauvegarde_req(curseur, q, mode_connaitdeja)

        for d in self.dechu:
            self.sauvegarde_req(curseur, d['page'], u'delete')

    def sauvegarde_req(self, curseur, q, mode):
        """
        Ajout ou Mise à jour d'un champ de la base de données
        * mode est dans ( 'insert', 'update' )
        """
        if mode == u'insert':
            req = u'INSERT INTO %s' % self.nom_base \
                + '(page, espacedenom, date, label, taille, consultations, traduction, importance) ' \
                + u'VALUES ("%s", "%s", "%s", "%s", "%s", "%s", %s, %s)' \
                % ( unicode2html(q['page'], 'ascii'),  str(q['espacedenom']), \
                q['date'].strftime("%Y-%m-%d"), q['label'], str(q['taille']), \
                str(q['consultations']), self._put_null(q['traduction']), \
                self._put_null(q['importance']) )
        elif mode == u'update':
            req = u'UPDATE %s SET espacedenom="%s", date="%s", label="%s", taille="%s", consultations="%s", traduction=%s, importance=%s WHERE page="%s"' \
                % (self.nom_base, str(q['espacedenom']), q['date'].strftime("%Y-%m-%d"), \
                q['label'], str(q['taille']), str(q['consultations']), \
                self._put_null(q['traduction']), self._put_null(q['importance']), \
                unicode2html(q['page'], 'ascii') )
        elif mode == u'delete':
            req = u'DELETE FROM %s WHERE page="%s"' % ( self.nom_base, unicode(q) )
        else:
            wikipedia.warning(u'mode de sauvegarde non reconnu.')
            return
        try:
            curseur.execute(req)
        except MySQLdb.Error, e:
            if e.args[0] == ER.DUP_ENTRY:
                self.sauvegarde_req(curseur, q, u'update')
            else:
                wikipedia.warning("%s error %d: %s." % (mode.capitalize(), e.args[0], e.args[1]))

    def _put_null(self, obj):
        if obj:
            return u'"%s"' % unicode2html(obj, 'ascii')
        else:
            return u'NULL'

    def vider_base(self, curseur):
        """
        Vide la base de donnée associée
        (utile pour retirer les déchus sur les wiki n'ayant pas cette catégorie)
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
            pt = BeBot.togglePageTrad(self.site, page)
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

    def wikiprojet(self, page):
        """
        Donne la plus grande importance Wikiprojet
        """
        rep = None
        if BeBot.hasWikiprojet(self.langue) and self.importanceRE:
            imp = []
            if (page.namespace() % 2) == 0:
                page = page.toggleTalkPage()
            for cat in page.categories(api=True):
                b = self.importanceRE.search(cat.title())
                if b:
                    imp.append(b.group('importance'))

            if len(imp) > 0:
                for i in self.retrait_importance:
                    if imp.count(i) > 0:
                        imp.remove(i)
                        if len(imp) == 0:
                            imp.append(i)
                            break
                rep = imp[0]
        return rep

    def run(self):
        connus = BeBot.charger(self.db, self.nom_base)
        for cat in self.cat_qualite:
            categorie = catlib.Category(self.site, cat)
            cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False, start='U')
            cpg = pagegenerators.PreloadingGenerator(cpg, pageNumber=125)
            for p in cpg:
                page = p
                if p.namespace() == 1: # Pour EN:GA et IT:FA
                    page = p.toggleTalkPage()
                article_connu = False
                #Comparer avec le contenu de la bdd
                for con in connus:
                    if page.title() == html2unicode(con[0]): #con[0]=page
                        article_connu = True
                        break
                if not article_connu or self.maj_stricte:
                    try:
                        date = self.date_labellisation(page.title())  # Récupération de la date
                    except PasDeDate as pdd:
                        self.pasdedate.append( {'page': pdd.page, 'date': u''} )
                        continue
                    infos = {
    'page': page.title(),    'espacedenom': page.namespace(),     'date': date, \
    'label': cat,         'taille': BeBot.taille_page(page), \
    'consultations':BeBot.stat_consultations(page, codelangue=self.langue), \
    'traduction': self.traduction(page),   'importance': self.wikiprojet(page) \
                            }
                    if article_connu:
                        self.connaitdeja.append(infos)
                    else:
                        self.nouveau.append(infos)
                else:
                    #self.connaitdeja.append( [ p.title(), p.namespace(), '1970-01-01', cat, 0, 0, None ] )
                    self.connaitdeja.append( { 'page': page.title(), \
                          'espacedenom': page.namespace(),    'label': cat, \
                          'importance': None } )

        if self.categorie_dechu:
            categorie = catlib.Category(self.site, self.categorie_dechu)
            # Vérifier parfois avec : Wikipédia:Articles de qualité/Justification de leur rejet
            cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False, start='(')
            # start sur « ( » à cause de EN
            for p in cpg:
                ptp = p.toggleTalkPage()
                if ptp.namespace() == 0:
                    for con in connus:
                        if ptp.title() == html2unicode(con[0]):
                            self.dechu.append( {'page': ptp.title(), 'date': u''} )

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

    log =  u"<center style='font-size:larger;'>'''Log « Contenu de qualité »'''" \
            + u"; exécution du %s</center>\n{{Sommaire à droite}}\n\n" \
            % unicode(datetime.date.today().strftime("%A %e %B %Y"), "utf-8")
    for cl in wikis:
        wikipedia.output( u"== WP:%s ..." % cl )
        cdq = ContenuDeQualite(wikipedia.Site(cl), mode)
        cdq.run()
        log += unicode(cdq)
        cdq.sauvegarder()
    wikipedia.Page(wikipedia.Site('fr'), u'Utilisateur:BeBot/Contenu de qualité').put(log, \
            comment=cdq.resume, minorEdit=False)

#    choix = wikipedia.inputChoice(u"Sauvegarder dans la base de donnees ?", ['oui', 'non'], ['o', 'n'], 'o')
#    if choix == "o" or choix == "oui":
#        cdq.sauvegarder()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
