#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, urllib, simplejson, sys, sqlite3, difflib
import pywikibot

"""
# Bibliothèque BeBot

Rassemble plusieurs fonctions génériques : 
* conversion mois vers entier
* lecture ligne par ligne d'un article
* taille d'une page
* page de traduction associée
* consultation mensuelle d'une page
* récupérer une table dans une bdd
* lire un fichier de configuration
* renverser une chaine de caractère
* sauvegarder une page
* supprimer une page
* vérifier qu'il n'y ait pas de blocage par un utilisateur
* nombre de contribs d'un utilisateur, date de dernière modif
* diff 
"""

BeginBotSection = '<!-- BEGIN BOT SECTION -->'
EndBotSection   = '<!-- END BOT SECTION -->'
ER_BotSection = re.compile("%s(.*)%s" % (BeginBotSection, EndBotSection), re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
RE_Modele = re.compile('\{\{(.+?)\}\}', re.IGNORECASE|re.LOCALE|re.DOTALL|re.MULTILINE)
RE_Comment = re.compile("(<!--.*?-->)", re.MULTILINE|re.DOTALL) # commentaire html
RE_Pipe = re.compile("\[\[((.+?)\|[^\]]+?)\]\]", re.LOCALE|re.MULTILINE|re.DOTALL) # lien avec pipe

def moistoint(mois):
    """ Convertit une chaine mois, en entier entre 1 et 12.
    """
    mois = mois.lower()
    if mois in  'janvier    january  januar':   return 1
    elif mois in 'février  febuary  februar':  return 2
    elif mois in 'mars    march   märz  maerz':   return 3
    elif mois in 'avril    april   ':        return 4
    elif mois in 'mai      may     ':        return 5
    elif mois in 'juin     june    juni':    return 6
    elif mois in 'juillet  july    juli':    return 7
    elif mois in 'août    august  ':        return 8
    elif mois in 'septembre  september  ':   return 9
    elif mois in 'octobre    october    oktober':   return 10
    elif mois in 'novembre   november   ':          return 11
    elif mois in 'décembre  december   dezember':  return 12
    else:
        pywikibot.warning('mois "%s" non reconnu.' % mois)
    return 0

def page_ligne_par_ligne(site, nompage):
    """ Lit une wikipage ligne par ligne
    """
    try:
        page = pywikibot.Page(site, nompage).get()
    except pywikibot.exceptions.NoPage:
        pywikibot.warning("la page « %s » n'est pas accessible." % nompage)
        return
    for ligne in page.split("\n"):
        yield ligne

def taille_page(page, ordre=1000):
    """ Retourne la taille d'une page en millier de caractères/signes
    """
    try:
        p = page.get()
    except:
        p = []
    return len(p)/ordre

def togglePageTrad(page):
    """ Retourne la page de traduction associée à un article, ou l'article associée à une traduction
    """
    site = page.site
    if not site.language() == 'fr':
        raise pywikibot.exceptions.NoPage(pywikibot.Page(page.site, \
                page.toggleTalkPage().title()+"/Traduction"))
    if page.isRedirectPage():
        page = page.getRedirectTarget()
    trad = re.compile("/Traduction$", re.LOCALE)
    if trad.search(page.title()):
        #Déjà une
        return pywikibot.Page(site, page.toggleTalkPage().title().split('/Traduction')[0])
    else:
        return pywikibot.Page(site, page.toggleTalkPage().title()+"/Traduction")

def stat_consultations(page, codelangue='fr', date=False):
    """ Nombre de consultation d'un article au mois donné (mois précédant par défaut)
    """
    if not date:
        date = datetime.date.today()
        if date.month > 1 :
            date = datetime.date(date.year, date.month-1, date.day)
        else:
            date = datetime.date(date.year-1, 12, date.day)
    url = 'http://stats.grok.se/json/%s/%s/%s' \
            % ( codelangue, date.strftime('%Y%m'), urllib.quote(page.title().encode('utf-8')) )
    try:
        res = simplejson.load(urllib.urlopen(url))
    except (urllib.URLError, urllib.HTTPError):
        pywikibot.warning("impossible de récupérer les stats à l'adresse %s" % url)
        return 0
    return res['total_views']

def charger_bdd(db, nom_base, champs="*", cond=None, lim=None, ordre=None):
    """ Charger une table depuis une base de données
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
    except:
        pywikibot.error("Erreur lors du chargement de la BDD - Requête : {0}\n".format(req))

    return curseur.fetchall()

def info_wikiprojet(page, ER, nom_groupe, tab_elimination):
    """ Donne l'info Wikiprojet (avancement ou importance) selon un ordre de suppression
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

def fichier_conf(fichier):
    """ Lit un fichier de configuration et retourne un dictionnaire des valeurs
    Format du fichier de conf : "clé=valeur"
    Tout ce qui est à droite de # est ignoré
    """
    conf = {}
    with open(fichier, "r") as f:
        for l in f.xreadlines():
            a = l.split('#', 1)
            if len(a) == 1: #TODO: si a non vide, prendre a[0]
                b = a[0].split('=', 1)
                conf[b[0].strip()] = b[1].strip()
    return conf

def reverse(chaine):
    """ Retourne la chaine de caractères mise à l'envers
    """
    rep = ''
    i = len(chaine)
    while i > 0:
        i -= 1
        rep += chaine[i]
    return rep

def save(page, commentaire='', minor=False, debug=False):
    """ Sauvegarde la page
    """
    if debug:
        pywikibot.output('Sav -> %s' % page.title())
    else:
        try:
            page.save(summary=commentaire, minor=minor)
        except pywikibot.EditConflict:
            pywikibot.warning("Abandonne la modification de %s à cause d'un conflit d'édition"
                              % (page,))
        except pywikibot.SpamfilterError as e:
            pywikibot.warning("Ne peut pas modifier %s à cause d'un blacklistage %s"
                              % (page, e.url))
        except pywikibot.PageNotSaved as error:
            pywikibot.warning("Erreur lors de l'écriture de %s" % error)
        except pywikibot.LockedPage:
            pywikibot.warning('Abandonne la modification de %s (page verrouillée)' % (page,))
        except pywikibot.ServerError as e:
            pywikibot.warning('Erreur Serveur : %s' % e)
        except:
            pywikibot.warning('Erreur inconnue lors du traitement de %s' % page.title())

def delete(page, raison, debug=False):
    """ Supprime la page
    """
    if debug:
        redir = ''
        if page.isRedirectPage():
            redir = " (redirection)"
        pywikibot.output('Del -> %s%s' % (page.title(), redir))
    else:
        try:
            page.delete(reason=raison, prompt=False)
        except pywikibot.NoUsername as e:
            pywikibot.warning('Suppression de %s impossible - Utilisateur inconnu' % page)
        except:
            pywikibot.warning('Suppression de %s impossible' % page)

def modeletodic(modele):
    """ Transforme un chaine "modèle" en tableau
    convention : r[0] est le nom du modèle
    """
    r = {}
    m = RE_Modele.search(modele)
    if m:
        chaine = m.group(1).replace('\n', '')
        chaine = RE_Comment.sub(r'', chaine)
        chaine = RE_Pipe.sub(r'[[\2]]', chaine) #pour le split après
        pos = 0
        for l in chaine.split("|"):
            if pos == 0:
                r[0] = l.strip()
                pos += 1
            else:
                a = l.split("=")
                b = a[0].strip()
                if len(a) > 1:
                    r[b] = a[1].strip()
                else:
                    r[pos] = b
                    pos +=1
    else:
        pywikibot.warning("BeBot.modeletodic() ; il a été impossible de lire le modèle suivant\n%s" % modele)
    return r

def blocage(site):
    """ Vérifie que BeBot n'a pas eu d'alerte bloquante de la part des utilisateurs
    """
    page = pywikibot.Page(site, 'Utilisateur:BeBot/Blocage')
    if len(page.text) > 0:
        last = page.getVersionHistory()[0]
        user = last[2]
        time = last[1]
        pywikibot.output('BeBot a été bloqué par %s (timestamp:%s)' % (user, time))
        pywikibot.output('Message : %s' % page.text)
        return True
    return False

def userdailycontribs(site, user, days=1):
    """ Nombre de modifications qu'un utilisateur à fait depuis 'days' jours à partir d'aujourd'hui
        + Date de la dernière
    # TODO : à partir d'un autre jour
    """
    contrib = 0
    last = ''
    ajd = site.getcurrenttime()
    fin = ajd - datetime.timedelta(days=days)
    for c in site.usercontribs(user, start=ajd, end=fin):
        contrib += 1
        if contrib == 1:
            last = c['timestamp']
    return [contrib, last]

def WM_verif_feneantise(site, semaine, annee):
    """ Vérifie qu'un wikimag a bien été rédigé
    """
    num = "%s/%s" % (annee, semaine)
    wm = pywikibot.Page(site, "Wikipédia:Wikimag/%s" % num)
    if not wm.exists() or taille_page(wm, 1) < 500 :
        return True
    return False

def WM_prevenir_redacteurs(site, message):
    """ Prévient les rédacteurs du wikimag
    """
    redac = [] # les rédacteurs déjà prévenus
    cat = pywikibot.Category(site, 'Utilisateur rédacteur Wikimag')
    for r in cat.articles():
        can = r.title().split('/')
        if len(can) > 0:
            can = can[0]
        redacteur = pywikibot.Page(site, can)
        if not redacteur.isTalkPage():
            redacteur = redacteur.toggleTalkPage()
        if redacteur.isRedirectPage():
            redacteur = redacteur.getRedirectTarget()
        # Avertissement avec dédoublonnage
        if not redacteur in redac:
            pywikibot.output(redacteur.title())
            redac.append(redacteur)
            redacteur.text += message
            save(redacteur, commentaire="Wikimag : alerte de rédaction", debug=False)

def duree_depuis_derniere_modif(site, page):
    """ Renvoie le nombre de jours depuis la dernière modification de la page
    """
    lr = page.latestRevision()
    versions = page.getVersionHistory()
    pop = versions.pop()
    while lr != pop[0]:
        # On cherche la dernière modif
        pop = versions.pop()
    date = datetime.datetime.strptime(pop[1], '%Y-%m-%dT%H:%M:%SZ')
    ajd = site.getcurrenttime()
    return (ajd-date).days

def diff(t1, t2):
    """ Affiche un diff entre deux chaînes (par exemple une page et sa version altérée)
    """
    diff = difflib.ndiff(t1.splitlines(1), t2.splitlines(1))
    for ligne in diff:
        if ligne[0] in "-+":
            pywikibot.output(ligne.rstrip('\n'))

