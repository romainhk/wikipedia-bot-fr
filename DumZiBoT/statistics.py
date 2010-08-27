# -*- coding: utf-8 -*-
"""
Script to gather statistics for project importance and quality assessment.
Updates the relevant project subpages with up-to-date stats.

This library is free software; you can redistribute it and/or
modify it under the terms of the MIT License.
See the LICENCE file
"""

import urllib, re, cPickle
from collections import defaultdict
import pywikibot

def putNb(page,nb):
    try:
        old = page.get()
    except pywikibot.NoPage:
        old = ''
    except pywikibot.IsRedirectPage:
        return
    if old != str(nb):
        page.put(str(nb))

site = pywikibot.Site('fr', 'wikipedia')

importance = ['maximum', u'élevée', 'moyenne', 'faible', 'inconnue']
avancement = ['AdQ', 'BA', 'A', 'B', 'BD', u'ébauche', 'inconnu']
patI = u"Catégorie:%s d'importance %s"
patA = u"Catégorie:%s d'avancement %s"
URLbase = u'http://toolserver.org/~bayo/intercat.php?'
patURL = u'formCat1=%s d\'avancement %s&formCat2=%s d\'importance %s'

pywikibot.setAction(u'Mise à jour des statistiques WP 1.0')

pywikibot.Page(pywikibot.Link('Utilisateur:DumZiBoT/DateEval')).put('{{subst:CURRENTDAY}} {{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}}')

param = u'{{[Uu]tilisateur:DumZiBoT/Demande statistiques projet[^}]*\|%s\s*=\s*([^\|}]*)\s*(?:\|[^}]*|)}}'
reNom = re.compile(param % '[Nn]om')
rePre = re.compile(param % u'[pP]réfixe')
reType = re.compile(param % '[Tt]ype')

reTl = re.compile(u'<!-- BEGIN BOT SECTION .* END BOT SECTION -->', re.DOTALL)

resultats = {}
pywikibot.output(u'Récupération des modèles...')
reqs = pywikibot.Page(site, u'Utilisateur:DumZiBoT/Demande statistiques projet')
gen = site.page_embeddedin(reqs, namespaces=[102])
gen = site.preloadpages(gen, groupsize=100)
for req in gen:
    try:
        text = req.get()
    except pywikibot.Error:
        continue
    s = reNom.search(text)
    if not s:
        pywikibot.output(u'Pas de modèle sur %s' % req.title(asLink=True))
        continue
    projet = s.group(1).strip()
    if ">" in projet or "<" in projet:
        pywikibot.warning(u're buggy? %s / %s' % (projet, req.title(asLink=True)))
        continue

    pywikibot.output(u'Traitement du projet %s...' % projet)
    s = rePre.search(text)
    prefixe = s.group(1).strip()
    s = reType.search(text)
    type = s.group(1).strip()

    pos = s.end()
    if not resultats.has_key(projet):
        # keys: category (avancement cat, or importance cat)
        # values: Page set
        artByCat = defaultdict(set)
        # keys: article title
        # values: [importance, avancement] 2-element list
        articles = defaultdict(lambda: [None, None])

        saveEval = pywikibot.config.datafilepath('eval', u'%s.dat' % projet)
        try:
            f = open(saveEval, 'r')
            oldArticles = cPickle.load(f)
            f.close()
        except (IOError, EOFError):
            oldArticles = {}

        # XXX it would be nicer to use an appropriate Evaluation class instead
        #   of a dict: it would allow cleaner semantics
        resultats[projet] = {}

        resultats[projet]['projet'] = projet

        total = 0
        for i, imp in enumerate(importance):
            catname = patI % (prefixe, imp)
            cat = pywikibot.Page(site, catname)
            lenCat = 0
            for p in site.categorymembers(cat, namespaces=[1]):
                artByCat[imp].add(p)
                lenCat += 1
                articles[p.title()][0] = imp
            resultats[projet][43 + i] = u'[[:%s|{{formatnum:%s}}]]' % (catname, lenCat)
            total += lenCat

        resultats[projet]['total'] = total

        t = pywikibot.Page(pywikibot.Link(u'Projet:%s/Total' % projet))
        putNb(t, total)

        totalEval = total - len(artByCat[importance[-1]])
        t = pywikibot.Page(pywikibot.Link(u'Projet:%s/Évaluation/Total évalué' % projet))
        putNb(t, totalEval)

        resultats[projet][48] = '{{formatnum:%s}}' % totalEval

        for i, av in enumerate(avancement):
            catname = patA % (prefixe, av)
            cat = pywikibot.Page(site, catname)
            for p in site.categorymembers(cat, namespaces=[1]):
                artByCat[av].add(p)
                try:
                    articles[p.title()][1] = av
                except KeyError:
                    pass
            resultats[projet][6*(i + 1)] = u'[[:%s|{{formatnum:%s}}]]' % (catname, len(artByCat[av]))


        if isinstance(prefixe, unicode):
            prefixe = urllib.quote(prefixe.encode('utf-8'))
        i = 1
        for av in avancement:
            if isinstance(av, unicode):
                a = urllib.quote(av.encode('utf-8'))
            else:
                a = av
            for imp in importance:
                if isinstance(imp, unicode):
                    im = urllib.quote(imp.encode('utf-8'))
                else:
                    im = imp
                inter = len(artByCat[av].intersection(artByCat[imp]))
                if inter:
                    url = URLbase + patURL % (prefixe, a, prefixe, im)
                    url = url.replace(' ', '%20')
                    resultats[projet][i] = u'<span class="plainlinks">[%s {{formatnum:%s}}]</span>' % (url, inter,)
                else:
                    resultats[projet][i] = ''
                i += 1
            i += 1

### This is unfinished/untested feature "history" of evaluations
#        oldKeys = set(oldArticles.keys())
#        newKeys = set(articles.keys())
#
#        inter = oldKeys & newKeys
#        new = newKeys - oldKeys
#        deleted = oldKeys - newKeys

        f = open(saveEval, 'w')
        cPickle.dump(dict(articles), f)
        f.close()

    tl = u'<!-- BEGIN BOT SECTION -->'
    if type.lower() == 'simple':
        tl += u'{{Utilisateur:NicDumZ/Eval\n'
    else:
        tl += u'{{Utilisateur:NicDumZ/Eval Detail\n'

    for (k,v) in resultats[projet].iteritems():
        tl += u'| %s = %s\n' % (k, v)
    tl += '}}\n<!-- END BOT SECTION -->'

    (new_text, n) = reTl.subn(tl, text, 1)
    if not n:
        new_text=text[:pos] + '\n' + tl + text[pos:]

    if new_text != text:
        req.put(new_text)
