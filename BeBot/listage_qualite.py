#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, MySQLdb, getopt, sys
from MySQLdb.constants import ER
import BeBot
import pywikibot
from pywikibot import pagegenerators, catlib

class ListageQualite:
    """ Listage Qualité
        Liste les AdQ/BA existants par avancement ( et theme ? ) sur le P:SAdQaW

        TODO : lister les adq/ba
        TODO : propositions d'apposition pour Lien AdQ|Lien BA
        TODO : date de maj sur "Projet:Suivi des articles de qualité des autres wikipédias/Listes"
    """
    def __init__(self, site):
        self.resume = u'Listage des articles de qualité du ' + datetime.date.today().strftime("%Y-%m-%d")
        self.site = site
        self.langue = self.site.language()
        self.label_se = {} # Liste des adq/ba Sens Equivalent sur fr
        self.label_nofr = {} # Liste des adq/ba sans label sur fr
        self.label_deux = {} # Liste des adq/ba doublement labellisés
        self.label_trad = {} # Liste des adq/ba avec traduction

        sous_page = {
                'de': u'Allemand',          'en': u'Anglais',
                'es': u'Espagnol',          'it': u'Italien',
                'nl': u'Néerlandais'
                }
        if sous_page.has_key(self.langue):
            self.page_projet = pywikibot.Page(self.site, \
                u"Projet:Suivi des articles de qualité des autres wikipédias/%s" \
                % sous_page[self.langue] )
        else:
            self.page_projet = None

        #Avancement
        self.avancementER = re.compile( u'Article.*avancement (?P<avancement>[\wé]+)$' )
        self.retrait_avancement = [ u'AdQ', u'BA', u'A', u'B', u'BD', u'ébauche' ] # inconnue

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
        """ Log des modifications à apporter à la bdd
        """
        resu = u'== Sur WP:%s ==\n' % self.langue

        return resu

    def afficher_labels(self, labels):
        """ Affiche les éléments du dictionnaire de dictionnaire "labels"
        """
        for k, l in labels.items():
            taille = unicode(l['taille'])
            trad = l['traduction']
            imp  = l['importance']
            if not trad:
                trad = u'-'
            if not imp:
                imp  = u'-'
            try:
                pywikibot.output(u"%s : %s ; %s ; %s" % (k, taille, trad, imp) )
            except:
                pywikibot.output(u"## Erreur avec la page de taille %s" % taille)

    def publier(self):
        """ Génère la page à publier
        """

    #######################################
    ### recherche d'infos
    #'avancement': BeBot.info_wikiprojet(page, self.avancementER, 'avancement', self.retrait_avancement)

    def lycos(self, nom_base, conditions=None):
        """ Récupère les articles labellisés correspondants à certaines conditions
        """
        champs = [ 'page', 'taille', 'traduction', 'importance' ]
        articles = BeBot.charger_bdd(self.db, nom_base, \
                champs=", ".join(champs), cond=conditions)
        rep = {}
        for a in articles:
            page = {}
            nom_page = unicode(a[0], 'UTF-8')
            page[champs[1]] = int(a[1])
            if a[2] is not None:
                page[champs[2]] = unicode(a[2], 'UTF-8')
            else:
                page[champs[2]] = None
            if a[3] is not None:
                page[champs[3]] = unicode(a[3], 'UTF-8')
            else:
                page[champs[3]] = None
            rep[nom_page] = page
        return rep

    def run(self):
        #self.label_nofr = self.lycos(self.nom_base)
        self.label_se = self.lycos(self.nom_base, conditions="traduction IS NULL")

        art_etrangers = self.lycos(self.nom_base, conditions="traduction IS NOT NULL")
        art_fr = self.lycos('contenu_de_qualite_fr')
        for page_et, infos_et in art_etrangers.items():
            eq_fr = infos_et['traduction']
            if art_fr.has_key(eq_fr):
                self.label_deux[page_et] = infos_et
            else:
                page_trad = BeBot.togglePageTrad(pywikibot.Page(self.site, eq_fr))
                if page_trad.exists():
                    self.label_trad[page_et] = infos_et
                    self.label_trad[page_et]['traduction'] = page_trad
                else:
                    self.label_nofr[page_et] = infos_et

        pywikibot.output(u"* %s Elements de label_se :" % str(len(self.label_se)) )
        self.afficher_labels(self.label_se)
        pywikibot.output(u"* Elements de label_deux :")
        self.afficher_labels(self.label_deux)
        pywikibot.output(u"* Elements de label_nofr :")
        self.afficher_labels(self.label_nofr)
        pywikibot.output(u"* Elements de label_trad :")
        self.afficher_labels(self.label_trad)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    if len(args) > 0:
        wikis = args
    else:
        wikis = ['fr']

    log =  u"<center style='font-size:larger;'>'''Log « Listage qualité »'''" \
            + u" ; exécution du %s</center>\n{{Sommaire à droite}}\n\n" \
            % unicode(datetime.date.today().strftime("%A %e %B %Y"), "utf-8")
    for cl in wikis:
        pywikibot.output( u"== WP:%s ..." % cl )
        lq = ListageQualite(pywikibot.Site(cl))
        lq.run()
        log += unicode(lq)
        lq.publier()
    #pywikibot.Page(pywikibot.Site('fr'), u'Utilisateur:BeBot/Listage qualité').put(log, \
    #        comment=lq.resume, minorEdit=False)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
