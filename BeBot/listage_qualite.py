#!/usr/bin/python
# -*- coding: utf-8  -*-
#$ -m ae
import re, datetime, MySQLdb, getopt, sys, locale
from MySQLdb.constants import ER
import BeBot
import pywikibot
from pywikibot import pagegenerators, catlib
locale.setlocale(locale.LC_ALL, '')

class ListageQualite:
    """ Listage Qualité
        Liste les AdQ/BA existants par avancement sur le P:SAdQaW
        
        TODO : lister les adq/ba par theme ?
        TODO : supporter l'italien
        TODO : propositions d'apposition de Lien AdQ|Lien BA => à part
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
        self.total = 0
        self.limite_label_se = 300

        self.sous_page = {
                'en': u'Anglais',
                'de': u'Allemand',
                'es': u'Espagnol',
                'it': u'Italien',
                'nl': u'Néerlandais'
                }
        if self.sous_page.has_key(self.langue):
            self.page_projet = pywikibot.Page(self.site_fr, \
                u"Projet:Suivi des articles de qualité des autres wikipédias/%s" \
                % self.sous_page[self.langue] )
        else:
            raise pywikibot.exceptions.Error( \
                u'Impossible de trouver la page adaptée à %s dans le projet' \
                % self.langue)

        self.statutER = re.compile(u'\| ?status\s*=\s*(?P<statut>[1-5]{1})', re.LOCALE)
        self.progression = u'[^ ]\| ?avancement_%s *= *(?P<progression>\d{1,3})'

        #Avancement wikiprojet
        self.avancementER = re.compile(u'Article.*avancement (?P<avancement>[\wé]+)$')
        self.retrait_avancement = [ \
                u'AdQ', u'BA', u'A', u'B', u'BD', u'ébauche', u'inconnue' ]

        #DB
        self.db = MySQLdb.connect(db="u_romainhk", \
                                read_default_file="/home/romainhk/.my.cnf", \
                                use_unicode=True, charset='utf8')
        self.nom_base = u'contenu_de_qualite_%s' % self.langue

    def __del__(self):
        self.db.close()

    #######################################
    ### Présentation
    def __str__(self):
        """ Log des modifications à apporter à la bdd
        """
        resu = u'\n== %i articles pour [[%s|WP:%s]] ==\n' \
                % (self.total, self.page_projet.title(), self.langue ) \
            + u'* %i adq/ba ne le sont pas sur WP:fr ;\n' \
                % len(self.label_nofr) \
            + u'* %i n´existent pas en français ;\n' % len(self.label_se) \
            + u'* %i sont en cours de traduction/traduit.\n' % len(self.label_trad)
        return resu + u'\n'

    def liste_sans_equivalent(self, les_se, titre):
        lim_deroul = 50
        rep = u"\n=== %s ===\n" % titre
        if len(les_se) > lim_deroul:
            rep += u'{{Boîte déroulante début|titre=Plus de %i %s}}\n' % (lim_deroul, titre)
        rep += u'{{Colonnes|nombre=2|1=\n'
        for titre, infos in sorted(les_se.iteritems()):
            rep += u"* [[:%s:%s]]\n" % (self.langue, titre)
        rep += u'}}\n'
        if len(les_se) > lim_deroul:
            rep += u'{{Boîte déroulante fin}}\n'
        return rep

    def publier(self):
        """ Génère le contenu de la page à publier
        """
        rep = u"<noinclude>{{Sommaire à droite}}\n" \
                + u"''Page générée le %s.''\n\n" \
                    % unicode(datetime.date.today().strftime("%e %B %Y"), 'UTF-8')
        rep += u'%i articles labellisés traités pour WP:%s ;<br />\n' \
                    % (self.total, self.langue) \
                + u'%i sont labellisés sur les deux wikis.\n' \
                    % len(self.label_deux) \
                + u"{{Clr}}\n"
        # Inexistants sur fr
        rep += u'\n== %i articles sans équivalent en français ==\n' \
                % len(self.label_se)
        label_se_adq = {}
        #lim_adq = 250
        #lim_ba = 100
        label_se_ba = {}
        for titre, infos in self.label_se.items():
            #if infos['label'] == 'AdQ' and len(label_se_adq) < lim_adq :
            if infos['label'] == 'AdQ' :
                label_se_adq[titre] = infos
            #elif infos['label'] == 'BA' and len(label_se_ba) < lim_ba :
            elif infos['label'] == 'BA' :
                label_se_ba[titre] = infos
#        rep += u"''Tronqué à partir de %i adq et %i ba.''\n" % (lim_adq, lim_ba)
        rep += u"''Limité à %i articles.''\n" % self.limite_label_se
        if len(label_se_adq) > 0:
            rep += self.liste_sans_equivalent(label_se_adq, 'AdQ')
        if len(label_se_ba) > 0:
            rep += self.liste_sans_equivalent(label_se_ba, 'BA')

        # Comparaison
        rep += u'\n== Comparaisons entre AdQ/BA %s et son équivalent en français ==\n' \
                % self.sous_page[self.langue].lower()
        rep += u"''Tri de %i articles selon l'avancement" % len(self.label_nofr) \
            + u" wikiprojet minimum de l'article en français hors traductions.''\n"
        for avan in self.retrait_avancement[2:]:
            rep += u'\n=== %s ===\n' % avan.capitalize()
            rep += u'{| class="wikitable sortable"\n' \
                + u'! scope=col | Article %s !! scope=col | Article français\n' \
                % self.sous_page[self.langue].lower() \
                + u'! scope=col | Ratio\n'
            for titre, infos in self.trier_comparaison(avan):
                rep += u'|-\n|[[:%s:%s|%s]] – %s ko\n' \
                        % (self.langue, titre, titre, infos['taille'])
                rep += u'|[[%s]] – %s ko||%s\n' % \
                        (infos['traduction'], \
                        infos['taille_fr'], \
                        unicode(self.ratio(infos['taille'], \
                            infos['taille_fr'])).replace(u'-',u'–') )
            rep += u'|}\n'

        # Traductions
        rep += u'\n== %i articles en traduction/traduit ==\n' % len(self.label_trad)
        rep += u'</noinclude>'
        rep += u'{| class="wikitable sortable" style="margin:auto;"\n' \
            + u'!scope=col| Article fr !!scope=col| Statut !!scope=col| Progression\n'
        for titre, infos in self.trier_pagetrad("1234"):
            rep += u'|-\n|[[%s]]||%s\n|[[%s|%i %%]]\n' \
                    % (infos['traduction'], \
                    BeBot.stou(infos['statut']), \
                    infos['souspage_trad'].title(), \
                    infos['progression'] )
        rep += u'|}\n<noinclude>\n'

        rep += u'\n=== Traductions terminées à labelliser ===\n'
        rep += u'{{Colonnes|nombre=2|1=\n'
        for titre, infos in self.trier_pagetrad("5"):
            rep += u'* [[%s]] ([[%s|spt]])\n' \
                    % (infos['traduction'], \
                    infos['souspage_trad'].title() )
        rep += u'}}\n'

        rep += u'\n[[Catégorie:Liste de suivi des articles de qualité des autres wikipédias|%s]]</noinclude>' \
                % self.langue
        return rep

    def ratio(self, taille, taille_fr):
        """ Calcul un ratio entier entre les tailles d'articles équivalents
        """
        return int(round(((taille - taille_fr) * 10) / (taille + taille_fr)))

    def trier_pagetrad(self, elus="1234"):
        """ Tri les pages de suivi de traduction par statut
        """
        statut = [ {}, {}, {}, {}, {}, {} ]
        for cle, infos in self.label_trad.items():
            statut[infos['statut']][cle] = infos

        for t in elus:
            for p in sorted(statut[int(t)].iteritems()):
                yield p

    def trier_comparaison(self, critere):
        """ Tri les comparaisons entre articles par avancement
        """
        ok = {}
        for cle, infos in self.label_nofr.iteritems():
            if infos['avancement'] == critere:
                ok[cle] = infos

        for p in sorted(ok.iteritems()):
            yield p

    #######################################
    ### Recherche d'infos
    def lycos(self, nom_base, conditions=None, limite=None):
        """ Récupère les articles labellisés de la base correspondants
            à certaines conditions
        """
        rep = {}
        champs = [ 'page', 'taille', 'traduction', 'importance', 'label' ]
        articles = BeBot.charger_bdd(self.db, nom_base, \
                champs=", ".join(champs), cond=conditions)
        #articles = sorted(articles.items())
        i = 0
        for a in articles:
            if limite is not None and i >= limite:
                break
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
            page[champs[4]] = unicode(a[4], 'UTF-8')
            page['avancement'] = BeBot.info_wikiprojet( \
                    pywikibot.Page(self.site_fr, nom_page), \
                    self.avancementER, 'avancement', \
                    self.retrait_avancement)
            rep[nom_page] = page
            i += 1

        return rep

    def infos_page_suivi(self, pagetrad):
        """ Récupère statut et progression d'une page de suivi de traduction
        """
        infos = {   'statut' : 0,
                    'progression' : 0 }
        try:
            page = pagetrad.get()
        except pywikibot.exceptions.IsRedirectPage:
            pywikibot.warning(u"verifier les interlangues pour %s (redirection)." \
                    % pagetrad.title() )
            return self.infos_page_suivi(pagetrad.getRedirectTarget())
        except:
            pywikibot.warning(u'impossible de récupérer la page %s' \
                    % pagetrad.title())
            return infos
        statut = self.statutER.search(page)
        if statut is not None:
            statut = int(statut.group('statut'))
            infos['statut'] = statut

        if statut != 5:
            if statut < 4:
                recherche = u'traduction'
            else:
                recherche = u'relecture'
            progressionER = re.compile(self.progression % recherche, re.LOCALE)
            prog = progressionER.search(page)
            if prog is not None:
                infos['progression'] = int(prog.group('progression'))
        return infos

    def run(self):
        self.label_se = self.lycos(self.nom_base, \
                conditions="traduction IS NULL", limite=self.limite_label_se)

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
                            pywikibot.Page(self.site_fr, eq_fr))

        self.total = len(self.label_se) + len(self.label_nofr) \
                + len(self.label_deux) + len(self.label_trad)

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

    log = u''
    for cl in wikis:
        pywikibot.output( u"== WP:%s ..." % cl )
        try:
            lq = ListageQualite(pywikibot.Site(cl))
        except:
            continue
        lq.run()
        lq.page_projet.put(lq.publier(), \
                comment=u'Mise à jour mensuelle des listings', minorEdit=False)
        log += unicode(lq)
    pywikibot.Page(pywikibot.Site('fr'), \
            u'Utilisateur:BeBot/Listage qualité').put(log, \
            comment=lq.resume, minorEdit=False)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
