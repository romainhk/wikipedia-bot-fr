#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, simplejson, urllib2
from wikipedia import *

"""
# Bibliothèque BeBot

Rassemble plusieurs fonctions génériques : 
taille d'une page, page de traduction associée, consultation mensuelle d'une page, conversion mois vers entier...
"""

def moistoint(mois):
    """
    Convertit une chaîne de caractètre correspondant à un mois, en un entier i (1≤i≤12).
    """
    mois = mois.lower()
    if mois in 'janvier    january':   return 1
    elif mois in u'février febuary':   return 2
    elif mois in 'mars     march':     return 3
    elif mois in 'avril    april':     return 4
    elif mois in 'mai      may':       return 5
    elif mois in 'juin     june':      return 6
    elif mois in 'juillet  july':      return 7
    elif mois in u'août    august':    return 8
    elif mois in 'septembre  september':  return 9
    elif mois in 'octobre    october':    return 10
    elif mois in 'novembre   november':   return 11
    elif mois in u'décembre  december':   return 12
    else:
        wikipedia.output(u'Mois « %s » non reconnu' % mois)
    return 0

def page_ligne_par_ligne(site, nompage):
    """
    Lit une wikipage ligne par ligne
    """
    try:
        page = wikipedia.Page(site, nompage).get()
    except pywikibot.exceptions.NoPage:
        wikipedia.output(u"La page « %s » n'est pas accessible." % nompage)
        return
    for ligne in page.split("\n"):
        yield ligne

def taille_page(page):
    """
    Retourne la taille d'une page en millier de caractères/signes
    """
    return len(page.get())/1000

def togglePageTrad(site, page):
    """
    Retourne la page de traduction associée à un page, ou la page associée à une traduction
    """
    if not site.language() == 'fr': return u''
    trad = re.compile(u"/Traduction$", re.LOCALE)
#    if (page.namespace() % 2) == 0:
    if not trad.search(page.title()):
        return wikipedia.Page(site, page.toggleTalkPage().title()+"/Traduction")
    else:
        # Espace de discussion
        return wikipedia.Page(site, page.toggleTalkPage().title().split('/Traduction')[0])

def stat_consultations(page, codelangue=u'fr', date=False):
    """
    Donne le nombre de consultation d'un article au mois donné (mois précédant par défaut)
    """
    if not date:
        date = datetime.date.today()
        date = datetime.date(date.year, date.month-1, date.day)
    url = "http://stats.grok.se/json/%s/%s/%s" % ( codelangue, date.strftime("%Y%m"), urllib2.quote(page.title().encode('utf-8')) )
    try:
        res = simplejson.load(urllib2.urlopen(url))
#    except urllib2.URLError, urllib2.HTTPError:
    except:
        wikipedia.output("Impossible de récupérer les stats à l'adresse %s" % url)
        return 0
    return res["total_views"]
