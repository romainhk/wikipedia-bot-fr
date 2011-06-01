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
        #self.tdRE = re.compile("\{\{Traduit de\|\w{2,5}(\|[^\|\}]*)*\}\}", re.LOCALE|re.IGNORECASE)
        self.oldidRE = re.compile("^\d+$", re.LOCALE|re.UNICODE|re.MULTILINE)
        self.sites = {}

    def dateRev(self, page, lang, title, oldid):
        if lang not in self.sites.keys():
            self.sites[lang] = pywikibot.Site(lang)
        p = pywikibot.Page(self.sites[lang], title)
        r = u''
        pywikibot.output(u'=== %s' % p.title())
        try:
            q = p.getVersionHistory()
        except:
            pywikibot.output(u'impossible de récupérer la page %s:%s' % (lang, title))
            # TODO : prendre la redirection , ou l'interwiki de page
            return r
        for i in q:
            if i[0] == oldid:
                r = i[1]
        return r

    def run(self):
        founds = {  u'+2' : 0,  u'-2' : 0,  u'match' : 0 }
        pg = pywikibot.pagegenerators.ReferringPageGenerator(self.TD, followRedirects=False, withTemplateInclusion=True, onlyTemplateInclusion=False, step=100, total=1000, content=False)
        for p in pywikibot.pagegenerators.DuplicateFilterPageGenerator(pg):
            if p.isTalkPage():
                c = self.tdRE.search(p.text)
                if c:
                    d = c.group(1)
                    a = d.split('|')
                    if len(a) > 2:
                        founds['+2'] += 1
                        if self.oldidRE.match(a[2]):
                            founds['match'] += 1
                            date = self.dateRev(p, a[0], a[1], a[2])
                            pywikibot.output(p.title() + u'\t: ' + str(a) + date)
                            if not date == u'':
                                date = datetime.date(int(date[0:4]),int(date[5:7]),int(date[8:10]))
                                pywikibot.output(u'{{Traduit de|%s|%s|%s|%s}}' % (a[0], a[1], date.strftime("%d/%m/%Y"), a[2]))
                        else:
                            #pywikibot.output(u'## '+p.title() + u'\t: ' + str(a))
                            pass
                    else:
                        founds['-2'] += 1
        pywikibot.output(u"-2:%i, +2:%i, match:%i" % (founds['-2'], founds['+2'], founds['match']))

def main():
    site = pywikibot.getSite()
    td = TraduitDe(site)
    td.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
