#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Trad_maintenance:
    """ Trad_maintenance
        Effectue les maintenances du Projet:Traduction :
      * supprimer les anciennes demandes sans suite
      * clore les relectures anciennes
      * supprimer les listes mensuelles devenues inutiles
    """
    def __init__(self, site, debug):
        self.site = site
        self.debug = debug
        self.resume = u'Maintenance du [[Projet:Traduction]]'
        self.date = datetime.date.today()
        self.stats = { 'suppr': 0, 'cloture' : 0, 'liste' : 0 }

        self.re_trad = re.compile(r'{{Traduction}}\s*', re.IGNORECASE)
        self.re_appel = re.compile('[\[\{]{2}Discussion:[\w/ ]+?/Traduction[\]\}]{2}\s*', re.LOCALE|re.UNICODE|re.IGNORECASE)
        self.re_statut = re.compile('\|\s*status\s*=\s*(\d{1})', re.LOCALE|re.UNICODE|re.IGNORECASE)
        self.re_traduitde = re.compile('\{\{Traduit de.+?\}\}\s*', re.IGNORECASE)
        self.re_suivi = re.compile("\{\{(Traduction/Suivi|Translation/Information)\s*\|(\w+)\|([^\|]+)\|", re.LOCALE|re.UNICODE|re.IGNORECASE)

        self.suppressions = []
        self.les_statuts = [ 'Demandes', 'En cours', 'A relire', 'En relecture', u'Terminée' ]
        les_mois = { 'janvier' : 0,    u'février' : 0,    'mars' : 0,        'avril' : 0,
                     'mai' : 0,         'juin' : 0,        'juillet' : 0,     u'août' : 0,
                     'septembre' : 0,   'octobre' : 0,     'novembre' : 0,    u'décembre': 0 }
        self.listes = {} # Nombre d'articles par statut / année / mois
        for s in self.les_statuts:
            self.listes[s] = {}
            for a in range(2006, self.date.year+1):
                self.listes[s][a] = les_mois.copy()
        
    def retirer_le_modele_Traduction(self, page):
        """ Retire le {{Traduction}} d'une page
        """
        page.text = self.re_trad.sub(r'', page.text)
        #pywikibot.output(u"&&&& retirer_le_modele_Traduction : %s" % page.title())
        #pywikibot.output(page.text)
        BeBot.save(page, comment=self.resume+u' : Retrait du modèle {{Traduction}}', minor=True, debug=self.debug)
        
    def supprimer(self, page, backlinks):
        """ Supprime la page et nettoie les pages liées
        """
        pywikibot.output(u"&& supprimer : %s" % page.title())
        pywikibot.output(backlinks)
        for b in backlinks:
            b.text = self.re_trad.sub(r'', b.text)
            b.text = self.re_appel.sub(r'', b.text)
            #pywikibot.output(b.text)
            BeBot.save(b, comment=self.resume+u' : Traduction abandonnée', debug=self.debug)
        self.retirer_le_modele_Traduction(BeBot.togglePageTrad(page))
        BeBot.delete(page, self.resume+u' : Traduction abandonnée', debug=self.debug)
        self.stats['suppr'] += 1
        
    def clore_traduction(self, page):
        """ Clôt une relecture : statut 3/4 -> 5
        """
        pywikibot.output(u"&&& clore : %s" % page.title())
        page.text = self.re_statut.sub('|status=5', page.text)
        #pywikibot.output(page.text)
        BeBot.save(page, comment=self.resume+u' : Clôture de la traduction', debug=self.debug)
        self.retirer_le_modele_Traduction(BeBot.togglePageTrad(page))
        self.stats['cloture'] += 1

    def traduit_de(self, page):
        """ Vérifie et ajoute le {{Traduit de}} à la page de discussion
        """
        disc = pywikibot.Page(self.site, page.title().replace('/Traduction', ''))
        l = self.re_trad.search(disc.text)
        m = self.re_traduitde.search(disc.text)
        if not l and not m:
            n = self.re_suivi.search(page.text)
            if n:
                langue = n.group(2)
                article = n.group(3).replace('_', ' ')
                appel = u'{{Traduit de|%s|%s}}\n' % (langue, article)
                disc.text = appel + disc.text
                #pywikibot.output(disc.text)
                BeBot.save(disc, comment=self.resume+u' : Ajout du bandeau de licence', debug=self.debug)
            else:
                pywikibot.warning(u'Impossible de trouver les infos de traduction pour [[%s]]' % page.title())
        
    def run(self):
        if self.debug:
            pywikibot.warning(u"=== Mode débuggage actif ; aucunes modifications effectuées ===")
        ancien = self.date.year - 2
        re_annee = re.compile('Traduction de (\d{4})')
        re_mois  = re.compile('Traduction du mois de ([\w\xe9\xfb]+)', re.UNICODE|re.LOCALE) # éû
        parannee = pywikibot.Category(self.site, u"Catégorie:Traduction par année")
        for c in parannee.subcategories(recurse=False): #parcours des traductions par année
            catTitle = c.title(withNamespace=False)
            m = re_annee.match(catTitle)
            if not m:
                continue
            annee = int(m.group(1))
            for p in c.articles(total=6, content=True): # Pour chaque traduction
                mois = u"" # Recherche du mois
                for d in p.categories():
                    m = re_mois.search(d.title())
                    if m:
                        mois = m.group(1)
                        break
                # Recherche du statut
                statut = self.re_statut.search(p.text)
                if not statut:
                    continue
                statut = int(statut.group(1))

                if annee <= ancien: # critère d'ancienneté
                    supprimer = False
                    #pywikibot.output(u"%s !! %i" % (p.title(), statut))
                    if statut == 1:  # Vieille demande
                        supprimer = True
                        backlinks = []
                        for b in p.backlinks(): # les pages liées
                            if b.title()[:19] == u'Projet:Traduction/*': # sera nettoyé automatiquement
                                continue
                            elif b.namespace() == 1: # utilisé comme bandeau de licence dans b
                                supprimer = False
                                continue
                            else:
                                backlinks.append(b)
                    elif statut == 3 or statut == 4: # Relecture abandonnée
                        statut = 5
                        self.clore_traduction(p)

                    if supprimer:
                        self.suppressions.append([p, backlinks])
                    elif mois != u'':
                        # Vérifier le {{Traduit de}}
                        self.traduit_de(p)
                        # Dénombrement global
                        self.listes[self.les_statuts[statut-1]][annee][mois] += 1

        # Application des suppressions
        pywikibot.output(u"------ Pages à supprimer ------")
        for p, backlinks in self.suppressions:
            self.supprimer(p, backlinks)

        # Nettoyage des listes mensuelles
        pywikibot.output(u"------ Listes à supprimer ------")
        for statut, l in self.listes.items():
            for annee, m in l.items():
                for mois, nb in m.items():
                    if nb == 0:
                        lis = pywikibot.Page(self.site, u'Projet:Traduction/*/%s/%s %i' % (statut, mois, annee))
                        #BeBot.delete(lis, self.resume+u' : Liste mensuelle périmée', debug=self.debug)
                        self.stats['liste'] += 1

        pywikibot.output(u'=== Statistiques ===\n* Nb de pages supprimées: %i\n* Nb de pages closes: %i\n* Listes périmées : %i' % (self.stats['suppr'], self.stats['cloture'], self.stats['liste']))

def main():
    debug = False
    if len(sys.argv) == 2 and sys.argv[1] == "debug":
        debug = True
    elif len(sys.argv) != 1:
        pywikibot.warning(u"Nombre de paramètres incorrectes")
        sys.exit(1)
    site = pywikibot.getSite()
    tm = Trad_maintenance(site, debug)
    tm.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
