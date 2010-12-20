#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class MailWikimag:
    """ Mail Wikimag
        Publie une version mail du wikimag
    """
    def __init__(self, site):
        self.site = site
        self.tmp = u'Utilisateur:BeBot/MailWikimag'
        self.mailinglist = u''
        self.modele_de_presentation = u'Utilisateur:Romainhk/Souspage2'
        self.date = datetime.date.today()
        self.mag = pywikibot.Page(site, u'Wikipédia:Wikimag/%s' % \
                unicode(self.date.strftime("%Y/%W"), "utf-8"))

    def run(self):
        # Préparation du contenu du mail
        modele = re.compile("\{\{[cC]omposition wikimag", re.LOCALE)
        pagetmp = pywikibot.Page(self.site, self.tmp)
        pagetmp.text = modele.sub(u'{{subst:%s|' % self.modele_de_presentation, self.mag.text)
        try:
            pagetmp.save(comment=u'Préparation du mail pour le Wikimag', minor=False)
        except:
            pywikibot.error(u"Impossible d'effectuer la substitution")
            sys.exit(2)
        #pywikibot.output(pagetmp._textgetter())

        pagetmp = pywikibot.Page(self.site, self.tmp)
        #pagetmp.text = u'{{annonces|4|bonjour àààà.}}\n[[Image:Salut.jpg|thumb|24px|AAAAAAA]]\n'
        #pagetmp.text += u'[http://fr.planet.wikimedia.org/ Planète]\n[http://meta.wikimedia.org]\n'
        #pagetmp.text += u'[[Nord]]\n[[Utilisateur:BeBot|Bebot]]'
        #Annonces
        r = re.compile(u"\{\{[aA]nnonces\|(\d+)\|([^\|\]]+)\}\}", re.LOCALE)
        pagetmp.text = r.sub(r'* \1 : \2', pagetmp.text)
        #Images
        r = re.compile(u"\[\[([iI]mage|[fF]ile|[fF]ichier):[^\]]+\]\]\s*", re.LOCALE)
        pagetmp.text = r.sub(r'', pagetmp.text)
        #Liens externes
        r = re.compile(u"\[(http:[^\] ]+) ([^\]]+)\]", re.LOCALE)
        pagetmp.text = r.sub(r'\2 [\1]', pagetmp.text)
        r = re.compile(u"\[(http:[^\] ]+)\]", re.LOCALE)
        pagetmp.text = r.sub(r'\1', pagetmp.text)
        #Liens internes
        #Pas d'interwiki, ni d'interlangue
        r = re.compile(u"\[\[([^\]\|]+)\|([^\]]+)\]\]", re.LOCALE)
        pagetmp.text = r.sub(r'\2 (http:/fr.wikipedia.org/wiki/\1)', pagetmp.text)
        r = re.compile(u"\[\[([^\]]+)\]\]", re.LOCALE)
        pagetmp.text = r.sub(r'http:/fr.wikipedia.org/wiki/\1', pagetmp.text)

        # Publication du mail sur la ml
        pywikibot.output(pagetmp.text)

def main():
    site = pywikibot.getSite()
    mw = MailWikimag(site)
    mw.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
