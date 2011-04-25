#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class BotWikimag:
    """ Bot Wikimag
        Publie le wikimag de la semaine sur la page de discussion des abonnées
    """
    def __init__(self, site):
        self.site = site
        self.date = datetime.date.today()
        self.lundi = self.date - datetime.timedelta(days=self.date.weekday())
        self.lundi_pre = self.lundi - datetime.timedelta(weeks=1)
        self.semaine = self.lundi_pre.strftime("%W").lstrip('0')

    def adl(self):
        """ Ajoute les adq/ba de la semaine à l'Atelier de Lecture
        """
        # Infos
        mag = pywikibot.Page(self.site, u'Wikipédia:Wikimag/%s/%s' % \
                (self.lundi_pre.strftime("%Y"), self.semaine) )
        split = re.compile("\|([\w \xe9]+?)=", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
        params = {} # Les paramètres du mag
        a = re.split(split, mag.text)
        for i in range(1, len(a), 2):
            params[a[i].lower()] = a[i+1].rstrip('\n').strip(' ')

        # Résultat
        lumiere = pywikibot.Page(self.site, u'Wikipédia:Atelier de lecture/Lumière sur...')
        """ Par ajout
        label = re.compile("== Adq ==([^={2}]*)", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
        lumiere.text = label.sub(r'== Adq ==\n%s\1' % params['adq'], lumiere.text)
        label = re.compile("== BA ==([^={2}]*)", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
        lumiere.text = label.sub(r'== BA ==\n%s\1' % params['ba'], lumiere.text)
        """
        icone = re.compile("^\* ", re.LOCALE|re.UNICODE|re.MULTILINE)
        params['adq'] = icone.sub(r'* {{AdQ|20px}} ', params['adq'])
        params['ba']  = icone.sub(r'* {{BA|20px}} ', params['ba'])
        lumiere.text = u'[[Fichier:HSutvald2.svg|left|60px]]\nLes articles labellisés durant la semaine dernière.{{Clr}}\n\n' \
                + u'<div style="height: 250px; overflow: auto; padding: 3px; border:1px solid #AAAAAA;" >\n' \
                + u'== Adq ==\n{{colonnes|nombre=3|\n' + params['adq'] + u'\n}}\n' \
                + u'\n== BA ==\n{{colonnes|nombre=3|\n' + params['ba'] + u'\n}}\n' \
                + u'</div>\n<noinclude>\n[[Catégorie:Wikipédia:Atelier de lecture|Lumière sur...]]\n</noinclude>'
        #print lumiere.text
        try:
            lumiere.save(comment=u'Maj de la liste par BeBot (%s)' % self.date.strftime("%e/%m/%Y"), minor=False, async=True)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de sauvegarder la liste des Adq/BA pour le Projet:Adl" )

    def newsboy(self, lecteur, msg):
        """ Distribut un magasine
        """
        lecteur = pywikibot.Page(self.site, u"Utilisateur:"+lecteur).toggleTalkPage()
        if lecteur.isRedirectPage():
            lecteur = lecteur.getRedirectTarget()
        # Donne le mag au lecteur
        lecteur.text = lecteur.text + msg
        try:
            lecteur.save(comment=u'Demandez Cannes Midi. Le tueur de Cannes frappe encore... 5 cents', minor=False, async=True)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de refourger le mag à %s" % lecteur.title(withNamespace=True) )

    def run(self):
        # Message à distribuer
        msg = u"\n== Wikimag - Semaine %s ==\n" % self.semaine
        msg += u"{{Wiki magazine|%s|%s}} ~~~~" % (self.lundi_pre.strftime("%Y"), self.semaine)

        r = re.compile(u"\*\* \{\{u\|(.+?)\}\}", re.LOCALE|re.UNICODE)
        liste = []
        for i in BeBot.page_ligne_par_ligne(self.site, u"Wikipédia:Wikimag/Abonnement"):
            m = r.search(i)
            if m is not None:
                liste.append(m.group(1))
        # Pour chaque abonné
        for l in liste:
            self.newsboy(l, msg)

        # Travail pour l'atelier de lecture
        self.adl()

def main():
    site = pywikibot.getSite()
    bw = BotWikimag(site)
    bw.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
