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
        self.tdRE = re.compile("\{\{Traduit de\|([^\}]+)\}\}", re.LOCALE|re.IGNORECASE)
        #self.tdRE = re.compile("\{\{Traduit de\|\w{2,5}(\|[^\|\}]*)*\}\}", re.LOCALE|re.IGNORECASE)
        self.oldidRE = re.compile("^\d+$", re.LOCALE|re.UNICODE|re.MULTILINE)

    def dateRev(self, lang, page, oldid):
        s = pywikibot.site.BaseSite(lang)
        p = pywikibot.Page(s, page)
        r = u''
        for i in p.getVersionHistory():
            if i[0] == oldid:
                r = i[1]
        return r

    def run(self):
        for p in pywikibot.pagegenerators.DuplicateFilterPageGenerator(pywikibot.pagegenerators.ReferringPageGenerator(self.TD, followRedirects=False, withTemplateInclusion=True, onlyTemplateInclusion=False, step=100, total=200, content=True)):
            if p.isTalkPage():
                c = self.tdRE.search(p.text)
                if c:
                    d = c.group(1)
                    a = d.split('|')
                    if len(a)>2:
                        if self.oldidRE.match(a[2]):
                            date = self.dateRev(a[0], a[1], a[2])
                            date = datetime.date(int(date[0:4]),int(date[5:7]),int(date[8:10]))
                            pywikibot.output(p.title() + u'\t: ' + str(a) + date)
                            pywikibot.output(u'{{Traduit de|%s|%s|%s|%s}}' % (a[0], a[1], date.strftime("%d/%m/%Y"), a[2]))
                        else:
                            #pywikibot.output(u'## '+p.title() + u'\t: ' + str(a))
                            pass
                    else:
                        #pywikibot.output(u'** '+p.title() + u'\t: ' + str(a))
                        pass

def main():
    site = pywikibot.getSite()
    td = TraduitDe(site)
    td.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
