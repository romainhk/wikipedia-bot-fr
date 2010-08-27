# -*- coding: utf-8 -*-
"""
Maintenance of translation project.

This library is free software; you can redistribute it and/or
modify it under the terms of the MIT License.
See the LICENCE file
"""

import pywikibot
import pywikibot.data.api as api

import logging
logging.getLogger().setLevel(logging.INFO)

import re
from datetime import datetime

languages = [
        [ 'en', 'anglais',  "l'" ],
        [ 'de', 'allemand', "l'" ],
        [ 'pl', 'polonais', "le&nbsp;" ],
        [ 'ja', 'japonais', "le&nbsp;" ],
        [ 'nl', u'néerlandais', "le&nbsp;" ],
        [ 'it', 'italien',  "l'" ],
        [ 'pt', 'portugais',    "le&nbsp;" ],
        [ 'sv', u'suédois', "le&nbsp;" ],
        [ 'es', 'espagnol', "l'" ],
        [ 'ru', 'russe',    "le&nbsp;" ],
        [ 'zh', 'chinois',  "le&nbsp;" ],
        [ 'fi', 'finnois',  "le&nbsp;" ],
        [ 'no', u'norvégien',   "le&nbsp;" ],
        [ 'eo', 'esperanto',    "l'" ],
        [ 'lv', 'letton',   "le&nbsp;" ],
        [ 'sk', 'slovaque', "le&nbsp;" ],
        [ 'da', 'danois',   "le&nbsp;" ],
        [ 'cs', u'tchèque', "le&nbsp;" ],
        [ 'he', u'hébreu',  "l'" ],
        [ 'ca', 'catalan',  "le&nbsp;" ],
        [ 'id', u'indonésien',  "l'" ],
        [ 'hu', 'hongrois', "le&nbsp;" ],
        [ 'ro', 'roumain',  "le&nbsp;" ],
        [ 'uk', 'ukrainien',    "l'" ],
        [ 'tr', 'turc',     "le&nbsp;" ],
        [ 'sr', 'serbe',    "le&nbsp;" ],
        [ 'lt', 'lithuanien',   "le&nbsp;" ],
        [ 'sl', u'slovène',     "le&nbsp;" ],
        [ 'bg', 'bulgare',  "le&nbsp;" ],
        [ 'ko', u'coréen',  "le&nbsp;" ],
        [ 'et', 'estonien', "l'" ],
        [ 'te', u'télougou',    "le&nbsp;" ],
        [ 'hr', 'croate',   "le&nbsp;" ],
        [ 'ar', 'arabe',    "l'" ],
        [ 'gl', 'galicien', "le&nbsp;" ],
        [ 'nn', u'norvégien nynorsk', "le&nbsp;" ],
        [ 'th', u'thaï',    "le&nbsp;" ],
        [ 'fa', 'persan',   "le&nbsp;" ],
        [ 'el', 'grec moderne', "le&nbsp;" ],
        [ 'ms', 'malais',   "le&nbsp;" ],
        [ 'eu', 'basque',   "le&nbsp;" ],
        [ 'io', 'ido',      "l'" ],
        [ 'ka', u'géorgien',    "le&nbsp;" ],
        [ 'nap', 'napolitain',  "le&nbsp;" ],
        [ 'bn', 'bengali',  "le&nbsp;" ],
        [ 'is', 'islandais',    "l'" ],
        [ 'vi', 'vietnamien',   "le&nbsp;" ],
        [ 'simple', 'anglais simple', "l'" ],
        [ 'bs', 'bosnien',  "le&nbsp;" ],
        [ 'lb', 'luxembourgeois', "le&nbsp;" ],
        [ 'br', 'breton',   "le&nbsp;" ],
        [ 'la', 'latin',    "le&nbsp;" ],
        [ 'wa', 'wallon',   "le&nbsp;" ],
        [ 'wuu', 'wu',      "le&nbsp;" ]
    ]

