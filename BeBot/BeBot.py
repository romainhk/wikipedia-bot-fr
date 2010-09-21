#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, urllib2, MySQLdb, simplejson
from MySQLdb.constants import ER
import pywikibot

"""
# Bibliothèque BeBot

Rassemble plusieurs fonctions génériques : 
* conversion mois vers entier
* lecture ligne par ligne d'un article
* taille d'une page
* page de traduction associée
* consultation mensuelle d'une page
* dire si un wiki possède un wikiprojet ou s'il donne la date de labellisation
* récupérer une table dans un bdd...
"""

def moistoint(mois):
    """
    Convertit un mois sous forme de chaîne de caractères, en son entier i associé (1≤i≤12).
    """
    mois = mois.lower()
    if mois in  'janvier    january  januar':   return 1
    elif mois in u'février  febuary  februar':  return 2
    elif mois in u'mars    march   märz  maerz':   return 3
    elif mois in 'avril    april   ':        return 4
    elif mois in 'mai      may     ':        return 5
    elif mois in 'juin     june    juni':    return 6
    elif mois in 'juillet  july    juli':    return 7
    elif mois in u'août    august  ':        return 8
    elif mois in 'septembre  september  ':   return 9
    elif mois in 'octobre    october    oktober':   return 10
    elif mois in 'novembre   november   ':          return 11
    elif mois in u'décembre  december   dezember':  return 12
    else:
        pywikibot.warning(u'mois "%s" non reconnu.' % mois)
    return 0

def page_ligne_par_ligne(site, nompage):
    """
    Lit une wikipage ligne par ligne
    """
    try:
        page = pywikibot.Page(site, nompage).get()
    except pywikibot.exceptions.NoPage:
        pywikibot.warning(u"la page « %s » n'est pas accessible." % nompage)
        return
    for ligne in page.split("\n"):
        yield ligne

def taille_page(page):
    """
    Retourne la taille d'une page en millier de caractères/signes
    """
    try:
        p = page.get()
    except:
        p = []
    return len(p)/1000

def togglePageTrad(page):
    """
    Retourne la page de traduction associée à un page, ou la page associée à une traduction
    """
    site = page.site
    if not site.language() == 'fr':
        raise pywikibot.exceptions.NoPage(pywikibot.Page(page.site, \
                page.toggleTalkPage().title()+"/Traduction"))
    trad = re.compile(u"/Traduction$", re.LOCALE)
    if trad.search(page.title()):
        #Déjà une
        return pywikibot.Page(site, page.toggleTalkPage().title().split('/Traduction')[0])
    else:
        return pywikibot.Page(site, page.toggleTalkPage().title()+"/Traduction")

def stat_consultations(page, codelangue=u'fr', date=False):
    """
    Donne le nombre de consultation d'un article au mois donné (mois précédant par défaut)
    """
    if not date:
        date = datetime.date.today()
        date = datetime.date(date.year, date.month-1, date.day)
    url = "http://stats.grok.se/json/%s/%s/%s" \
            % ( codelangue, date.strftime("%Y%m"), urllib2.quote(page.title().encode('utf-8')) )
    try:
        res = simplejson.load(urllib2.urlopen(url))
    except urllib2.URLError, urllib2.HTTPError:
        pywikibot.warning(u"impossible de récupérer les stats à l'adresse %s" % url)
        return 0
    return res["total_views"]

def hasDateLabel(langue):
    """ Dit si un wiki précise la date de labellisation
    """
    #if langue in "fr de":
    if langue in "fr": # Trop peu de labels avec une date sur DE
        return True
    else:
        return False

def hasWikiprojet(langue):
    """ Dit si un wiki possède un wikiprojet
    """
    # Le projet sur DE à l'air en sommeil
    if langue in "fr en":
        return True
    else:
        return False

def charger_bdd(db, nom_base, champs="*", cond=None):
    """
    Charger une table depuis une base de données
    """
    curseur = db.cursor()
    req = "SELECT %s FROM %s" % (champs, nom_base)
    if cond is not None:
        req += " WHERE %s" % cond
    try:
        curseur.execute(req)
    except MySQLdb.Error, e:
        pywikibot.error(u"SELECT error %d: %s.\nRequête : %s" % (e.args[0], e.args[1], req))

    return curseur.fetchall()

def info_wikiprojet(page, ER, nom_groupe, tab_elimination):
    """
    Donne l'info Wikiprojet (avancement ou importance) selon un ordre de suppression
    """
    rep = None
    if ER:
        info = []
        if (page.namespace() % 2) == 0:
            page = page.toggleTalkPage()
        for cat in page.categories():
            b = ER.search(cat.title())
            if b:
                info.append(b.group(nom_groupe))

        if len(info) > 0 and tab_elimination:
            for i in tab_elimination:
                if info.count(i) > 0:
                    info.remove(i)
                    if len(info) == 0:
                        info.append(i)
                        break
            rep = info[0]
    return rep

def stou(statut):
    """ Convertit un entier "Statut" (1 <= s <= 5) en message unicode
    """
    if   statut == 1:
        return u'Demande de traduction'
    elif statut == 2:
        return u'Traduction'
    elif statut == 3:
        return u'Demande de relecture'
    elif statut == 4:
        return u'Relecture'
    elif statut == 5:
        return u'Traduction terminé'
    else:
        #if statut < 1 or statut > 5:
        return u'Statut inconnu'
