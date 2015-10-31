#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys, sqlite3
#import webhelpers.feedgenerator as feedgenerator
import pyatom
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Atom_Labellisations:
    """ Atom Labellisations
        Génère un flux Atom des articles récemment labellisés
    """
    def __init__(self, site, bddsqlite, fluxatom, debug):
        self.site = site
        self.debug = debug
        self.ajd = datetime.datetime.today()
        self.re_modele = re.compile("\{\{((Article[ _]de[ _]qualité|Bon[ _]article|Portail[ _]de[ _]qualité|Bon[ _]portail).+?\}\})", re.LOCALE|re.IGNORECASE|re.MULTILINE|re.DOTALL|re.UNICODE)
        self.re_date = re.compile("([^ _]+)[ /-]([^\s]+)[ /-](\d+)", re.LOCALE|re.IGNORECASE|re.UNICODE)
        self.cats = ["Catégorie:Article de qualité", "Catégorie:Bon article", "Catégorie:Portail de qualité", "Catégorie:Bon portail"]
        # Le flux
        self.fp = open(fluxatom, 'w') # OUTPUT
        #self.feed = feedgenerator.Atom1Feed(
        #    title="[WP:fr] Labellisations",
        #    link="http://hosaka.hd.free.fr/labellisations.atom",
        #    description="Les articles récemment labellisés (AdQ, BA, PdQ, BP) sur la wikipédia francophone.",
        #    language="fr")
        self.feed = pyatom.AtomFeed(
            title="[WP:fr] Labellisations",
            subtitle="Les articles récemment labellisés (AdQ, BA, PdQ, BP) sur la wikipédia francophone.",
            feed_url="http://hosaka.hd.free.fr/labellisations.atom",
            url="http://hosaka.hd.free.fr/",
            author="BeBot")

        #DB
        try:
            self.conn = sqlite3.connect(bddsqlite)
        except:
            pywikibot.output("Impossible d'ouvrir la base sqlite {0}".format(bddsqlite))
            exit(2)
        self.conn.row_factory = sqlite3.Row
        self.nom_base = 'labels'

    def ajouteralabdd(self, page):
        # Suppression d'un modèle chiant pour le calcul de date
        p = page.text.replace('{{1er}}', '1').replace('{{er}}', '')
        # Récupération des infos
        n = self.re_modele.search(p)
        if n:
            mod = BeBot.modeletodic(n.group(0))
            categorie = n.group(2).replace('_', ' ')
            # Remise au propre de la casse
            categorie = categorie[0].upper() + categorie[1:].lower()
            date = datetime.datetime(1970, 1, 1)
            if 'date' in mod:
                o = self.re_date.search(mod['date'])
                if o:
                    try:
                        jour = int(o.group(1))
                        mois = BeBot.moistoint(o.group(2))
                        annee = int(o.group(3))
                    except:
                        pywikibot.error("Problème de conversion de la date '%s' sur [[%s]]" % (o.group(0), page.title()))
                        return False
                    date = datetime.datetime(annee, mois, jour)
                else:
                    pywikibot.error("Impossible de reconnaitre le format de date pour %s" % page.title())
                    return False
            # Sauvegarde
            curseur = self.conn.cursor()
            req = 'INSERT INTO %s ' % self.nom_base \
                + '(titre, label, date) VALUES ("%s", "%s", "%s")' \
                % (page.title(), categorie, date)
            if self.debug:
                #pywikibot.output("Ajout de %s" % page.title())
                print('.',end="",flush=True)
                return
            try:
                curseur.execute(req)
            except sqlite3.Error as e:
                pywikibot.error("Erreur lors de l'INSERT :\n%s" % (e.args[0]))
            self.conn.commit()
            return True
        if page.namespace() == 0:
            pywikibot.error("Impossible de trouver le modèle AdQ/BA sur l'article %s" % page.title())
        return False

    def supprimerdelabdd(self, page):
        curseur = self.conn.cursor()
        req = 'DELETE FROM %s ' % self.nom_base \
            + 'WHERE titre="%s"' % page.title()
        if self.debug:
            pywikibot.output("Suppression de %s" % page.title())
            return
        try:
            curseur.execute(req)
        except sqlite3.Error as e:
            pywikibot.error("Erreur lors du DELETE :\n%s" % (e.args[0]))
        self.conn.commit()
        
    def ajouterauflux(self, page, date, categorie):
        #self.feed.add_item(
        #    title=page.title(),
        #    link="http://fr.wikipedia.org/wiki/%s" % page.title(asUrl=True),
        #    description=categorie,
        #    pubdate=date,
        #    categories=[categorie])
        self.feed.add(
            title=page.title(),
            url="http://fr.wikipedia.org/wiki/%s" % page.title(asUrl=True),
            content=categorie,
            content_type="html",
            author="BeBot",
            updated=date)

    def run(self):
        adq_wp = []
        adq_base = []
        res = BeBot.charger_bdd(self.conn, self.nom_base, ordre='"titre" ASC')
        for r in res:
            adq_base.append(pywikibot.Page(self.site, r['titre']))

        for cat in self.cats:
            labels = pywikibot.Category(self.site, cat)
            for a in labels.articles():
                adq_wp.append(a)
        # Différences
        nouveaux = list(set(adq_wp) - set(adq_base))
        dechus   = list(set(adq_base) - set(adq_wp))
        for a in nouveaux:
            self.ajouteralabdd(a)
        for a in dechus:
            self.supprimerdelabdd(a)
        if len(dechus) > 0:
            pywikibot.output("Articles déchus de leur status : {0}".format(dechus))
        # Génération du flux
        res = BeBot.charger_bdd(self.conn, self.nom_base, lim=50, ordre='"date" DESC')
        for r in res:
            p = pywikibot.Page(self.site, r['titre'])
            date = datetime.datetime.strptime(r['date'], '%Y-%m-%d %H:%M:%S')
            categorie = r['label']
            self.ajouterauflux(p, date, categorie)
        if not self.debug:
            #self.feed.write(self.fp, 'utf-8')
            self.fp.write(self.feed.to_string())
        pywikibot.output("Nombre de modifications sur la base : {0}".format(self.conn.total_changes))
        self.fp.close()

def main():
    site = pywikibot.getSite()
    if BeBot.blocage(site):
        sys.exit(7)
    debug = False
    if len(sys.argv) > 4 or len(sys.argv) < 3:
        pywikibot.error("Syntaxe: atom_labellisations.py BASE_SQLITE FLUX_ATOM [DEBUG]")
        sys.exit(1)

    bddsqlite = sys.argv[1]
    fluxatom = sys.argv[2]
    for par in sys.argv:
        if par.lower() == "debug":
            debug = True

    al = Atom_Labellisations(site, bddsqlite, fluxatom, debug)
    al.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
