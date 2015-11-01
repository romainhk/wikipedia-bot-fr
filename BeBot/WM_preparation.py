#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys, feedparser
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class PreparationWikimag:
    """ Préparation d'un wikimag : 
        annonces, images, promotions AdQ/BA de la semaine courante ; alerte si pas de mag.
    TODO: problème de reconnaissance des dates: {{Article de qualité|...|date=1{{er}} février 2011}}
    """
    def __init__(self, site):
        self.site = site
        self.annonces = []
        self.adq = []
        self.ba = []
        self.propositions_adq = []
        self.propositions_ba = []
        self.inconnu = []
        self.planete = []

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
        self.semaine = self.date.strftime("%W").lstrip('0')
        self.annee = self.date.year

        self.resume = 'BeBot : Préparation du wikimag débutant le ' + self.lasemaine
        pywikibot.setAction(self.resume)
        if self.date_fin.month == 'janvier':
            pywikibot.output(self.date.strftime("%Y/%m/%d")+" : Attention, certaines données de l'année %i ne seront pas prises en compte" % int(self.date_fin.year)-1)
        self.articleRE = re.compile("\* [^\{]*\{\{a-label\|([^\|\}]+)\}\}")

    def __str__(self):
        """ Page à publier 
        """
        resultat = "''Préparation du [[Wikipédia:Wikimag|wikimag]] allant du " \
            + self.lasemaine + " au " + self.date_fin.strftime("%A %e %B %Y") + ".''\n"

        resultat += "\n== Annonces ==\n"
        for a in self.annonces:
            resultat += a + '\n'

        resultat += "\n== Images du jour ==\n"
        for i in self.jours:
            resultat += '* {{m|Wikipédia:Image du jour/' + str(int(i.strftime("%d"))) \
                    + i.strftime(" %B %Y") + "|namespace=Wikipédia}}\n"

        resultat += "\n== Labels =="
        resultat += "\n=== AdQ ===\n"
        for a in self.adq:
            resultat += '* {{a-label|' + a + '}}\n'
        resultat += "\n; Propositions\n"
        for a,b in self.propositions_adq:
            resultat += '* {{a-label|' + a + '}} '+ b + '\n'

        resultat += "\n=== BA ===\n"
        for a in self.ba:
            resultat += '* {{a-label|' + a + '}}\n'
        resultat += "\n; Propositions\n"
        for a,b in self.propositions_ba:
            resultat += '* {{a-label|' + a + '}} '+ b + '\n'

        if len(self.inconnu) > 0:
            resultat += "\n=== Inconnus ===\n"
            for a in self.inconnu:
                resultat += '* [[' + a + ']]\n'

        resultat += "\n== Planète ==\n"
        for u, t in self.planete:
            # Remplacement des crochets dans le titre (pas un lien externe)
            t = t.replace('[', '&#x5B;').replace(']', '&#x5D;')
            resultat += '* [{url} {titre}]\n'.format(url=u, titre=t)

        return resultat+'\n'

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
                if mc != "":                      # Si on a un mois valide
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

    def articles_propositions(self, nompage, RE):
        """ Liste les propositions
            (cf. self.articles_promus() )
        """
        semRE = re.compile("^; Semaine du \d+ .*?au \{*(\d+)[^\s]* (.+?) (\d{4})", \
                re.LOCALE|re.MULTILINE)
        articles = []
        extremum = self.date_fin - datetime.timedelta(days=1)
        #cetteSemaine = unicode(extremum.strftime("%e#%B#%Y").strip(), errors='ignore')
        cetteSemaine = extremum.strftime("%e#%B#%Y").strip()
        trouve = False
        for ligne in BeBot.page_ligne_par_ligne(self.site, nompage):
            s = semRE.search(ligne)
            if s is not None:              # Changement de semaine
                mois = s.group(2).replace('û', '').replace('é', '')
                fin = s.group(1)+'#'+mois+'#'+s.group(3)
                if fin == cetteSemaine and not trouve:
                    trouve = True
                else:
                    return articles    # Abandon au premier changement
            elif trouve:
                s = RE.search(ligne)
                if s is not None:
                    icone = ''
                    if len(s.groups()) >= 2 and s.group(2) is not None:
                        icone = s.group(2)
                    articles.append([s.group(1), icone])
        return articles    # Impossible ; en cas de foirage complet

    def run(self):
        pywikibot.output("Préparation du wikimag débutant le " + self.lasemaine)
        # Annonces
        moisRE = re.compile("==== *(.+) *====", re.LOCALE)
        annonceRE = re.compile("\{\{[aA]nnonce[^\|]*\|(\d+)\|")
        mois_courant = int(self.date.strftime("%m"))
        for ligne in BeBot.page_ligne_par_ligne(self.site, 'Wikipédia:Annonces'):
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
        self.adq= self.articles_promus('Wikipédia:Articles de qualité/Justification de leur promotion/%i' \
                % self.date.year, modeleRE)
        modeleRE = re.compile("\{\{[bB]on article[^\}]*\| *date *=([^\|\}]+)", re.LOCALE)
        self.ba = self.articles_promus('Wikipédia:Bons articles/Justification de leur promotion/%i' \
                % self.date.year, modeleRE)
        # Propositions
        modeleRE = re.compile("^\* \d+ : \{\{Sous-page:a2\|Discuter\|([^\|\}]+)\|.+?\}\}.*?(\{\{Icône wikiconcours\|.*?\}\})?.*?$", re.LOCALE|re.MULTILINE)
        self.propositions_adq = self.articles_propositions( \
                'Wikipédia:Articles de qualité/Propositions', modeleRE)
        self.propositions_ba  = self.articles_propositions( \
                'Wikipédia:Bons articles/Propositions', modeleRE)
        # Planète wikimedia
        feed = feedparser.parse('http://fr.planet.wikimedia.org/atom.xml')
        for ent in feed.entries:
            if 'published_parsed' in ent:
                pub = ent.published_parsed
            else:
                pub = ent.updated_parsed
            if pub < self.date_fin.timetuple() and pub >= self.date.timetuple():
                for l in ent.links:
                    if l.rel == "alternate":
                        self.planete.append( (l.href, ent.title) )
                        break
        self.planete.reverse() # ordre chronologique

        if (BeBot.WM_verif_feneantise(self.site, self.semaine, self.annee) and self.date.strftime("%w") == 0):
            #NB: que le dimanche
            msg  = "\n\n== Wikimag - Semaine %s ==\n" % self.semaine
            msg += "Attention, le [[WP:WM|wikimag]] ''[[Wikipédia:Wikimag/%s|de cette semaine]]'' n'est pas encore rédigé. Dépéchez vous ! (Aide: [[Utilisateur:BeBot/Préparation Wikimag]]) ~~~~\n" % self.annee
            msg += "\n{{Petit|Ce message a été déposé automatiquement grâce à [[:Catégorie:Utilisateur rédacteur Wikimag]]}}" # A supprimer un jour
            BeBot.WM_prevenir_redacteurs(self.site, msg, resume)

def main():
    site = pywikibot.Site()
    if BeBot.blocage(site):
        sys.exit(7)
    pw = PreparationWikimag(site)
    pw.run()

    page_resultat = pywikibot.Page(site, 'Utilisateur:BeBot/Préparation Wikimag')
    page_resultat.text = pw
    BeBot.save(page_resultat, debug=False)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
