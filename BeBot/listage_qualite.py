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
        
        #Suppression de la colonne "traduction" avec le lien sous-page
        #Supprimmer "Notes" ?

        TODO : lister les adq/ba par avancement 
                                 par theme
        TODO : propositions d'apposition pour Lien AdQ|Lien BA
        TODO : date de maj sur "Projet:Suivi des articles de qualité des autres wikipédias/Listes"
    """
    def __init__(self, site):
        self.resume = u'Listage des articles de qualité du ' + datetime.date.today().strftime("%Y-%m-%d")
        self.site = site
        self.site_fr = pywikibot.Site(u'fr')
        self.langue = self.site.language()
        self.label_se = {} # Liste des adq/ba Sens Equivalent sur fr
        self.label_nofr = {} # Liste des adq/ba sans label sur fr
        self.label_deux = {} # Liste des adq/ba doublement labellisés
        self.label_trad = {} # Liste des adq/ba avec traduction
        """ Schématiquement :
        article étranger : existe sur fr ?  -> NON => label_se
            |-> OUI : labellisé sur fr ?    -> OUI => label_deux
                |-> NON : traduction ouverte ?  -> OUI => label_trad
                    |-> NON => label_nofr
        """

        self.sous_page = {
                'de': u'Allemand',      'en': u'Anglais',
                'es': u'Espagnol',      'it': u'Italien',
                'nl': u'Néerlandais'
                }
        if self.sous_page.has_key(self.langue):
            self.page_projet = pywikibot.Page(self.site, \
                u"Projet:Suivi des articles de qualité des autres wikipédias/%s" \
                % self.sous_page[self.langue] )
        else:
            raise pywikibot.exceptions.Error( \
                    u'Impossible de trouver la page adaptée à %s dans le projet' % self.langue)
        self.statutER = re.compile(u'\| *status *= *(?P<statut>[1-5]{1})', re.LOCALE)
        self.progression = u'\| *avancement_%s *= *(?P<progression>[0-9]{1,3})'

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
        resu = u'== Sur WP:%s ==\n' % self.langue \
            + u'%i AdQ traités pour WP:%s :\n' % (total, self.langue) \
            + u'* %i articles de qualité ne le sont pas sur WP:fr ;\n' \
                % len(self.label_nofr) \
            + u'* %i n´existent pas en français ;\n' % len(self.label_se) \
            + u'* %i sont en cours de traduction/traduit (%.1f %% du total).\n' \
                % (len(self.label_trad), len(self.label_trad)/total)

        return resu

    def afficher_labels(self, labels):
        """ Affiche les éléments du dictionnaire de dictionnaire "labels"
        """
        for k, l in labels.items():
            taille = l['taille']
            trad = l['traduction']
            imp  = l['importance']
            avan = l['avancement']
            if trad is None:
                trad = u'-'
            if imp is None:
                imp  = u'-'
            if avan is None:
                avan = u'-'
            try:
                pywikibot.output(u"%s : %i ; %s ; %s ; %s" % (k, taille, trad, imp, avan) )
            except:
                pywikibot.output(u"## Erreur avec la page de taille %i" % taille)

    def publier(self):
        """ Génère le contenu de la page à publier
        """
        rep = u"<noinclude>''Page générée le %s''\n" \
                % datetime.date.today().strftime("%e %B %Y")
        # Inexistants sur fr
        rep += u'\n== Articles sans équivalent en français ==\n{{Colonnes|nombre=2|1=\n'
        for titre, infos in sorted(self.label_se.iteritems()):
            rep += u"* [[:%s:%s|%s]]\n" % (self.langue, titre, titre)
        rep += u'}}\n'

        # Comparaison
        #TODO: séparer par theme ou par avancement
        rep += u'\n== Comparaisons entre AdQ %s et leur équivalent en français ==\n' \
                % self.sous_page[self.langue].lower()
        rep += u'{| class="wikitable sortable"\n' \
            + u'! scope=col | Article original !! scope=col | Article français\n' \
            + u'! scope=col | Ratio\n'
        for titre, infos in sorted(self.label_nofr.iteritems()):
            rep += u'|-\n|[[:%s:%s|%s]] (%s ko)\n' \
                    % (self.langue, titre, titre, infos['taille'])
            rep += u'|[[%s]] (%s ko)||%s|| %s\n' % \
                    (infos['traduction'], \
                    infos['taille_fr'], \
                    str(self.ratio(infos['taille'], \
                        infos['taille_fr'])).replace('-','–') )
        rep += u'|}\n'

        # Traductions
        rep += u'\n== AdQ et traduction ==\n'
        rep += u'</noinclude>{| class="wikitable sortable" style="margin:auto;"\n' \
            + u'! scope=col | Article !! scope=col | Statut !! scope=col | Avancement\n'
        for titre, infos in sorted(self.label_trad.iteritems()):
            rep += u'|-\n|[[%s]]||%i\n|[[%s|%i %%]]\n' \
                    % (infos['traduction'], \
                    infos['statut'], \
                    infos['souspage_trad'].title(), \
                    infos['progression'] )
            #TODO: trier par statut
            #TODO: séparer les terminées à labeliser
        rep += u'|}\n'

        # Statistiques
        total = len(self.label_se) + len(self.label_nofr) \
                + len(self.label_deux) + len(self.label_trad)
        rep += u'\n== Statistiques ==\n' \
            + u'Sur %i AdQ traités pour WP:%s :\n' % (total, self.langue) \
            + u'* %i articles de qualité ne le sont pas sur WP:fr ;\n' \
                % len(self.label_nofr) \
            + u'* %i le sont sur les deux ;\n' % len(self.label_deux) \
            + u'* %i n´existent pas en français ;\n' % len(self.label_se) \
            + u'* %i sont en cours de traduction/traduit (%.1f %% du total).\n' \
                % (len(self.label_trad), len(self.label_trad)/total)

        rep += u'\n[[Catégorie:Liste de suivi des articles de qualité des autres wikipédias|%s]]</noinclude>' \
                % self.langue
        return rep

    def ratio(self, taille, taille_fr):
        """ Calcul un ratio entier entre les tailles d'articles équivalents
        """
        return round(((taille - taille_fr) * 10) / (taille + taille_fr))

    #######################################
    ### recherche d'infos

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
            page['avancement'] = BeBot.info_wikiprojet( \
                    pywikibot.Page(self.site_fr, nom_page), \
                    self.avancementER, 'avancement', \
                    self.retrait_avancement)
            rep[nom_page] = page
        return rep

    def infos_page_suivi(self, pagetrad):
        """ Récupère le statut d'une page de suivi de traduction
        """
        infos = {   'statut' : 0,
                    'progression' : 0 }
        try:
            page = Pagetrad.get()
        except:
            return infos
        statut = self.statutER.search(page)
        if statut is not None:
            infos['statut'] = statut.group('statut')
        if statut != 1:
            if statut < 4:
                recherche = u'traduction'
            else:
                recherche = u'relecture'
            progressionER = re.compile(self.progression % recherche, re.LOCALE)
            prog = progressionER.search(page)
            if prog is not None:
                infos['progression'] = prog.group('progression')
        return infos

    def run(self):
        self.label_se = self.lycos(self.nom_base, conditions="traduction IS NULL")

        art_etrangers = self.lycos(self.nom_base, conditions="traduction IS NOT NULL")
        art_fr = self.lycos('contenu_de_qualite_fr')
        for page_et, infos_et in art_etrangers.items():
            eq_fr = infos_et['traduction']
            if art_fr.has_key(eq_fr):
                self.label_deux[page_et] = infos_et
            else:
                page_trad = BeBot.togglePageTrad(pywikibot.Page(self.site_fr, eq_fr))
                if page_trad.exists():
                    self.label_trad[page_et] = infos_et
                    self.label_trad[page_et]['souspage_trad'] = page_trad
                    ipt = self.infos_page_suivi(page_trad)
                    self.label_trad[page_et]['statut'] = ipt['statut']
                    self.label_trad[page_et]['progression'] = ipt['progression']
                else:
                    self.label_nofr[page_et] = infos_et
                    self.label_nofr[page_et]['taille_fr'] = BeBot.taille_page( \
                            pywikibot.Page(self.sitefr, eq_fr))

        #pywikibot.output(u"** %s Elements de label_se :" % str(len(self.label_se)) )
        #self.afficher_labels(self.label_se)
        #pywikibot.output(u"** %s Elements de label_deux :" % str(len(self.label_deux)))
        #self.afficher_labels(self.label_deux)
        #pywikibot.output(u"** %s Elements de label_nofr :" % str(len(self.label_nofr)))
        #self.afficher_labels(self.label_nofr)
        #pywikibot.output(u"** %s Elements de label_trad :" % str(len(self.label_trad)))
        #self.afficher_labels(self.label_trad)

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
        wikis = ['nl']

    log =  u"<center style='font-size:larger;'>'''Log « Listage qualité »'''" \
            + u" ; exécution du %s</center>\n{{Sommaire à droite}}\n\n" \
            % unicode(datetime.date.today().strftime("%A %e %B %Y"), "utf-8")
    for cl in wikis:
        pywikibot.output( u"== WP:%s ..." % cl )
        try:
            lq = ListageQualite(pywikibot.Site(cl))
        except:
            continue
        lq.run()
        log += unicode(lq)
        log += lq.publier()
    pywikibot.Page(pywikibot.Site('fr'), u'Utilisateur:BeBot/Listage qualité').put(log, \
            comment=lq.resume, minorEdit=False)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
