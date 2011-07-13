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
* récupérer une table dans un bdd
* lire un fichier de configuration
* retourner une chaine de caractère...
"""

BeginBotSection = u'<!-- BEGIN BOT SECTION -->'
EndBotSection   = u'<!-- END BOT SECTION -->'
ER_BotSection = re.compile("%s(.*)%s" % (BeginBotSection, EndBotSection), re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)

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
    if page.isRedirectPage():
        page = page.getRedirectTarget()
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
        if date.month > 1 :
            date = datetime.date(date.year, date.month-1, date.day)
        else:
            date = datetime.date(date.year-1, 12, date.day)
    url = 'http://stats.grok.se/json/%s/%s/%s' \
            % ( codelangue, date.strftime('%Y%m'), urllib2.quote(page.title().encode('utf-8')) )
    try:
        res = simplejson.load(urllib2.urlopen(url))
    except urllib2.URLError, urllib2.HTTPError:
        pywikibot.warning(u"impossible de récupérer les stats à l'adresse %s" % url)
        return 0
    return res['total_views']

def hasWikiprojet(langue):
    """ Dit si un wiki possède un wikiprojet
    """
    # Le projet sur DE à l'air en sommeil
    if langue in "fr en":
        return True
    else:
        return False

def charger_bdd(db, nom_base, champs="*", cond=None, lim=None, ordre=None):
    """
    Charger une table depuis une base de données
    """
    curseur = db.cursor()
    req = "SELECT %s FROM %s" % (champs, nom_base)
    if cond is not None:
        req += " WHERE %s" % cond
    if ordre is not None:
        req += " ORDER BY %s" % ordre
    if lim is not None:
        req += " LIMIT 0,%i" % lim
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
    stat = [ u'Statut inconnu', \
            u'Demande de traduction',   u'Traduction', \
            u'Demande de relecture',    u'Relecture', \
            u'Traduction terminé' ]
    if statut >= 1 and statut <= 5:
        return stat[statut]
    return stat[0]

def fichier_conf(fichier):
    """ Lit un fichier de configuration et retourne un dictionnaire des valeurs
    Format du fichier de conf : "clé=valeur"
    Tout ce qui est à droite de # est ignoré
    """
    conf = {}
    with open(fichier, "r") as f:
        for l in f.xreadlines():
            a = l.split('#', 1)
            if len(a) == 1:
                b = a[0].split('=', 1)
                conf[b[0].strip()] = b[1].strip()
    return conf

def reverse(chaine):
    """ Retourne la chaine de caractères mise à l'envers
    """
    rep = u''
    i = len(chaine)
    while i > 0:
        i -= 1
        rep += chaine[i]
    return rep

def retirer(exprs, text):
    """ Retire les ER de la liste 'exprs' du text
    """
    for a in exprs:
        text = a.sub(r'', text)
    return text

