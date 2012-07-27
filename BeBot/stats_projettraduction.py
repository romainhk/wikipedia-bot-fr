#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Stats_ProjetTraduction:
    """ Stats_ProjetTraduction
        Analyse toutes les pages de suivi du Projet:Traduction pour en donner qq stats
    """
    def __init__(self, site):
        self.site = site
        self.resume = u"Calcul de statistiques"
        self.resultats = {
            "nb_pages" : 0,
            "taille" : 0,
            "contribution" : 0,
            "contributeur" : 0,
            "duree" : 0}

    def put_resultats(self):
        """ Affichage des resultats
        """
        total = float(self.resultats['nb_pages'])
        duree = self.resultats['duree']/total
        contribution = float(self.resultats['contribution'])/total
        contributeur = float(self.resultats['contributeur'])/total
        taille = float(self.resultats['taille'])/total
        msg = u'== Statistiques ==\nStatisitques au %s\n' % datetime.datetime.today().strftime("%d/%m/%Y")
        msg += u"* Nombre total de pages : %i\n" % total
        msg += u"* Durée moyenne d'une traduction : %i jours (%.2f années)\n" % (duree, float(duree/365.25))
        msg += u"* Nombre moyen de contributions : %.1f\n" % contribution
        msg += u"* Nombre moyen de contributeurs : %.1f\n" % contributeur
        msg += u"* Taille moyenne des pages de suivi : %.2f milliers de caractères\n" % (float(taille)/1000.0)
        msg += u"\n[[Catégorie:Maintenance du Projet Traduction|*]]\n"

        #res = pywikibot.Page(self.site, u"Utilisateur:BeBot/Stats_ProjetTraduction")
        res = pywikibot.Page(self.site, u"Projet:Traduction/*/Maintenance")
        stats = re.compile(u"^== Statistiques ==[^=]*", re.DOTALL|re.MULTILINE)
        res.text = stats.sub(r'', res.text)
        res.text = res.text + msg
        try:
            res.save(comment=self.resume, minor=False, async=True)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de modifier la page %s" % res.title(withNamespace=True) )

    def run(self):
        bot = re.compile('bot', re.IGNORECASE)
        parstatut = pywikibot.Category(self.site, u"Catégorie:Traduction par statut")
        for c in parstatut.subcategories(recurse=False):
            if c.title() != u"Catégorie:Liste des traductions par mois":
                for p in c.articles():
                    if p.namespace() == 1:
                        taille = BeBot.taille_page(p, 1) # en octet
                        #(oldid, u'2004-07-27T16:15:30Z', u'USER', u'CONTENU')
                        histo = p.getVersionHistory()
                        contribution = 0
                        contributeur = []
                        for h in histo:
                            cont = h[2]
                            if not bot.search(cont): # si le contributeur n'est pas un bot
                                contribution += 1
                                if cont not in contributeur: # si nouveau contributeur
                                    contributeur.append(cont)
                        date_deb = datetime.datetime.strptime(histo[-1][1], '%Y-%m-%dT%H:%M:%SZ')
                        date_fin = datetime.datetime.strptime(histo[0][1], '%Y-%m-%dT%H:%M:%SZ')
                        duree = date_fin - date_deb
                        duree = duree.days # en jours
                    
                        #pywikibot.output("taille:%i ; duree:%i ; contribution:%i ; contributeur:%s" % (taille, duree, contribution, contributeur) )
                        self.resultats["nb_pages"] += 1
                        self.resultats["taille"] += taille
                        self.resultats["duree"] += duree
                        self.resultats["contribution"] += contribution
                        self.resultats["contributeur"] += len(contributeur)
        self.put_resultats()

def main():
    site = pywikibot.getSite()
    spt = Stats_ProjetTraduction(site)
    spt.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
