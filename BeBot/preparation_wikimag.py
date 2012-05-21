#!/usr/bin/python
# -*- coding: utf-8  -*-
#$ -m ae
import re, datetime, locale
import BeBot
import pywikibot
from pywikibot import pagegenerators, catlib
locale.setlocale(locale.LC_ALL, '')

class PreparationWikimag:
    """ Préparation d'un wikimag : 
        annonces, images, promotions AdQ/BA de la semaine courante ; alerte si pas de mag.
        TODO : problème de reconnaissance des dates :
            {{Article de qualité|...|date=1{{er}} février 2011}}
    """
    def __init__(self, site):
        self.site = site
        self.annonces = []
        self.adq = []
        self.ba = []
        self.propositions = []
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
            resultat += u'* {{a-label|' + a + u'}}\n'
        resultat += u"\n=== BA ===\n"
        for a in self.ba:
            resultat += u'* {{a-label|' + a + u'}}\n'
        resultat += u"\n=== Propositions ===\n"
        for a,b in self.propositions:
            resultat += u'* {{a-label|' + a + u'}} '+ b + u'\n'

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
        semRE = re.compile("^; Semaine du \d+ .*?au (\d+) (.+?) (\d{4})", \
                re.LOCALE|re.MULTILINE)
        articles = []
        extremum = self.date_fin - datetime.timedelta(days=1)
        cetteSemaine = unicode(extremum.strftime("%e#%B#%Y"))
        trouve = False
        for ligne in BeBot.page_ligne_par_ligne(self.site, nompage):
            s = semRE.search(ligne)
            if s is not None:              # Changement de semaine
                fin = s.group(1)+u'#'+s.group(2)+u'#'+s.group(3)
                if fin == cetteSemaine and not trouve:
                    trouve = True
                else:
                    return articles    # Abandon au premier changement
            elif trouve:
                s = RE.search(ligne)
                if s is not None:
                    icone = u''
                    if len(s.groups()) >= 2 and s.group(2) is not None:
                        icone = s.group(2)
                    articles.append([s.group(1), icone])
        return articles    # Impossible ; en cas de foirage complet

    def verif_feneantise(self):
        """ Prévient les rédacteurs si le mag n'a même pas été commencé !
        """
        if not self.date.strftime("%w") == 0:
            return False        # Alerte uniquement le dimanche
        semaine = self.date.strftime("%W").lstrip('0')
        annee = self.date.year
        num = u"%s/%s" % (annee, semaine)
        msg  = u"\n\n== Wikimag - Semaine %s ==\n" % semaine
        msg += u"Attention, le [[WP:WM|wikimag]] ''[[Wikipédia:Wikimag/%s|de cette semaine]]'' n'est pas encore rédigé. Dépéchez vous ! (Aide: [[Utilisateur:BeBot/Préparation Wikimag]]) ~~~~\n" % num
        msg += u"\n{{Petit|Ce message a été déposé automatiquement grâce à [[:Catégorie:Utilisateur rédacteur Wikimag]]}}" # A supprimer un jour

        wm = pywikibot.Page(self.site, u"Wikipédia:Wikimag/%s" % num)
        #pywikibot.output(BeBot.taille_page(wm, 1))
        #NB: Wikipédia:Wikimag/pre fait 522 signes
        if not wm.exists() or BeBot.taille_page(wm, 1) < 566 :
            resume = u"Wikimag : alerte rédaction"
            redac = []
            cat = catlib.Category(self.site, u'Utilisateur rédacteur Wikimag')
            cpg = pagegenerators.CategorizedPageGenerator(cat, recurse=False)
            for r in cpg:
                can = r.title().split('/')
                if len(can) > 0:
                    can = can[0]
                redacteur = pywikibot.Page(self.site, can)
                if not redacteur.isTalkPage():
                    redacteur = redacteur.toggleTalkPage()
                if redacteur.isRedirectPage():
                    redacteur = redacteur.getRedirectTarget()
                # Avertissement avec dédoublonnage
                if not redacteur in redac:
                    redac.append(redacteur)
                    pywikibot.output(redacteur.title())
                    redacteur.text += msg
                    try:
                        redacteur.save(comment=resume, minor=False, async=True)
                    except pywikibot.Error, e:
                        pywikibot.warning(u"Pas d'alerte pour %s" % redacteur.title(withNamespace=True) )

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
        # Propositions
        modeleRE = re.compile("^\* \d+ : \{\{Sous-page:a2\|Discuter\|([^\|\}]+)\|.+?\}\}.*?(\{\{Icône wikiconcours\|.*?\}\})?.*?$", re.LOCALE|re.MULTILINE)
        self.propositions  = self.articles_propositions( \
                u'Wikipédia:Contenus de qualité/Propositions', modeleRE)
        self.propositions += self.articles_propositions( \
                u'Wikipédia:Bons articles/Propositions', modeleRE)

        self.verif_feneantise()

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
