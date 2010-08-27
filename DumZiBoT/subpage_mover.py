# -*- coding: utf-8  -*-
"""
Script moving special subpages when a page has been moved.
It is supposed to run at regular intervals, as it only checks the
last moves in ]now-delta, now]

This library is free software; you can redistribute it and/or
modify it under the terms of the MIT License.
See the LICENCE file
"""

import pywikibot
from datetime import timedelta
import re

interval = timedelta(hours=2)
subpages = ['Suppression', u'Article de qualité', u'Bon article',
            'Droit d\'auteur', u'Neutralité', 'Traduction',
            '[Aa]rchives?\d*', u'À faire']
subpagesGroup = '(' + '|'.join(subpages) + ')'

site = pywikibot.Site('fr', 'wikipedia')
summary = u'Robot: renommage différé des sous-pages de discussion, suite au renommage de la page principale %s'

copyvio = re.compile('(?i).*/(copyvio|purge|clean)')

msg = {
    'purge' : u'* [[Image:Commons-emblem-copyright.svg|20px]] %s [[Image:pfeil rechts.svg|12px]] %s',
    'miss': u'** [[Fichier:Commons-emblem-query.svg|20px]] %s n\'existe plus. Sous-pages de %s non vérifiées',
    'move': u'** Déplacement: %s [[Image:Progress axis arrow 2.svg|30px]] %s',
    'user': u'** [[Fichier:Ambox contradict.svg|20px]] %s est une page utilisateur. Tentative de renommage de compte ?',
    'error': u'** [[Fichier:Gnome-emblem-important.svg|20px]] %s : %s',
    'ignore': u'** [[Fichier:Commons-emblem-notice.svg|20px]] Sous-page ignorée: %s'
}

bureaucrates = ['Anthere', 'Clem23', u'Céréales Killer', 'EDUCA33E', 'Esprit Fugace', 'Popo le Chien']

section = re.compile('==[^=]*==[^=]*(?!=)', re.M)

def getEligibleMoves():
    now = site.getcurrenttime()
    checkfrom = now - interval
    checkto = checkfrom - interval
    return site.logevents(logtype='move', \
                            start=checkfrom, \
                            end=checkto)
log = {}
for entry in getEligibleMoves():
    title = entry.title()
    if not title.isTalkPage():
        log[entry] = []
        if entry.ns() == 2 and not '/' in title.title():
            # Tried to rename ?
            if entry.user() not in bureaucrates:
                log[entry].append(msg['user'] % title.title(asLink=True))

        target = entry.new_title()
        if copyvio.match(target.title()) or copyvio.match(title.title()):
            log[entry] = msg['purge'] % (title.title(asLink=True), target.title(asLink=True))
            continue

        if not target.exists():
            log[entry].append( msg['miss'] \
                               % (target.title(asLink=True), \
                                  title.title(asLink=True)))
            continue
        talk = title.toggleTalkPage()
        targettalk = target.toggleTalkPage()
        subpagesRe = re.compile(u'%s(?P<sub>/%s)' % (re.escape(talk.title()), subpagesGroup))
        pywikibot.output(u'* %s -> %s' % (title.title(), target.title()))
        for page in site.allpages(namespace=entry.ns()+1, \
                                    prefix=talk.title(withNamespace=False) + '/'):
            m = subpagesRe.match(page.title())
            if m:
                pywikibot.output(u'** %s' % page.title())
                try:
                    log[entry].append(msg['move'] % \
                        (page.title(asLink=True), u'[[' + targettalk.title() + m.group('sub') + ']]'))
                    site.movepage(page, targettalk.title() + m.group('sub'), \
                        summary % targettalk.title(), \
                        noredirect=entry.suppressedredirect())
                except pywikibot.Error, e:
                    log[entry].append( msg['error']% (page.title(asLink=True), e))
            else:
                log[entry].append(msg['ignore'] % page.title(asLink=True))

logtext = ''
for entry, events in log.iteritems():
    if not events:
        continue
    if not isinstance(events, unicode):
        logtext += u'* %s [[Image:pfeil rechts.svg|12px]] %s\n' % (entry.title().title(asLink=True), entry.new_title().title(asLink=True))
        logtext += '\n'.join(events) + '\n'
    else:
        logtext += events + '\n'

#logtext = u'* test (Tentative de ne laisser que 24 entrées au maximum)'
if logtext:
    logtext = '\n\n== ~~~~~ ==\n' + logtext
    logpage = pywikibot.Page(site, 'Utilisateur:DumZiBoT/Log/MoveSubPages')
    text = logpage.get()

    allsections = [m for m in section.finditer(text)]
    begin = allsections[0].start()
    text = text[:begin].rstrip()
    # keep only the 23 latest sections
    keep = allsections[-23:]
    for m in keep:
        text += '\n' + m.group()
    try:
        logpage.put(text + logtext, 'Journalisation')
    except pywikibot.Error, e:
        print logtext
        print e
