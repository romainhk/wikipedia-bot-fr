#!/usr/bin/python
# -*- coding: utf-8  -*-
from wikipedia import *

# Bibliothèque BeBot

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
    """ Lit une wikipage ligne par ligne
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
    if (page.namespace() % 2) == 0:
        return wikipedia.Page(site, page.toggleTalkPage().title()+"/Traduction")
    else:
        # Espace de discussion
        return wikipedia.Page(site, page.toggleTalkPage().title().split('/Traduction')[0])

