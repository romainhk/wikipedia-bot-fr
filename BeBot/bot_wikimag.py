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
        self.annee = self.lundi_pre.strftime("%Y")

        self.mag = pywikibot.Page(self.site, u'Wikipédia:Wikimag/%s/%s' % (self.annee, self.semaine) )
        self.numero = '???'
        num = re.compile(u"\|numéro *= *(\d+)", re.LOCALE|re.UNICODE)
        m = num.search(self.mag.text)
        if m is not None:
            self.numero = m.group(1)

        self.resume = u'Demandez [[Wikipédia:Wikimag/%s/%s|Cannes Midi (n°%s)]]. Le tueur de Cannes frappe encore... 5 cents' \
                % (self.annee, self.semaine, self.numero)

    def adl(self):
        """ Ajoute les adq/ba de la semaine à l'Atelier de Lecture
        """
        # Infos
        split = re.compile("\|([\w \xe9]+?)=", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
        params = {  'adq': u'', u'propositions adq' : u'',
                    'ba' : u'', u'propositions ba'  : u'' } # Les paramètres du mag
        a = re.split(split, self.mag.text)
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
        #Retrait des a-label
        alabel = re.compile("\{\{[aA]-label\|([^\}]+)\}\}", re.LOCALE|re.UNICODE)
        params['adq'] = alabel.sub(r'[[\1]]', params['adq'])
        params['propositions adq'] = alabel.sub(r'* [[\1]]', params['propositions adq'])
        params['ba']  = alabel.sub(r'[[\1]]', params['ba'])
        params['propositions ba'] = alabel.sub(r'* [[\1]]', params['propositions ba'])
        propositions = params['propositions adq'] + params['propositions ba']
        pywikibot.output(u"# Publication sur l'Atelier de lecture")
        #Ajout des icones
        icone = re.compile("^\* ", re.LOCALE|re.UNICODE|re.MULTILINE)
        params['adq'] = icone.sub(r'* {{AdQ|20px}} ', params['adq'])
        params['ba']  = icone.sub(r'* {{BA|20px}} ', params['ba'])
        lumiere.text = u'[[Fichier:HSutvald2.svg|left|60px]]\nLes articles labellisés durant la semaine dernière et les nouvelles propositions au label.{{Clr}}\n' \
                + u'\n{{colonnes|nombre=3|\n' + params['adq'] + u'\n}}\n' + u'<hr />' \
                + u'\n{{colonnes|nombre=3|\n' + params['ba']  + u'\n}}\n' + u'<hr />' \
                + u'\n{{colonnes|nombre=3|\n' + propositions  + u'\n}}\n' \
                + u'<noinclude>\n[[Catégorie:Wikipédia:Atelier de lecture|Lumière sur...]]\n</noinclude>'
        #pywikibot.output(lumiere.text)
        try:
            lumiere.save(comment=u'Maj hebdomadaire de la liste', minor=False, async=True)
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
            lecteur.save(comment=self.resume, minor=False, async=True)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de refourger le mag à %s" % lecteur.title(withNamespace=True) )

    def run(self):
        # Message à distribuer
        msg = u"\n== Wikimag n°%s - Semaine %s ==\n" % (self.numero, self.semaine)
        msg += u"{{Wiki magazine|%s|%s}} ~~~~" % (self.annee, self.semaine)

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
