#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Trad_maintenance:
    """ Trad_maintenance
        Effectue les maintenances du Projet:Traduction :
      * supprimmer les anciennes demandes sans suite
      * clôre les relectures anciennes
    """
    def __init__(self, site, debug):
        self.site = site
        self.debug = debug
        self.resume = u"Maintenance du [[Projet:Traduction]]"
        self.date = datetime.date.today()
        self.stats = { 'suppr': 0, 'cloture' : 0, 'modele' : 0 }
        self.re_trad = re.compile(r'{{Traduction}}\s*', re.IGNORECASE)
        self.re_appel = re.compile('[\[\{]{2}Discussion:[\w/ ]+?/Traduction[\]\}]{2}\s*', re.LOCALE|re.UNICODE|re.IGNORECASE)
        self.re_statut = re.compile('\|\s*status\s*=\s*(\d{1})', re.LOCALE|re.UNICODE|re.IGNORECASE)
        
    def retirer_le_modele_Traduction(self, page):
        """ Supprime le {{Traduction}} d'une page
        """
        page.text = self.re_trad.sub(r'', page.text)
        pywikibot.output(u"&&&& retirer_le_modele_Traduction : %s" % page.title())
        pywikibot.output(page.text)
        # save page
        self.stats['modele'] += 1
        
    def supprimer(self, page, backlinks):
        """ Supprime la page et nettoie les pages liées
        """
        pywikibot.output(u"&& supprimer : %s" % page.title())
        pywikibot.output(backlinks)
        for b in backlinks:
            b.text = self.re_trad.sub(r'', b.text)
            b.text = self.re_appel.sub(r'', b.text)
            pywikibot.output(b.text)
            # save b
        self.retirer_le_modele_Traduction(BeBot.togglePageTrad(page))
        #delete page
        self.stats['suppr'] += 1
        
    def clore_traduction(self, page):
        """ Clôt une relecture : statut 3/4 -> 5
        """
        pywikibot.output(u"&&& clore : %s" % page.title())
        page.text = self.re_statut.sub('|status=5', page.text)
        pywikibot.output(page.text)
        # save page
        self.retirer_le_modele_Traduction(BeBot.togglePageTrad(page))
        self.stats['cloture'] += 1

    def traduit_de(self, page):
        """ Ajoute le {{Traduit de}} à la page de discussion
        """
        pass
        
    def run(self):
        if self.debug:
            pywikibot.output(u"=== Mode débuggage actif ; aucunes modifications effectuées")
        ancien = self.date.year - 2
        re_annee = re.compile('Traduction de (\d{4})')
        parannee = pywikibot.Category(self.site, u"Catégorie:Traduction par année")
        for c in parannee.subcategories(recurse=False):
            catTitle = c.title(withNamespace=False)
            m = re_annee.match(catTitle)
            if not m:
                continue
            annee = int(m.group(1))
            if annee <= ancien: # critère d'ancienneté
                for p in c.articles(total=4, content=True):
                    supprimer = False
                    n = self.re_statut.search(p.text)
                    if not n:
                        continue
                    n = int(n.group(1))
                    pywikibot.output(u"%s !! %i" % (p.title(), n))
                    if n == 1:
                        supprimer = True
                        backlinks = []
                        for b in p.backlinks(): # pages liées
                            if b.title()[:19] == u'Projet:Traduction/*': # sera nettoyé automatiquement
                                continue
                            elif b.namespace() == 1: # utilisé comme bandeau de licence
                                supprimer = False
                                continue
                            else:
                                backlinks.append(b)
                    elif n == 3 or n == 4:
                        self.clore_traduction(p)
                        
                    if supprimer:
                        if not self.debug:
                            self.supprimer(p, backlinks)
                            ## Vérifier aussi les licences : self.traduit_de(p)
                        else:
                            pywikibot.output(u"* [[%s]]" % p.title())
        pywikibot.out(u'=== Statistiques ===\n* Nb de pages supprimmées: %i\n* Nb de pages closes: %i\n* Nb de {{Traduction}} retirés: %i' % (self.stats['suppr'], self.stats['cloture'], self.stats['modele']))

def main():
    debug = False
    if len(sys.argv) == 1:
        debug = True
    elif len(sys.argv) != 0:
        pywwikibot.output(u"Nombre de paramètres incorrectes")
        sys.exit(1)
    site = pywikibot.getSite()
    tm = Trad_maintenance(site, debug)
    tm.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