cats = [[u'Article à traduire', 'Demande de traduction',        'Demandes', 'Demandes de traduction'],
        [u'Article en cours de traduction', 'Traduction en cours',  'En cours', 'Traductions en cours'],
        [u'Article à relire', u'Traduction à relire',           'A relire', u'Traductions à relire'],
        [u'Article en cours de relecture', u'Relecture en cours',   'En relecture', 'Relectures en cours'],
        [u'Traduction terminée', u'Traduction terminée',        u'Terminée', u'Traductions terminées']]

int2month = [u'placeholder_zero', u'janvier', u'février', u'mars', u'avril',
             u'mai', u'juin', u'juillet', u'août', u'septembre', u'octobre',
             u'novembre', u'décembre']
month2int = dict((month, i) for i, month in enumerate(int2month))

site = pywikibot.Site('fr', 'wikipedia')

pywikibot.setAction(u'Robot : Màj hebdomadaire des pages de suivi du Projet:Traduction')

#Résultats
bylang = {}
bystatus = {}

#RE
re_date = re.compile(u'\|\s*jour\s*=.*(?P<day>(?:(?<=\D)\d|\d{2}))\s*\|\s*mois\s*=\s*(?P<month>[\wéû]+)\s*\|\s*année\s*=\s*(?P<year>\d{4})')
re_lang = re.compile(u'\{\{(Translation/Information|Traduction/Suivi)\s*\|(?P<code>\w{2,8})\|')

def datecmp(x, y):
    """
        x, y are [datetime, Page] elements.
        Sort by date, let newer dates get first.
    """
    if x[0] < y[0]:
        return 1
    elif x[0] > y[0]:
        return -1
    else:
        return 0

def put_page(page, new):
    """
        Prints diffs between orginal and new (text), puts new text for page
    """
    pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                     % page.title())
    try:
        pywikibot.showDiff(page.get(), new)
    except pywikibot.NoPage:
        pywikibot.showDiff("", new)
    try:
        page.put(new, minorEdit=False)
    except pywikibot.EditConflict:
        pywikibot.warning(u'Skipping %s because of edit conflict'
                          % (page,))
    except pywikibot.SpamfilterError, e:
        pywikibot.warning(u'Cannot change %s because of blacklist entry %s'
                          % (page, e.url))
    except pywikibot.PageNotSaved, error:
        pywikibot.warning(u'Error putting page: %s' % error)
    except pywikibot.LockedPage:
        pywikibot.warning(u'Skipping %s (locked page)' % (page,))
    except pywikibot.ServerError, e:
        pywikibot.warning(u'Server Error : %s' % e)

def get_on_regexp(page, reg):
    """
       Load the page's text from the wiki and apply a regexp
    """
    try:
        text = page.get()
    except pywikibot.NoPage:
        pywikibot.output(u'Page %s not found' % page.title(asLink=True))
        return
    except pywikibot.IsRedirectPage:
        pywikibot.output(u'Page %s is a redirect' % page.title(asLink=True))
        return
    return reg.search(text)

#Init
for lang, x, y in languages:
    bylang[lang] = {}
    for cat, a, b, c in cats:
        bylang[lang][cat] = []

#Traitement
for item in cats:
    cat = item[0]
    pywikibot.output(u'Processing category "%s"...' % cat)
    bystatus[cat] = []
    cur_cat = pywikibot.Page(site, u'Catégorie:%s' % cat)
    gen = site.categorymembers(cur_cat, step=4900)
    gen = site.preloadpages(gen, groupsize=200)
    for page in gen:
        if (page.namespace() % 2) == 1 : # = espace de discussion
            match = get_on_regexp(page, re_date)
            if not match:
                pywikibot.warning(u'date not found on %s' % page.title(asLink=True))
                continue

            try:
                date = datetime(int(match.group('year')),
                    month2int[match.group('month')], int(match.group('day')))
            except KeyError:
                pywikibot.warning(u"month « %s » undefined on %s" % (match.group('month'), page.title(asLink=True)) )
                continue
            elem = [date, page]
            bystatus[cat].append(elem)
            lang = get_on_regexp(page, re_lang)
            if lang:
                if bylang.has_key(lang.group('code')):
                    bylang[lang.group('code')][cat].append(elem)
                else:
                    pywikibot.warning(u'wrong language on %s' % page.title(asLink=True) )
            else:
                pywikibot.warning(u'no langugage on %s' % page.title(asLink=True) )

