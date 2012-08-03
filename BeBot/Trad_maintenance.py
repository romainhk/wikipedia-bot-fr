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
      * supprimer les listes mensuelles devenues inutiles (et qui ne se vident pas)
    """
    def __init__(self, site, debug):
        self.site = site
        self.debug = debug
        self.resume = u'Maintenance du [[Projet:Traduction]]'
        self.date = datetime.date.today()
        self.stats = { 'suppr': 0, 'cloture' : 0, 'traduitde': 0,  'liste' : 0 }

        self.re_trad = re.compile(r'{{Traduction}}\s*', re.IGNORECASE)
        self.re_appel = re.compile('[\[\{]{2}Discussion:[\w/ ]+?/Traduction[\]\}]{2}\s*', re.LOCALE|re.UNICODE|re.IGNORECASE)
        self.re_statut = re.compile('\|\s*status\s*=\s*(\d{1})', re.LOCALE|re.UNICODE|re.IGNORECASE)
        self.re_traduitde = re.compile('\{\{Traduit de.+?\}\}\s*', re.IGNORECASE)
        #self.re_suivi = re.compile("\{\{(Traduction/Suivi|Translation/Information)\s*\|(\w+)\|([^\|]+)\|", re.LOCALE|re.UNICODE|re.IGNORECASE)
        self.re_suivi = re.compile("\{\{((Traduction/Suivi|Translation/Information).+)\}\}<noinclude", re.LOCALE|re.IGNORECASE|re.MULTILINE|re.DOTALL)

        self.suppressions = []
        self.les_statuts = [ 'Demandes', 'En cours', 'A relire', 'En relecture', u'Terminée' ]
        les_mois = { 'janvier' : 0,    u'février' : 0,     'mars' : 0,        'avril' : 0,
                     'mai' : 0,         'juin' : 0,        'juillet' : 0,    u'août' : 0,
                     'septembre' : 0,   'octobre' : 0,     'novembre' : 0,   u'décembre': 0 }
        self.listes = {} # Nombre d'articles par statut / année / mois
        for s in self.les_statuts:
            self.listes[s] = {}
            for a in range(2006, self.date.year+1):
                self.listes[s][a] = les_mois.copy()
        
    def __str__(self):
        r  = u"== Rapport d'exécution ==\n"
        r += u'* Nb de pages supprimées: %i\n' % self.stats['suppr']
        r += u'* Nb de traductions closes: %i\n' % self.stats['cloture']
        r += u'* Nb de {{Traduit de}} ajoutés: %i\n' % self.stats['traduitde']
        r += u'* Listes périmées : %i\n' % self.stats['liste']
        return r

    def retirer_le_modele_Traduction(self, page):
        """ Retire le {{Traduction}} d'une page
        """
        page.text = self.re_trad.sub(r'', page.text)
        BeBot.save(page, comment=self.resume+u' : Retrait du modèle {{Traduction}}', minor=True, debug=self.debug)
        
    def supprimer(self, page):
        """ Supprime la page et nettoie les pages liées
        """
        pywikibot.output(u"&& supprimer : %s" % page.title())
        self.retirer_le_modele_Traduction(BeBot.togglePageTrad(page)) # si traduction active
        for b in page.backlinks():
            #b.text = self.re_trad.sub(r'', b.text) #-> prise ne charge par retirer_le_modele_Traduction
            b.text = self.re_appel.sub(r'', b.text)
            #pywikibot.output(b.text)
            BeBot.save(b, comment=self.resume+u' : Traduction abandonnée', debug=self.debug)
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
                a = BeBot.modeletodic(n.group(0))
                if not a.has_key(1) or not a.has_key(2):
                    pywikibot.warning(u"Impossible de trouver le nom ou la langue d'origine pour %s" % page.title())
                    return False
                langue = a[1]
                article = a[2].replace('_', ' ')
                plus = u''
                if a.has_key(u'oldid') and a.has_key(u'jour') and a.has_key(u'mois') and a.has_key(u'année') :
                    # TODO : utiliser le oldid pour retrouver sa date
                    oldid = a['oldid']
                    jour = a['jour']
                    mois = BeBot.moistoint(a['mois'])
                    annee = a[u'année']
                    if oldid != u'' and jour != u'' and mois != 0 and annee != u'':
                        plus = u"|%s|%s/%i/%s" % (a['oldid'], a['jour'], mois, a[u'année'])
                appel = u'{{Traduit de|%s|%s%s}}\n' % (langue, article, plus)
                pywikibot.output(appel)
                disc.text = appel + disc.text
                #pywikibot.output(disc.text)
                BeBot.save(disc, comment=self.resume+u' : Ajout du bandeau de licence', debug=self.debug)
                self.stats['traduitde'] += 1
            else:
                pywikibot.warning(u'Impossible de trouver les infos de traduction pour %s' % page.title())
        
    def run(self):
        if self.debug:
            pywikibot.warning(u"== Mode débuggage actif ; aucunes modifications effectuées ==")
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
            for p in c.articles(total=9, content=True): # Pour chaque traduction
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
                if mois != u'':
                    # Dénombrement global
                    self.listes[self.les_statuts[statut-1]][annee][mois] += 1

                if annee <= ancien: # critère d'ancienneté
                    if statut == 1:  # Vieille demande
                        self.suppressions.append(p)
                    elif statut == 3 or statut == 4: # Relecture abandonnée
                        statut = 5
                        self.clore_traduction(p)
                else:
                    # Vérifier simplement le {{Traduit de}}
                    self.traduit_de(p)

        # Application des suppressions
        pywikibot.output(u"------ Pages à supprimer ------")
        for p in self.suppressions:
            self.supprimer(p)

        # Nettoyage des listes mensuelles
        pywikibot.output(u"------ Listes à supprimer ------")
        for statut, l in self.listes.items():
            for annee, m in l.items():
                for mois, nb in m.items():
                    if nb == 0:
                        lis = pywikibot.Page(self.site, u'Projet:Traduction/*/%s/%s %i' % (statut, mois, annee))
                        #BeBot.delete(lis, self.resume+u' : Liste mensuelle périmée', debug=self.debug)
                        self.stats['liste'] += 1

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
    pywikibot.output(tm)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
