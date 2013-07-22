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
      TODO: vérifier que les demandes récentes n'aient pas de {{Traduit de}}
    """
    def __init__(self, site, debug):
        self.site = site
        self.debug = debug
        self.resume = u'Restructuration du [[Projet:Traduction]]'
        self.date = datetime.date.today()
        self.stats = { 'suppr': 0, 'cloture' : 0, 'traduitde': 0 }

        self.re_trad = re.compile(r'{{(Demande de t|T)raduction[^\}/]*}}\s*', re.LOCALE|re.IGNORECASE)
        #self.re_appel = re.compile('[\[\{]{2}(Discu(ssion|ter):[^\]\}]+?/Traduction)[^\]\}]*[\]\}]{2}\s*', re.LOCALE|re.UNICODE|re.IGNORECASE|re.DOTALL)
        self.re_appel = re.compile('{{(Discu(ssion|ter):[^\]\}]+?/Traduction)[^\]\}]*}}\s*', re.LOCALE|re.UNICODE|re.IGNORECASE|re.DOTALL)
        self.re_statut = re.compile('\|\s*status\s*=\s*(\d{1})', re.LOCALE|re.UNICODE|re.IGNORECASE)
        self.re_traduitde = re.compile('\{\{Traduit de.+?\}\}\s*', re.IGNORECASE)
        self.re_suivi = re.compile("\{\{((Traduction/Suivi|Translation/Information).+?\}\})", re.LOCALE|re.IGNORECASE|re.MULTILINE|re.DOTALL)

        self.re_discus = re.compile("== *Discussion *==(.*?)^==", re.LOCALE|re.IGNORECASE|re.MULTILINE|re.DOTALL)

        self.les_statuts = [ 'Demandes', 'En cours', 'A relire', 'En relecture', u'Terminée' ]
        les_mois = { 'janvier' : 0,    u'février' : 0,     'mars' : 0,        'avril' : 0,
                     'mai' : 0,         'juin' : 0,        'juillet' : 0,    u'août' : 0,
                     'septembre' : 0,   'octobre' : 0,     'novembre' : 0,   u'décembre': 0 }
        self.listes = {} # Nombre d'articles par statut / année / mois
        for s in self.les_statuts:
            self.listes[s] = {}
            for a in range(2006, self.date.year+1):
                self.listes[s][a] = les_mois.copy()
        self.sites = {} # les wikipedia étranger visités
        self.gros_suivi = [] # page de suivi grosse, contenu à transférer ?
        
    def __str__(self):
        r  = u"== Rapport d'exécution ==\n"
        r += u'* Nb de pages supprimées: %i\n' % self.stats['suppr']
        r += u'* Nb de traductions closes: %i\n' % self.stats['cloture']
        r += u'* Nb de {{Traduit de}} ajoutés: %i\n' % self.stats['traduitde']
        r += u"\nPage de suivi trop grande (les supprimer ?)\n"
        for a in self.gros_suivi:
            r += u"* [[%s]]\n" % a
        return r

    def retirer_le_modele_Traduction(self, page):
        """ Retire le {{Traduction}} d'une page
        """
        ns = page.namespace()
        if ns == 2 or ns == 3:
            pywikibot.output('Page utilisateur %d (retirer_modele) -> exit : %s' % (ns, b.title()))
            return
        text = self.re_trad.sub(r'', page.text)
        if text != page.text:
            page.text = text
            BeBot.save(page, commentaire=self.resume+u' : Retrait du modèle {{Traduction}}', minor=True, debug=self.debug)
        
    def suppr_mod(self, b, titres):
        ns = b.namespace()
        if ns == 2 or ns == 3:
            #pywikibot.output('Page utilisateur %d (suppr_mod) -> exit : %s' % (ns, b.title()))
            return
        self.retirer_le_modele_Traduction(b) # si traduction active
        for a in re.finditer(self.re_appel, b.text):
            trouve = a.group(1).encode('ascii', 'ignore')
            if trouve in titres:
                c = b.text[:a.start()] + b.text[a.end():]
                #BeBot.diff(b.text, c)
                b.text = c
        BeBot.save(b, commentaire=self.resume+u' : Traduction abandonnée', debug=self.debug)

    def supprimer(self, page):
        """ Supprime la page et nettoie les pages liées
        """
        t = page.title().encode('ascii', 'ignore')
        titres = [ t ]
        titres.append(t.replace('Discussion:', 'Discuter:'))
        for b in page.backlinks(filterRedirects=True): # On trouve les différents noms de la page
            t = b.title().encode('ascii', 'ignore')
            titres.append(t)
            titres.append(t.replace('Discussion:', 'Discuter:'))
        # PdDis
        disc = pywikibot.Page(self.site, page.title().replace('/Traduction', ''))
        if disc.exists(): # Nettoyage de PdDis
            self.suppr_mod(disc, titres)

        for b in page.embeddedin(): # nettoyage des inclusions
            self.suppr_mod(b, titres)
        for b in page.backlinks(followRedirects=True): # Nettoyage des redirections
            if b.isRedirectPage():
                BeBot.delete(b, self.resume+u" : Redirection d'une traduction abandonnée", debug=self.debug)
                self.stats['suppr'] += 1

        #taille = BeBot.taille_page(page, 1) # < 2800
        #taille = 7777
        taille = 0
        m = self.re_discus.search(page.text)
        if m:
            taille = len(m.group(1))
        if taille < 260:
            BeBot.delete(page, self.resume+u' : Traduction abandonnée', debug=self.debug)
            self.stats['suppr'] += 1
        else:
            pywikibot.output(u"><> Discussion détectée sur : http://fr.wikipedia.org/wiki/%s -- taille:%d" % (page.title(), taille))
            self.gros_suivi.append(page.title())
        
    def clore_traduction(self, page):
        """ Clôt une traduction
        """
        #pywikibot.output(u"&&& clore : %s" % page.title())
        page.text = self.re_statut.sub('|status=5', page.text)
        com = self.resume
        BeBot.save(page, commentaire=com, debug=self.debug)
        self.retirer_le_modele_Traduction(BeBot.togglePageTrad(page))
        self.stats['cloture'] += 1

    def traduit_de(self, page):
        """ Vérifie et ajoute le {{Traduit de}} à la page de discussion
        """
        disc = pywikibot.Page(self.site, page.title().replace('/Traduction', ''))
        if disc.isRedirectPage():
            disc = disc.getRedirectTarget()
        m = self.re_traduitde.search(disc.text)
        if not m:
            n = self.re_suivi.search(page.text) # Récupération des infos de traduction
            if n:
                a = BeBot.modeletodic(n.group(0))
                if not a.has_key(1) or not a.has_key(2):
                    pywikibot.warning(u";;; Impossible de trouver le nom ou la langue d'origine pour %s" % page.title())
                    return False
                langue = a[1]
                article = a[2].replace('_', ' ')
                if 'status' in a:
                    statut = a['status']
                else:
                    pywikibot.output(";;; Statut introuvable -> on passe")
                    pywikibot.output(a)
                    return False
                if statut == "1":
                    pywikibot.output(";;; Statut 'Demande' -> ne pas ajouter le {{Traduit de}}")
                    return True
                plus = u''
                if a.has_key(u'oldid') and a['oldid'] != u'' and a['oldid'] != u'830165' :
                    # On utilise le oldid pour retrouver la date
                    oldid = a['oldid']
                    if self.sites.has_key(langue):
                        sit = self.sites[langue]
                    else:
                        sit = pywikibot.Site(langue)
                        self.sites[langue] = sit
                    orig = pywikibot.Page(sit, article)
                    if orig.isRedirectPage():
                        orig = orig.getRedirectTarget()

                    date = u''
                    try:
                        for o in orig.fullVersionHistory():
                            revis = unicode(o[0])
                            if revis == oldid:
                                date = o[1]
                                break;
                    except: #Nopage
                        pywikibot.warning(u";;; Impossible de lire l'historique pour %s:%s" % (langue, orig.title()))
                        return False
                    #pywikibot.output(date.__str__()[8:10])
                    date = date.__str__()
                    if date != u'':
                        jour  = date[8:10].lstrip('0')
                        mois  = date[5:7].lstrip('0')
                        annee = date[0:4]
                        plus = u"|%s/%s/%s|%s" % (jour, mois, annee, oldid)
                    else:
                        pywikibot.warning(u"Ne peut dater une ancienne révision de %s" % page.title())
                appel = u'{{Traduit de|%s|%s%s}}\n' % (langue, article, plus)
                #BeBot.diff(disc.text, appel + disc.text)
                disc.text = appel + disc.text
                BeBot.save(disc, commentaire=self.resume+u' : Ajout du bandeau de licence', debug=self.debug)
                self.stats['traduitde'] += 1
                return True
            else:
                pywikibot.warning(u'Impossible de trouver les infos de traduction pour %s' % page.title())
        return True
        
    def run(self):
        if self.debug:
            pywikibot.warning(u"== Mode débuggage actif ; aucunes modifications effectuées ==")
        parannee = pywikibot.Category(self.site, u"Catégorie:Traduction par année")
        for c in parannee.subcategories(recurse=False): #parcours des traductions par année
            for p in c.articles(content=False, total=25): # Pour chaque traduction
                pywikibot.output(">>>>> %s <<<<<" % p.title())
                td = self.traduit_de(p)
                #self.clore_traduction(p)
                if td: # erreur grave à vérifier
                    self.supprimer(p)

def main():
    site = pywikibot.getSite()
    if BeBot.blocage(site):
        sys.exit(7)
    debug = False
    if len(sys.argv) == 2 and sys.argv[1] == "debug":
        debug = True
    elif len(sys.argv) != 1:
        pywikibot.warning(u"Nombre de paramètres incorrectes")
        sys.exit(1)
    site.login()
    tm = Trad_maintenance(site, debug)
    tm.run()
    pywikibot.output(tm)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