# Okay, we now have two sorted collections containing the info we needed.
###############################
##### Pages-lang
for l in bylang.itervalues():
    for m in l.itervalues():
        m.sort(cmp=datecmp)
header_pattern = u'{{Translation/IntroLang|code langue=%s|langue=%s|article=%s}}'
LIMITE_CHAPITRE = 50
LIMITE_DEROULANT = 15
for code, nomlong, pre in languages:
    langpage = pywikibot.Page(site, u'Projet:Traduction/*/Lang/%s' % code)
    new_text = header_pattern % (code, nomlong, pre) + '\n\n'
    found = 0
    lengths = {}
    for item in cats:
        length = len(bylang[code][item[0]])
        lengths[item[0]] = length

    # Limitation du nombre de modèles affichés
    k = lengths.keys()
    v = lengths.values()
    while sum(v) > 90:
        m = max(v)
        ind = v.index(m)
        m = m*3/4
        v[ind] = m
        ind = k[ind]
        bylang[code][ind] = bylang[code][ind][:m]

    for item in cats:
        status = item[0]
        nomlong = item[1]
        new_text += u'== %s ==\n' % nomlong
        length = len(bylang[code][status])
        found += length
        if length > LIMITE_CHAPITRE:
            length = LIMITE_CHAPITRE
            bylang[code][status] = bylang[code][status][:length]
        if length > LIMITE_DEROULANT:
            new_text += u'{{Boîte déroulante début|titre=%s/%s %s}}\n' % (length, lengths[status], item[3])
        for elem in bylang[code][status]:
            new_text += u'{{%s}}\n' % elem[1].title()
        if length > LIMITE_DEROULANT:
            new_text += u'{{Boîte déroulante fin}}\n'
        new_text += '\n'
    if not langpage.exists():
        if not found:
            pywikibot.output('Still no entries for %s' % langpage)
        else:
            put_page(langpage, new_text)
    else:
        if new_text == langpage.get():
            pywikibot.output(u'No changes were necessary for %s' % langpage)
        else:
            put_page(langpage, new_text)

###############################
##### Pages-status
for l in bystatus.itervalues():
    l.sort(cmp=datecmp)
date_now = datetime.now().date()
before = u"<noinclude>{{Projet:Traduction/Entete/ListeMensuelle|%s}}</noinclude>\n"
pattern = u'Projet:Traduction/*/%s/%s %s'
LIMITE_INCLUDE = 7

for item in cats:
    cat = item[0]
    text = ""
    month = date_now.month
    year = date_now.year
    ttype = item[2]
    page = pywikibot.Page(site, pattern  % (ttype, int2month[month], year))
    i = 0
    for elem in bystatus[cat]:
        edate = elem[0].date()
        if edate.month != month:
            month = edate.month
            year = edate.year
            if text or page.exists():
                text = before % ttype + text
                put_page(page, text)
            text = ""
            i = 0
            page = pywikibot.Page(site, pattern % (ttype,
                                                   int2month[month],
                                                   year))
        text += u'{{%s}}' % elem[1].title()
        i += 1
        if i == LIMITE_INCLUDE:
            text += '<noinclude>'
        text += '\n'
    if text or page.exists():
        text = before % ttype + text
        put_page(page, text)

print 'DONE.'
