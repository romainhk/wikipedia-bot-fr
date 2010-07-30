#!/usr/bin/python
# -*- coding: utf-8  -*-
from wikipedia import *

# Bibliothèque BeBot

def togglePageTrad(site, page):
    """
    Retourne la page de traduction associée à un page, ou la page associée à une traduction
    """
    if (page.namespace() % 2) == 0:
        return wikipedia.Page(site, page.toggleTalkPage().title()+"/Traduction")
    else:
        # Espace de discussion
        return wikipedia.Page(site, page.toggleTalkPage().title().split('/Traduction')[0])

def taille_page(page):
    """
    Retourne la taille d'une page en millier de caractères/signes
    """
    return len(page.get())/1000

def moistoint(mois):
    """
    Convertit une chaîne de caractètre correspondant à un mois, en un entier i (1≤i≤12).
    """
    mois = mois.lower()
    if mois == u'janvier':     return 1
    elif mois == u'février':   return 2
    elif mois == u'mars':      return 3
    elif mois == u'avril':     return 4
    elif mois == u'mai':       return 5
    elif mois == u'juin':      return 6
    elif mois == u'juillet':   return 7
    elif mois == u'août':      return 8
    elif mois == u'septembre':  return 9
    elif mois == u'octobre':    return 10
    elif mois == u'novembre':   return 11
    elif mois == u'décembre':   return 12
    else:
        wikipedia.output(u'Mois « %s » non reconnu' % mois)
    return 0
