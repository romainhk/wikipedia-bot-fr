#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, MySQLdb, getopt, sys, locale
from MySQLdb.constants import ER
import pywikibot
from pywikibot import pagegenerators
import BeBot
locale.setlocale(locale.LC_ALL, '')

class ContenuDeQualite:
    """ Contenu de Qualité
        Recherche et sauvegarde les AdQ/BA existants.
        (Persistance du nom de l'article, de son label...)
        Comparer avec http://fr.wikipedia.org/wiki/Utilisateur:Maloq/Stats

    Paramètres :
    * pywikibot.Site où travailler
    Arguments :
    * "Wikis" : une liste de code langue des wiki à analyser (fr par défaut)

    Exemple:
    python contenu_de_qualite.py fr de nl 
    >  mise à jour pour les wiki francophone, germanophone et néerlandophone.

        TODO : les intentions de proposition au label -> pas de catégorie associée
        TODO : les portails/themes de qualité
        TODO : passer à sqlite
    """
    def __init__(self, site):
        self.site = site
        self.langue = self.site.language()
        self.total_avant = 0

        self.categories_de_qualite = {
                'fr': [ u'Article de qualité',   u'Bon article' ],
                'en': [ u'Featured articles',    u'Wikipedia good articles' ],
                'de': [ u'Kategorie:Wikipedia:Exzellent',   u'Kategorie:Wikipedia:Lesenswert' ],
                'es': [ u'Categoría:Wikipedia:Artículos destacados',  u'Categoría:Wikipedia:Artículos buenos' ],
       # pas celle-ci        'it': [ u'Voci in vetrina' ],
                'nl': [ u'Categorie:Wikipedia:Etalage-artikelen' ]
                } #! l'ordre est important
        self.cat_qualite = self.categories_de_qualite[self.langue]
            # Nom des catégories correspondant aux deux labels

        self.interwikifrRE = re.compile(u"\[\[fr:(?P<iw>[^\]]+)\]\]", re.LOCALE|re.UNICODE)

        # Principaux conteneurs
        self.nouveau = []       # Nouveaux articles promus
        self.connaitdeja = []   # Articles déjà listés
        """ Structure des éléments de "nouveau" et "connaitdeja" :
        { 'page': html'',   'label': u'',   'taille': int,    'traduction': html'' }
        """
        # DB
        self.db = MySQLdb.connect(db="u_romainhk_transient", \
                                read_default_file="/home/romainhk/.my.cnf", \
                                use_unicode=True, charset='utf8')
        self.curseur = self.db.cursor()
        self.nom_base = u'contenu_de_qualite_%s' % self.langue

    def __del__(self):
        self.db.close()

    #######################################
    ### __str__
    def __str__(self):
        """
        Log des modifications à apporter à la bdd
        """
        resu = u'\n== Sur WP:%s ==\n' % self.langue
        resu += u"%i nouveaux articles labellisés trouvés : %i AdQ" \
            % (len(self.nouveau), self.nb_label(u"AdQ", [self.nouveau]))
        if len(self.cat_qualite) > 1:
            resu += u" et %i BA" % self.nb_label(u"BA", [self.nouveau])
        resu += u". (Total avant sauvegarde : %i articles. Après : %s articles ; %i AdQ" \
                % ( self.total_avant, str(len(self.nouveau) + len(self.connaitdeja)),\
                self.nb_label(u"AdQ", [self.nouveau, self.connaitdeja]) )
        if len(self.cat_qualite) > 1:
            resu += u' et %i BA' % self.nb_label( u"BA", [self.nouveau, self.connaitdeja])
        resu += u")\n\nAu reste, il y a %i déjà connus, et %i retraits." \
                % ( len(self.connaitdeja), self.connus )
        if len(self.nouveau) > 0 and len(self.nouveau) < 12:
            resu += u"\n=== Nouveau contenu de qualité ===\n"
            resu += self.lister_article(self.nouveau)
        return resu + u'\n'

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
            for p in table:
                r.append(u"[[%s%s]]" % ( plus, pywikibot.page.html2unicode(p['page'])) )
            return u'* ' + '\n* '.join(r) + u'\n'
        return u''

    #######################################
    ### db
    def sauvegarder(self):
        """
        Sauvegarder dans une base de données
        """
        pywikibot.log(u'# Sauvegarde dans la base pour la langue "%s".' % self.langue)

        for q in self.nouveau:
            self.req_bdd(q, 'insert')

    def req_bdd(self, q, mode):
        """
        Ajout ou Mise à jour d'un champ de la base de données
        * "mode" est dans ( 'insert', 'update', 'delete' )
        """
        if mode == 'insert':
            req = u'INSERT INTO %s' % self.nom_base \
                + '(page, label, taille, traduction) ' \
                + u'VALUES ("%s", "%s", "%s", %s)' \
                % ( q['page'].replace('"', '\\"'), \
                    q['label'], \
                    str(q['taille']), \
                    self._put_null(q['traduction']) )
        elif mode == 'update':
            req = u'UPDATE %s SET' % self.nom_base \
                + u' label="%s", taille="%s", traduction=%s' \
                % ( q['label'], \
                    str(q['taille']), \
                    self._put_null(q['traduction']) ) \
                + u' WHERE page="%s"' % q['page'].replace('"', '\\"')
        elif mode == 'delete':
            req = u'DELETE FROM %s WHERE page="%s"' \
                    % ( self.nom_base, unicode(q).replace('"', '\\"') )
        else:
            pywikibot.warning(u'mode de sauvegarde "%s" non reconnu.' % mode)
            return
        try:
            self.curseur.execute(req)
        except MySQLdb.Error, e:
            if e.args[0] == ER.DUP_ENTRY:
                self.req_bdd(q, 'update')
            else:
                pywikibot.warning(u"%s error %d: %s.\nReq : %s" \
                        % (mode.capitalize(), e.args[0], e.args[1], req) )

    def _put_null(self, obj):
        if obj is not None:
            return u'"%s"' % obj.replace('"', '\\"')
        else:
            return u'NULL'

    def vider_base(self):
        """
        Vide la base de donnée associée (pour retirer les déchus)
        """
        pywikibot.log(u"## Vidage de l'ancienne base")
        req = u'TRUNCATE TABLE %s' % self.nom_base
        try:
            self.curseur.execute(req)
        except MySQLdb.Error, e:
            pywikibot.warning(u"Truncate error %d: %s" % (e.args[0], e.args[1]))
    
    #######################################
    ### recherche d'infos
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
            res = self.interwikifrRE.search(page.text)
            if res is not None:
                return res.group('iw')
            else:
                return None

    def get_infos(self, page, cattoa):
        """
        Recherche toutes les informations nécessaires associées à une page
        """
        infos = {
            'page': page.title(), \
            'label': cattoa, \
            'taille': BeBot.taille_page(page), \
            'traduction': self.traduction(page), \
            }
        return infos

    def normaliser_page(self, con):
        return unicode(con[0], 'UTF-8')

    def run(self):
        NB_AJOUTS = 0
        RETRAITS = True
        connus = BeBot.charger_bdd(self.db, self.nom_base, champs=u'page')
        connus = map(self.normaliser_page, connus)
        self.total_avant = len(connus)
        ordre_cats = [ u'AdQ', u'BA', u'?' ]
        for cat in self.cat_qualite:
            categorie = pywikibot.Category(self.site, cat)
            cpg = pagegenerators.CategorizedPageGenerator(categorie, recurse=False)
            try:
                i = self.categories_de_qualite[self.langue].index(cat)
            except:
                i = 2
            cattoa = ordre_cats[i]

            for p in pagegenerators.DuplicateFilterPageGenerator(cpg):
                if NB_AJOUTS < 2000:
                    if p.namespace() == 0:
                        page = p
                    elif p.namespace() == 1: # Pour EN:GA et IT:FA
                        page = p.toggleTalkPage()
                    else:
                        continue
                    if page.isRedirectPage():
                        page = page.getRedirectTarget()
                    title = page.title()
                    if title not in connus: #Comparaison avec le contenu de la bdd
                        infos = self.get_infos(page, cattoa)
                        NB_AJOUTS += 1
                        if infos is not None:
                            self.nouveau.append(infos)
                    else:
                        connus.remove(title)
                        self.connaitdeja.append( \
                               { 'page': title, \
                              'label': cattoa } ) # Ils ne seront pas ajoutés
                else:
                    pywikibot.output("Limite d'ajouts atteinte avec "+p.title())
                    RETRAITS = False
                    break

        # On retire ceux qui ont disparus
        if RETRAITS:
            pywikibot.output('Retraits : '+str(connus))
            for c in connus:
                self.req_bdd(c, 'delete')
        self.connus = len(connus)

        pywikibot.log( u"Total: %i ajouts ; %i déjà connus ; %i retraits." \
                % (len(self.nouveau), len(self.connaitdeja), len(connus)) )

def main():
    if BeBot.blocage(pywikibot.getSite()):
        sys.exit(7)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s")
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    if len(args) > 0:
        wikis = args
    else:
        wikis = ['fr']

    log =  u"<center style='font-size:larger;'>'''Log « Contenu de qualité »'''" \
            + u" ; exécution du %s</center>\n{{Sommaire à droite}}\n" \
            % unicode(datetime.date.today().strftime("%A %e %B %Y"), "utf-8")

    for cl in wikis:
        pywikibot.log( u"== WP:%s ..." % cl )
        cdq = ContenuDeQualite(pywikibot.Site(cl))
        cdq.run()
        cdq.sauvegarder()
        log += unicode(cdq)

    pywikibot.Page(pywikibot.Site('fr'), \
        u'Utilisateur:BeBot/Contenu de qualité').put(log, \
            comment=u'Repérage du contenu de qualité au ' \
            + datetime.date.today().strftime("%Y-%m-%d"), \
            minorEdit=False)
    pywikibot.log(u'\nPasser voir le log complet sur ' \
            + u'http://fr.wikipedia.org/wiki/Utilisateur:BeBot/Contenu_de_qualit%C3%A9')

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
