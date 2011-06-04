#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class TraduitDe:
    """ Traduit de
        Reformatte les modèles "Traduit de"
    """
    def __init__(self, site):
        self.site = site
        self.TD = pywikibot.Page(self.site, u'Modèle:Traduit de')
        self.tdRE = re.compile("\{\{Traduit de\|([^\}]+)\}\}", re.LOCALE|re.IGNORECASE|re.UNICODE)
        self.oldidRE = re.compile("^\d+$", re.LOCALE|re.UNICODE|re.MULTILINE)
        self.sites = {} # Mémorisation des sites explorés

    def dateRev(self, page, lang, title, oldid):
        """ Donne la date de la version d'une page
        """
        if lang not in self.sites.keys():
            self.sites[lang] = pywikibot.Site(lang)
        p = pywikibot.Page(self.sites[lang], title)
        r = u''
        try:
            q = p.getVersionHistory()
        except:
            pywikibot.output(u'* [[%s]] %s:%s' % (page.title(), lang, title))
            # TODO : prendre la redirection, ou l'interwiki de page
            return r
        oldid = int(oldid)
        for i in q:
            if i[0] == oldid:
                r = i[1]
                break
        return r

    def run(self):
        founds = {}
        pg = pywikibot.pagegenerators.ReferringPageGenerator(self.TD, followRedirects=False, withTemplateInclusion=True, onlyTemplateInclusion=False, step=150, total=50000, content=False)
        #pg = pywikibot.pagegenerators.LinkedPageGenerator(pywikibot.Page(self.site, u'Utilisateur:BeBot/Test'), step=None, total=None, content=True) # Page de test
        for p in pywikibot.pagegenerators.DuplicateFilterPageGenerator(pg):
            if p.isTalkPage():
                c = self.tdRE.search(p.text)
                if c:
                    d = c.group(1)
                    a = d.split('|')
                    if len(a) > 2:
                        if self.oldidRE.match(a[2]):
                            date = self.dateRev(p, a[0], a[1], a[2])
                            if not date == u'':
                                date = datetime.date(int(date[0:4]),int(date[5:7]),int(date[8:10]))
                                fr = u''
                                if len(a) > 4:
                                    fr = u'|' + u'|'.join(a[3:5])
                                td = u'{{Traduit de|%s|%s|%s|%s%s}}' % (a[0], a[1].strip(' '), date.strftime("%d/%m/%Y"), a[2], fr)
                                founds[p.title()] = td
                                #pywikibot.showDiff(p.text, self.tdRE.sub(td, p.text))
                                p.text = self.tdRE.sub(td, p.text)
                                p.save(comment=u'Ajout automatique du paramètre 'date' au modèle "Traduit de" ([[Discussion modèle:Traduit de#Date de traduction sans oldid]])', minor=True, async=True)
        #for k in founds.iterkeys():
        #    pywikibot.output(k)
        pywikibot.output(u'Total : %i' % len(founds))

def main():
    site = pywikibot.getSite()
    td = TraduitDe(site)
    td.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
