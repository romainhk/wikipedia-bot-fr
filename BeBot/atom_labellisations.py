#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys, sqlite3
import webhelpers.feedgenerator as feedgenerator
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Atom_Labellisations:
    """ Atom Labellisations
        Génère un flux Atom des articles labellisés
    """
    def __init__(self, site, debug):
        self.site = site
        self.debug = debug
        self.ajd = datetime.datetime.today()
        self.re_modele = re.compile(u"\{\{((Article de qualité|Bon article|Portail de qualité|Bon portail).+?\}\})", re.LOCALE|re.IGNORECASE|re.MULTILINE|re.DOTALL|re.UNICODE)
        self.re_date = re.compile(u"(\d+)[ /-]([^\s]+)[ /-](\d+)", re.LOCALE|re.IGNORECASE|re.UNICODE)
        self.cats = [u"Catégorie:Article de qualité", u"Catégorie:Bon article"]
        # Le flux
        self.fp = open('labellisations.atom', 'w')
        self.feed = feedgenerator.Atom1Feed(
            title=u"Labellisations sur WP:fr",
            link=u"http://romainhk.hd.free.fr/labellisations.atom",
            description=u"Les labellisations sur la wikipédia francophone.",
            language=u"fr")

        #DB
        bddsqlite = "atom_labellisations.sqlite"
        try:
            self.conn = sqlite3.connect(bddsqlite)
        except:
            pywikibot.output("Impossible d'ouvrir la base sqlite {0}".format(bddsqlite))
            exit(2)
        self.conn.row_factory = sqlite3.Row
        self.nom_base = u'labels'

    def ajouteralabdd(self, page):
        n = self.re_modele.search(page.text) # Récupération des infos de traduction
        if n:
            mod = BeBot.modeletodic(n.group(0))
            categorie = n.group(2)
            date = datetime.datetime(1970, 1, 1)
            if 'date' in mod:
                o = self.re_date.search(mod['date'])
                if o:
                    jour = int(o.group(1))
                    mois = BeBot.moistoint(o.group(2))
                    annee = int(o.group(3))
                    date = datetime.datetime(annee, mois, jour)
                else:
                    pywikibot.error(u"Impossible de reconnaitre le format de date pour %s" % page.title())
            # Sauvegarde
            curseur = self.conn.cursor()
            req = u'INSERT INTO %s ' % self.nom_base \
                + u'(titre, label, date) VALUES ("%s", "%s", "%s")' \
                % (page.title(), categorie, date)
            try:
                curseur.execute(req)
            except sqlite3.Error as e:
                pywikibot.error(u"Erreur lors de l'INSERT :\n%s" % (e.args[0]))
            self.conn.commit()

            pywikibot.output("Ajout de %s" % page.title())
            return True
        pywikibot.error(u"Impossible de trouver le modèle AdQ/BA sur la page %s" % page.title())
        return False

    def supprimerdelabdd(self, page):
        curseur = self.conn.cursor()
        req = u'DELETE FROM %s ' % self.nom_base \
            + u'WHERE titre="%s"' % page.title()
        try:
            curseur.execute(req)
        except sqlite3.Error as e:
            pywikibot.error(u"Erreur lors du DELETE :\n%s" % (e.args[0]))
        self.conn.commit()
        pywikibot.output("Suppression de %s" % page.title())
        
    def ajouterauflux(self, page, date, categorie):
        self.feed.add_item(
            title=page.title(),
            link=u"http://fr.wikipedia.org/wiki/%s" % page.title(asUrl=True),
            description=u"",
            pubdate=date,
            categories=[categorie])

    def run(self):
        adq_wp = []
        adq_base = []
        res = BeBot.charger_bdd(self.conn, self.nom_base, ordre='"titre" ASC')
        for r in res:
            adq_base.append(pywikibot.Page(self.site, r['titre']))

        for cat in self.cats:
            labels = pywikibot.Category(self.site, cat)
            for a in labels.articles(total=5):
                adq_wp.append(a)
        # Différences
        nouveaux = list(set(adq_wp) - set(adq_base))
        dechus   = list(set(adq_base) - set(adq_wp))
        for a in nouveaux:
            self.ajouteralabdd(a)
        for a in dechus:
            self.supprimerdelabdd(a)
        # Génération du flux
        res = BeBot.charger_bdd(self.conn, self.nom_base, ordre='"date" DESC')
        for r in res:
            p = pywikibot.Page(self.site, r['titre'])
            date = datetime.datetime.strptime(r['date'], '%Y-%m-%d %H:%M:%S')
            categorie = r['label']
            self.ajouterauflux(p, date, categorie)
        self.feed.write(self.fp, 'utf-8')
        self.fp.close()

def main():
    site = pywikibot.getSite()
    if BeBot.blocage(site):
        sys.exit(7)
    debug = False
    for par in sys.argv:
        if par.lower() == "debug":
            debug = True

    al = Atom_Labelisations(site, debug)
    al.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
