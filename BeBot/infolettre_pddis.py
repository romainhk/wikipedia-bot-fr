#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Infolettre:
    """ Infolettre
        Publie une infolettre sur la page de discussion des abonnées (wikimag et RAW)
    """
    def __init__(self, site, infolettre, debug):
        self.site = site
        self.infolettre = infolettre
        self.debug = debug
        pywikibot.output("# Publication de l'infolettre %s" % self.infolettre)
        self.date = datetime.date.today()
        self.lundi = self.date - datetime.timedelta(days=self.date.weekday())
        self.lundi_pre = self.lundi - datetime.timedelta(weeks=1)
        self.semaine = self.lundi_pre.isocalendar()[1]
        self.annee = self.lundi_pre.isocalendar()[0]
        self.abn = {
                "wikimag" : u"Wikipédia:Wikimag/Abonnement",
                "raw"     : u"Wikipédia:Regards sur l'actualité de la Wikimedia/Inscription" }

    def adl(self, mag):
        """ (Avec le wikimag) Ajoute les adq/ba de la semaine à l'Atelier de Lecture
        """
        separation = u'<center><hr style="width:42%;" /></center>'

        split = re.compile("\|([\w \xe9]+?)=", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
        lien = re.compile("\[\[.*?\]\]", re.LOCALE|re.UNICODE)
        params = {  'adq': u'', u'propositions adq' : u'',
                    'ba' : u'', u'propositions ba'  : u'' } # Les paramètres du mag
        a = re.split(split, mag.text)
        for i in range(1, len(a), 2):
            #retrait des liens
            a[i] = lien.sub(r'', a[i])
            params[a[i].lower()] = a[i+1].rstrip('\n').strip(' ')

        lumiere = pywikibot.Page(self.site, u'Wikipédia:Atelier de lecture/Lumière sur...')
        #Retrait des a-label
        alabel = re.compile("\{\{[aA]-label\|([^\}\|]+).*?\}\}", re.LOCALE|re.UNICODE)
        params['adq'] = alabel.sub(r'[[\1]]', params['adq'])
        params['propositions adq'] = alabel.sub(r'[[\1]]', params['propositions adq'])
        params['ba']  = alabel.sub(r'[[\1]]', params['ba'])
        params['propositions ba'] = alabel.sub(r'[[\1]]', params['propositions ba'])
        propositions = params['propositions adq'] + u'\n' + params['propositions ba']
        #Ajout des icones
        icone = re.compile("^\* ", re.LOCALE|re.UNICODE|re.MULTILINE)
        params['adq'] = icone.sub(r'* {{AdQ|20px}} ', params['adq'])
        params['ba']  = icone.sub(r'* {{BA|20px}} ', params['ba'])
        lumiere.text = u'[[Fichier:HSutvald2.svg|left|60px]]\nLes articles labellisés durant la semaine dernière et les nouvelles propositions au label.{{Clr}}\n' \
                + u'\n{{colonnes|nombre=3|\n' + params['adq'] + u'\n}}\n' + separation \
                + u'\n{{colonnes|nombre=3|\n' + params['ba']  + u'\n}}\n' + separation \
                + u'\n{{colonnes|nombre=3|\n' + propositions  + u'\n}}\n' \
                + u'<noinclude>\n[[Catégorie:Wikipédia:Atelier de lecture|Lumière sur...]]\n</noinclude>'
        pywikibot.output(u"# Publication sur l'Atelier de lecture")
        BeBot.save(lumiere, commentaire=u'Maj hebdomadaire de la liste', debug=self.debug)

    def wikimag(self):
        """ Wikimag """
        mag = pywikibot.Page(self.site, u'Wikipédia:Wikimag/%s/%s' % (self.annee, self.semaine) )
        if not mag.exists():
            pywikibot.output("# Impossible de trouver l'infolettre à distribuer")
            return ""
        if mag.isRedirectPage():
            mag = mag.getRedirectTarget()
        numero = '???'
        num = re.compile(u"\|numéro *= *(\d+)", re.LOCALE|re.UNICODE)
        m = num.search(mag.text)
        if m is not None:
            numero = m.group(1)

        self.resume = u'Demandez [[Wikipédia:Wikimag/%s/%s|Cannes Midi (n°%s)]]. Le tueur de Cannes frappe encore... 5 cents' \
                % (self.annee, self.semaine, numero)
        # Message à distribuer
        msg  = u"\n\n== Wikimag n°%s - Semaine %s ==\n" % (numero, self.semaine)
        msg += u"{{Wikimag message|%s|%s|%s}} ~~~~" % (numero, self.annee, self.semaine)
        # Travail pour l'atelier de lecture
        self.adl(mag)
        return msg

    def raw(self):
        """ Regards sur l'actualité de la Wikimedia """
        self.semaine = self.lundi.isocalendar()[1]
        self.resume = u"Regards sur l'actualité de la Wikimedia - semaine %s de %s" % (self.semaine, self.annee)
        msg  = u"\n\n== Regards sur l'actualité de la Wikimedia - Semaine %s ==\n" % (self.semaine)
        msg += u"{{Regards sur l'actualité de la Wikimedia/PdD|%s|%s}}\n~~~~" % (self.annee, self.semaine)
        return msg

    def rm_old(self, page):
        """ Supprime les anciens mag
        """
        if self.infolettre == u"wikimag":
            oldmag = re.compile("^== Wikimag (n.?\d+ )?- Semaine (\d+) ?==.*?^==", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
        else:
            return False

        for f in oldmag.finditer(page.text):
            if len(f.groups()) == 2:
                sem = int(f.group(2))
                if abs(int(self.semaine)-sem) > 1:
                    page.text = page.text.replace(f.group(0), '==')
                    # en cas de remplacement, on recommence pour être sûre qu'il n'y en ai pas d'autres à faire
                    self.rm_old(page)
        return True

    def newsboy(self, lecteur, msg, purge=True):
        """ Distribut l'infolettre
        """
        if lecteur.isRedirectPage():
            lecteur = lecteur.getRedirectTarget()
        if purge:
            self.rm_old(lecteur)
        lecteur.text += msg
        BeBot.save(lecteur, commentaire=self.resume, debug=self.debug)

    def run(self):
        if   self.infolettre == u"wikimag":
            msg = self.wikimag()
        elif self.infolettre == u"raw":
            msg = self.raw()
        else:
            pywikibot.output(u"Infolettre '%s' inconnue. Abandon." % self.infolettre)
            sys.exit(1)

        # Liste des abonnés
        r = re.compile(u"\*\* \{\{u\|(.+?)\}\}\s*(\{\{BeBot nopurge\}\})?", re.LOCALE|re.UNICODE|re.IGNORECASE)
        liste = [] # [ Nom d'utilisateur ; bool : purge des anciens ]
        for i in BeBot.page_ligne_par_ligne(self.site, self.abn[self.infolettre]):
            m = r.search(i)
            if m is not None:
                purge = True
                if m.group(2) is not None:
                    purge = False
                liste.append([m.group(1), purge])

        # Distribution
        if hasattr(self, "resume"):
            for l,p in liste:
                boiteauxlettres = pywikibot.Page(self.site, u"Utilisateur:"+l).toggleTalkPage()
                self.newsboy(boiteauxlettres, msg, p)

def main():
    site = pywikibot.getSite()
    if BeBot.blocage(site):
        sys.exit(7)
    if len(sys.argv) <= 1:
        pywikibot.output("Syntaxe: infolettre_pddis.py MAGAZINE [DEBUG]")
        sys.exit(1)
    debug = False
    nbarg = len(sys.argv)
    infolettre = ""
    for par in sys.argv:
        if par.lower() == "debug":
            debug = True
        else:
            lettre = sys.argv[1].lower()
    bw = Infolettre(site, lettre, debug)
    bw.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
