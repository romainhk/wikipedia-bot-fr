#!/usr/bin/python
# -*- coding: utf-8  -*-
__version__ = 'PreparationWikimag 20100705'
import re, datetime
from wikipedia import *

def moistoint(mois):
    " Convertit une chaîne de caractètre correspondant à un mois, en un entier i (1≤i≤12). "
    mois = mois.lower()
    if mois == 'janvier':     return 1
    elif mois == u'février':  return 2
    elif mois == 'mars':      return 3
    elif mois == 'avril':     return 4
    elif mois == 'mai':       return 5
    elif mois == 'juin':      return 6
    elif mois == 'juillet':   return 7
    elif mois == u'août':     return 8
    elif mois == 'septembre':  return 9
    elif mois == 'octobre':    return 10
    elif mois == 'novembre':   return 11
    elif mois == u'décembre':  return 12
    else:
        wikipedia.output(u'Mois « %s » non reconnu' % mois)
    return 0

class PreparationWikimag:
    """ Préparation d'un wikimag : 
        annonces, images et promotions AdQ/BA de la semaine courante.
    """
    def __init__(self, site):
        self.site = site
        self.annonces = []
        self.adq = []
        self.ba = []
        self.inconnu = []

        #Dates
        self.date = datetime.date.today()
        unjour = datetime.timedelta(days=1)
        jour = self.date.weekday()
        while jour != 0:
            self.date = self.date - unjour
            jour = self.date.weekday()
        self.lasemaine = self.date.strftime("%A %e %B %Y")
        self.date_fin = self.date + datetime.timedelta(days=7)

        self.jours = []
        jour = self.date
        while jour != self.date_fin:
            self.jours.append(jour)
            jour = jour + unjour

        self.resume = u'BeBot : Préparation du wikimag débutant le ' + self.lasemaine
        wikipedia.setAction(self.resume)
        if self.date_fin.month == u'janvier':
            wikipedia.output(self.date.strftime("%Y/%m/%d")+u" : Attention, certaines données de l'année %i ne seront pas prises en compte" % int(self.date_fin.year)-1)
        self.articleRE = re.compile("\* [^\{]*\{\{a-label\|([^\|\}]+)\}\}")

    def __str__(self):
        """ Page à publier 
        """
        resultat = u"''Préparation du [[Wikipédia:Wikimag|wikimag]] allant du " \
            + self.lasemaine + u" au " + self.date_fin.strftime("%A %e %B %Y") + u".''\n"

        resultat += u"\n== Annonces ==\n"
        for a in self.annonces:
            resultat += a + u'\n'

        resultat += u"\n== Images du jour ==\n"
        for i in self.jours:
            resultat += u'* {{m|Wikipédia:Image du jour/' + str(int(i.strftime("%d"))) \
                    + i.strftime(" %B %Y") + u"|namespace=Wikipédia}}\n"

        resultat += u"\n== Labels =="
        resultat += u"\n=== AdQ ===\n"
        for a in self.adq:
            resultat += u'* [[' + a + u']]\n'
        resultat += u"\n=== BA ===\n"
        for a in self.ba:
            resultat += u'* [[' + a + u']]\n'

        if len(self.inconnu) > 0:
            resultat += u"\n=== Inconnus ===\n"
            for a in self.inconnu:
                resultat += u'* [[' + a + u']]\n'
        return resultat

    def page_ligne_par_ligne(self, nompage):
        """ Lit une wikipage ligne par ligne
        """
        try:
            page = wikipedia.Page(self.site, nompage).get()
        except pywikibot.exceptions.NoPage:
            wikipedia.output(u"La page « %s » n'est pas accessible." % nompage)
            return
        for ligne in page.split("\n"):
            yield ligne

    def articles_promus(self, nompage, RE):
        """ Traitement pour les articles promus
        * listage des articles à vérifier
        * tri par date
        Paramètres:
            -> nompage : nom de la page contenant la liste des promotions
            -> RE : expression rationnelle pour reconnaitre le modèle indiquant
                une promotion, ainsi que la date
        """
        mois = [ self.date.month ]
        if self.date.month != self.date_fin.month: mois.append(self.date_fin.month)
        articles = []
        r = []
        moisRE = re.compile("=== *([^\s\d=]+) *===", re.LOCALE)

        # Listage des articles des mois courants
        for ligne in self.page_ligne_par_ligne(nompage):
            m = moisRE.search(ligne)
            if m:                                   # Changement de mois
                mc = moistoint(m.group(1))
                if mc not in mois: mc = ""
                continue
            a = self.articleRE.match(ligne)
            if a:
                if mc != "":                    # Si on a un mois valide
                    articles.append( a.group(1) )

        # Vérification des dates exactes
        dateRE = re.compile("(\d{1,2}) (\w{3,9}) (\d{2,4})", re.LOCALE)
        for a in articles:
            try:
                page = wikipedia.Page(self.site, a).get()
            except pywikibot.exceptions.NoPage:
                self.inconnu.append(a)
                continue
            m = RE.search(page)
            if m:
                date = m.group(1)
                d = dateRE.search(date)
                if d:
                    jour = d.group(1)
                    mois = moistoint(d.group(2))
                    annee = d.group(3)
                    date_adq = datetime.date(day=int(jour), month=mois, year=int(annee))
                    if not (self.date > date_adq) and not (self.date_fin <= date_adq):
                        r.append(a)
                else:
                    self.inconnu.append(a)
        return r

    def run(self):
        wikipedia.output(u"Préparation du wikimag débutant le " + self.lasemaine)
           
        # Annonces
        moisRE = re.compile("==== *(\w+) *====", re.LOCALE)
        annonceRE = re.compile("\{\{[aA]nnonce[^\|]*\|(\d+)\|")
        mois_courant = 0
        for ligne in self.page_ligne_par_ligne(u'Wikipédia:Annonces'):
            if re.match(r'== *Voir ', ligne): break     # Fin des annonces
            m = moisRE.search(ligne)
            if m:                                   # Changement de mois
                mois_courant = moistoint(m.group(1))
                continue
            a = annonceRE.match(ligne)
            if a:                                   # Une annonce
                val = int( re.sub(r'{{.*}}', '', a.group(1)) )
                date_annonce = datetime.date(day=val, month=mois_courant, year=self.date.year)
                if self.date <= date_annonce < self.date_fin:
                    self.annonces.append(ligne)

        # AdQ, BA
        modeleRE = re.compile("\{\{[aA]rticle de qualit[^\}]*\| *date=([^\|\}]+)", re.LOCALE)
        self.adq= self.articles_promus(u'Wikipédia:Articles de qualité/Justification de leur promotion/'+str(self.date.year), modeleRE)
        modeleRE = re.compile("\{\{[bB]on article[^\}]*\| *date=([^\|\}]+)", re.LOCALE)
        self.ba = self.articles_promus(u'Wikipédia:Bons articles/Justification de leur promotion/'+str(self.date.year), modeleRE)


def main():
    site = wikipedia.getSite()
    pw = PreparationWikimag(site)
    pw.run()

    page_resultat = wikipedia.Page(site, u'Utilisateur:BeBot/Préparation Wikimag')
    page_resultat.put(unicode(pw))

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
