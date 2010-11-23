#!/usr/bin/python
# -*- coding: utf-8  -*-
#$ -m ae
import re, datetime, locale
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

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
        self.lasemaine = unicode(self.date.strftime("%A %e %B %Y"), "utf-8")
        self.date_fin = self.date + datetime.timedelta(days=7)

        self.jours = []
        jour = self.date
        while jour != self.date_fin:
            self.jours.append(jour)
            jour = jour + unjour

        self.resume = u'BeBot : Préparation du wikimag débutant le ' + self.lasemaine
        pywikibot.setAction(self.resume)
        if self.date_fin.month == u'janvier':
            pywikibot.output(self.date.strftime("%Y/%m/%d")+u" : Attention, certaines données de l'année %i ne seront pas prises en compte" % int(self.date_fin.year)-1)
        self.articleRE = re.compile("\* [^\{]*\{\{a-label\|([^\|\}]+)\}\}")

    def __str__(self):
        """ Page à publier 
        """
        resultat = u"''Préparation du [[Wikipédia:Wikimag|wikimag]] allant du " \
            + self.lasemaine + u" au " + unicode(self.date_fin.strftime("%A %e %B %Y"), "utf-8") + u".''\n"

        resultat += u"\n== Annonces ==\n"
        for a in self.annonces:
            resultat += a + u'\n'

        resultat += u"\n== Images du jour ==\n"
        for i in self.jours:
            resultat += u'* {{m|Wikipédia:Image du jour/' + str(int(i.strftime("%d"))) \
                    + unicode(i.strftime(" %B %Y"), "utf-8") + u"|namespace=Wikipédia}}\n"

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
        return resultat+u'\n'

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
        for ligne in BeBot.page_ligne_par_ligne(self.site, nompage):
            m = moisRE.search(ligne)
            if m is not None:                     # Changement de mois
                mc = BeBot.moistoint(m.group(1))
                if mc not in mois: mc = ""
                continue
            a = self.articleRE.match(ligne)
            if a is not None:
                if mc != "":                    # Si on a un mois valide
                    articles.append( a.group(1) )

        # Vérification des dates exactes
        dateRE = re.compile("(\d{1,2}) ([^0-9\|\} ]{3,9}) (\d{2,4})", re.LOCALE)
        for a in articles:
            try:
                page = pywikibot.Page(self.site, a).get()
            except pywikibot.exceptions.IsRedirectPage:
                page = pywikibot.Page(self.site, a).getRedirectTarget().get()
            except pywikibot.exceptions.NoPage:
                self.inconnu.append(a)
                continue
            m = RE.search(page)
            if m is not None:
                date = m.group(1)
                d = dateRE.search(date)
                if d is not None:
                    jour = d.group(1)
                    mois = BeBot.moistoint(d.group(2))
                    annee = d.group(3)
                    date_adq = datetime.date(day=int(jour), month=mois, year=int(annee))
                    if not (self.date > date_adq) and not (self.date_fin <= date_adq):
                        r.append(a)
                    #else:
                    #    pywikibot.output("Date %s en dehors de la plage %s - %s" % (d.group(), unicode(self.date.strftime("%e %B %Y"), "utf-8"), unicode(self.date_fin.strftime("%e %B %Y"), "utf-8") ))
                else:
                    self.inconnu.append(a)
        return r

    def run(self):
        pywikibot.output(u"Préparation du wikimag débutant le " + self.lasemaine)
           
        # Annonces
        moisRE = re.compile("==== *(.+) *====", re.LOCALE)
        annonceRE = re.compile("\{\{[aA]nnonce[^\|]*\|(\d+)\|")
        mois_courant = int(self.date.strftime("%m"))
        for ligne in BeBot.page_ligne_par_ligne(self.site, u'Wikipédia:Annonces'):
            if re.match(r'== *Voir ', ligne): break     # Fin des annonces
            m = moisRE.search(ligne)
            if m is not None:                           # Changement de mois
                mois_courant = BeBot.moistoint(m.group(1))
                continue
            a = annonceRE.match(ligne)
            if a is not None:                           # Une annonce
                val = int( re.sub(r'{{.*}}', '', a.group(1)) )
                date_annonce = datetime.date(day=val, month=mois_courant, year=self.date.year)
                if self.date <= date_annonce < self.date_fin:
                    self.annonces.append(ligne)

        # AdQ, BA
        modeleRE = re.compile("\{\{[aA]rticle de qualit[^\}]*\| *date *=([^\|\}]+)", re.LOCALE)
        self.adq= self.articles_promus(u'Wikipédia:Articles de qualité/Justification de leur promotion/%i' \
                % self.date.year, modeleRE)
        modeleRE = re.compile("\{\{[bB]on article[^\}]*\| *date *=([^\|\}]+)", re.LOCALE)
        self.ba = self.articles_promus(u'Wikipédia:Bons articles/Justification de leur promotion/%i' \
                % self.date.year, modeleRE)

def main():
    site = pywikibot.getSite()
    pw = PreparationWikimag(site)
    pw.run()

    page_resultat = pywikibot.Page(site, u'Utilisateur:BeBot/Préparation Wikimag')
    page_resultat.put(unicode(pw))

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
