#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys, os, urllib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class MailWikimag:
    """ Mail Wikimag
        Publie le wikimag par mail

        Nécessite en argument l'adresse d'un fichier de configuration du type :
mailinglist=    # sur laquel on va publier le mag (mode debug si omis)
epreuve=        # adresse mail des relecteurs
from=           # adresse de l'expédieur, truc@toto.fr
#mode=          # (facultatif) format d'envoi : text (*), html ou multi
#semaine=       # (facultatif) forcer l'usage d'une semaine en particulier ; pratique pour le debug
        L'option finale -e permet de faire une épreuve (tirage limité aux relecteurs)

        TODO
        gérer les interlangues
        html : inclure les images ?
    """
    def __init__(self, site, fichier_conf, epreuve):
        self.site = site
        self.conf_mail = fichier_conf
        self.conf = BeBot.fichier_conf(self.conf_mail)
        self.epreuve = epreuve
        self.tmp = u'Utilisateur:BeBot/MailWikimag' # Pour le mode text
        date = datetime.date.today()
        self.lundi = date - datetime.timedelta(days=date.weekday())
        self.lundi_pre = self.lundi - datetime.timedelta(weeks=1)
        if self.epreuve:
            pywikibot.output(u"# Mode épreuve ; publication limitée")
            self.lundi_pre = self.lundi
            self.lundi = self.lundi_pre + datetime.timedelta(weeks=1)
        self.debug = False # Mode de débugage actif ?
        if 'semaine' in self.conf:
            self.semaine = self.conf['semaine']
            self.debug = True
        else:
            self.semaine = self.lundi_pre.strftime("%W").lstrip('0')
        self.mag = pywikibot.Page(site, u'Wikipédia:Wikimag/%s/%s' % \
                (self.lundi_pre.strftime("%Y"), self.semaine) )
        self.numero = 0
        if self.mag.isRedirectPage():
            self.mag = self.mag.getRedirectTarget()

        self.fichier_mail = u'./mail_wikimag.tmp' # Fichier temporaire pour le mail
        self.mode = u'' # Mode de génération en cours : text ou html
        self.sommaire_jocker = '###141### SOMMAIRE ###592###'
        self.exps = {
                'split'     : re.compile("^\|([\w \xe9]+?)\s*=", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'style'     : re.compile("\s*(style|valign|width|rowspan|colspan)=\".+?\"\s*", re.LOCALE|re.UNICODE|re.IGNORECASE),
                'sommaire'  : re.compile(self.sommaire_jocker, re.LOCALE|re.UNICODE),
                'W_liste'   : re.compile("^\s*\*", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'http'      : re.compile("(http)%3A", re.LOCALE|re.UNICODE|re.MULTILINE),
                'html'      : re.compile("<(?P<balise>\w+)[^<>]*>(.*?)</(?P=balise)>", re.LOCALE|re.UNICODE|re.DOTALL),
                'comment'   : re.compile("<!--(.*?)-->", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'center'    : re.compile("<center>(.*?)</center>", re.LOCALE|re.UNICODE|re.DOTALL),
                'hr'        : re.compile("<hr[ /]*>", re.LOCALE|re.UNICODE),
                'br'        : re.compile("<br[ /]*>", re.LOCALE|re.UNICODE),
                'W_br'      : re.compile("\n\n", re.LOCALE|re.UNICODE|re.MULTILINE),
                'annonces'  : re.compile("\*? ?\{\{Annonce[ \w\xe9]*\|(\d+)\|(.+)\}\}", re.LOCALE|re.UNICODE|re.IGNORECASE),
                'image'     : re.compile("\[\[(?:Image|File|Fichier):([^\]]+)\]\]\s*", re.LOCALE|re.UNICODE|re.IGNORECASE),
                'image_seule' : re.compile("^\[\[(?:Image|File|Fichier):(.*)\]\]$\s?", re.LOCALE|re.UNICODE|re.IGNORECASE|re.MULTILINE),
                'lien_ext'  : re.compile("(\[http:[^\] ]+ +[^\]]*\])", re.LOCALE|re.UNICODE),
                'lien_int'  : re.compile("(\[\[.+?\]\])", re.LOCALE|re.UNICODE),
                'modele'    : re.compile("\{\{(.+?)\}\}", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                #'modele'    : re.compile("\{\{([^\|\}:=]*?)\|?([^\}:]*)\}\}", re.LOCALE|re.UNICODE),
                'ref'       : re.compile("<ref>(.*?)</ref>", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'tableau'   : re.compile("\{\|(.+)\|\}", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'formatnum' : re.compile("\{\{(formatnum):([^\}:]*)\}\}", re.LOCALE|re.UNICODE),
                '='         : re.compile("\{\{=\}\}", re.LOCALE|re.UNICODE),
                'quote'     : re.compile("(?P<quote>'{2,5})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'b'         : re.compile("(?P<quote>'{3})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'i'         : re.compile("(?P<quote>'{2})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'liste'     : re.compile("\*+\s?([^\*]*)", re.LOCALE|re.UNICODE),
                'User'      : re.compile("\[\[Utilisateur:(\w+)(\|\w+)?\]\]", re.LOCALE|re.UNICODE|re.IGNORECASE),
                'User talk' : re.compile("\[\[Discussion utilisateur:(\w+)(\|\w+)?\]\]", re.LOCALE|re.UNICODE|re.IGNORECASE),
                'W___'      : re.compile("__[A-Z]+__\s*", re.LOCALE),
                'transclu'  : re.compile("\{\{([^\|\}]+)\}\}", re.LOCALE|re.UNICODE),
                'noinclude' : re.compile("<noinclude>(.*?)</noinclude>\s*", re.LOCALE|re.UNICODE|re.DOTALL)
                } # Toute les expressions qui seront détectée
        self.modeles = {
                'u' : 1,    'm' : 1,    'u\'' : 1,  'a' : 1,    'l' : 1,    'citation' : 1,
                'grossir' : 1,
                'lang' : 2,
                'a-label' : 'lien',
                'guil' : 'guil',    'citation' : 'guil',    u'citation étrangère' : 'guil',
                u'unité' : u'unité',    'heure' : 'heure',     'wikimag bistro' : 'WM_bistro'
                } # Ce qu'il faut faire avec chaque modele : les modèles inconnus seront supprimés
        self.interprojets = {
                'wikipedia'     : 'wikipedia.org/wiki/',
                'wiktionary'    : 'wiktionary.org/wiki/',
                'wikinews'      : 'wikinews.org/wiki/',
                'wikibooks'     : 'wikibooks.org/wiki/',
                'wikiquote'     : 'wikiquote.org/wiki/',
                'wikisource'    : 'wikisource.org/wiki/',
                'wikispecies'   : 'species.wikimedia.org/wiki/',#
                'v'             : 'wikiversity.org/wiki/',
                'wikimedia'     : 'wikimediafoundation.org/wiki/',#
                'commons'       : 'commons.wikimedia.org/wiki/',#
                'meta'          : 'meta.wikimedia.org/wiki/',#
                'incubator'     : 'incubator.wikimedia.org/wiki/',#
                'mw'            : 'www.mediawiki.org/wiki/',#
                'bugzilla'      : 'bugzilla.wikimedia.org/wiki/'#
                } # nom-url des autres projets
        self.raccourcis_interprojets = {
                'w'     : 'wikipedia',
                'wikt'  : 'wiktionary',
                'n'     : 'wikinews',
                'b'     : 'wikibooks',
                'q'     : 'wikiquote',
                's'     : 'wikisource',
                'species'     : 'wikispecies',
                'foundation'  : 'wikimedia',
                'm'     : 'meta'
                }

        self.aProjetLocal = [ 'wikipedia', 'wiktionary', 'wikinews', 'wikibooks', 
                'wikiquote', 'wikisource', 'v' ] # Projets pour lesquels il existe une version localisée
        self.disclaimer = u'Des erreurs ? Consulter [[%s|la dernière version sur le wiki]]' % self.mag.title() # Message de fin

    def transclusion(self, match):
        """ Traitement spécifique pour les transclusions
        """
        page = match.group(1)
        if page in self.modeles.keys():
            return u'{{%s}}' % page # Modèle simple pour lequel on a un plan
        p = pywikibot.Page(self.site, u'Modèle:'+page)
        if p.exists():
            return u'' # Modèle inconnu, mais certainement pas une transclusion
        if page[0] == u'/':
            page = self.mag.title() + page
        # Lien seul
        #return u'Retrouvez la page « %s » sur le wiki' % self.lien_interne(%page.split('/').pop())

        # Recopiage
        p = pywikibot.Page(self.site, page)
        p.text = self.exps['noinclude'].sub(r'', p.text)
        return p.text

    def modele(self, match):
        """ Traitement spécifiques pour les modèles (à paramètres ou non)
        """
        params = {} # Les paramètres du modèle
        i = -1
        pipe = match.group(1).split('|')
        for p in pipe:
            a = p.split('=')
            b = a[0]
            if len(a) < 2:
                c = b
                b = i
                i += 1
            else:
                c = a[1]
            params[b] = c
        nom = params[-1].lower()
        if nom not in self.modeles.keys():
            return u'' # Les modèles complexes restants
        action = self.modeles[nom]
        if   type(action) == type(1):
            return params[action-1]  # i-ème paramètre
        elif action == 'lien':
            return u'[[' + params[0] + u']]' # lien interne
        elif action == 'espace':
            return u' '
        elif action == u'guil':
            return u'« ' + params[0] + u' »'
        elif action == u'unité':
            return params[0] + u' ' + params[1]
        elif action == u'heure':
            return params[0] + u'h' + params[1]
        elif action == u'WM_bistro':
            jour = params[0].replace(' ', '_')
            titre = params[1]
            if len(params) != 4:
                sub = params[1]
            else:
                sub = params[2]
            sub = sub.replace(' ', '_')
            return self.lien_externe(u'[http://fr.wikipedia.org/wiki/Wikipédia:Le_Bistro/%s#%s %s]' % (jour, sub, titre))

    def tableau(self, match):
        """ Transcrit un tableau
        """
        tab = []
        tailles = []
        text = match.group(1)
        while self.exps['style'].search(text):
            text = self.exps['style'].sub('', text)
        rows = text.split('|-')
        for r in rows[1:]:
            if '||' in r:
                cols = r.split('||')
            else:
                cols = r.split('\n|')[1:]
            col = []
            for c in cols:
                if len(c) > 1:
                    col.append(c)
            tab.append(col)
            tailles.append(len(col))
        # Rendu
        ret = u''
        if self.mode == u'text':
            for j in range(0,max(tailles)):
                for i in range(0,len(tailles)):
                    ret += tab[i][j]
        else:
            tr = u''
            for r in tab:
                td = u''
                for c in r:
                    td += '<td>%s</td>\n' % c
                tr += '\t<tr>%s</tr>\n' % td
            ret = '<table>\n%s</table>' % tr
        #pywikibot.output(ret)
        return ret

    def lien_externe(self, lien):
        esp = lien.strip('[]').split(' ')
        cible = esp[0]
        if len(esp) == 1:
            nom = ' '.join(esp[0:])
        else:
            nom = ' '.join(esp[1:])
        if self.mode == 'text':
            return '%s [ %s ]' % (nom, cible)
        else:
            return self.html_lien(cible, nom)

    def lien_interne(self, lien):
        sep = lien.strip('[]').split('|')
        cible = sep[0]
        if len(sep) == 1:
            nom = sep[0]
        else:
            nom = sep[1]
        projet = 'wikipedia'
        langue = 'fr'
        deuxpoint = cible.split(':')
        if cible[0] == ':':
            prems = deuxpoint[1]
            if prems in self.interprojets.keys():
                projet = prems
                cible = ':'.join(deuxpoint[2:])
            elif prems in self.raccourcis_interprojets.keys():
                projet = self.raccourcis_interprojets[prems]
                cible = ':'.join(deuxpoint[2:])
            #elif prems in self.langues:
        cible = self.interprojets[projet] + cible
        if projet in self.aProjetLocal:
            cible = langue + '.' + cible

        lien_externe_associe = u'http://' + cible.replace(' ', '_')
        #pywikibot.output('|'.join(sep) + ' : ' + lien_externe_associe)
        return self.lien_externe(u'[%s %s]' % (lien_externe_associe, nom))

    def remplacer_les_liens(self, text):
        """ Mets en forme des liens
        """
        for lien in re.finditer(self.exps['lien_ext'], text):
            b = text.partition(lien.group(0))
            text = b[0] + self.lien_externe(lien.group(0)) + b[2]
        for lien in re.finditer(self.exps['lien_int'], text):
            b = text.partition(lien.group(0))
            text = b[0] + self.lien_interne(lien.group(0)) + b[2]
        return text

    def gen_plaintext(self, pagetmp):
        """ Génération du format texte brut
        """
        self.mode = u'text'
        modele_de_presentation = u'Wikimag_par_mail'
        modele = re.compile("\{\{[cC]omposition wikimag", re.LOCALE)

        pagetmp.text = modele.sub(u'{{subst:%s|' % modele_de_presentation, self.mag.text)
        pagetmp.text = BeBot.retirer( [self.exps['noinclude']], pagetmp.text) # retrait de la catégorie
        try:
            pagetmp.save(comment=u'Préparation pour le mail du Wikimag', minor=False)
        except:
            pywikibot.error(u"Impossible d'effectuer la substitution")
            sys.exit(2)
        text = pywikibot.Page(self.site, self.tmp).text + self.disclaimer
        if self.epreuve: text = u'CE MAIL EST UNE ÉPREUVE DU PROCHAIN MAG.\n' + text
        text = self.exps['User'].sub(r'{{u|\1}}', text)
        text = self.exps['='].sub(r'&#x3D;', text)
        text = self.exps['formatnum'].sub(r'\2', text)
        text = self.exps['annonces'].sub(r'* \1 : \2', text)
        text = self.exps['transclu'].sub(self.transclusion, text)
        text = self.exps['modele'].sub(self.modele, text)

        text = self.exps['ref'].sub(r' (\1)', text)
        text = BeBot.retirer( [self.exps['comment'], self.exps['br'], \
                self.exps['image_seule'], self.exps['image'], self.exps['W___'], \
                self.exps['noinclude']], text)
        text = self.exps['hr'].sub(r'-----  -----  -----', text)
        text = self.exps['tableau'].sub(self.tableau, text)
        text = self.exps['center'].sub(r'    \1', text)
        text = self.exps['html'].sub(r'\2', text)
        text = self.exps['quote'].sub(r'\2', text)
        text = text.replace('&#x3D;', '=')
        return self.remplacer_les_liens(text)

    def gen_html(self):
        """ Génération au format Html
        """
        self.mode = u'html'
        text = self.mag.text[2:]
        parametres = {
                u'édito'        : ['paragraphe',    u'Éditorial'],
                'annonces'      : ['annonces',      'Annonces'],
                'bistro'        : ['liste',         u'Échos du bistro',     2],
                'adq'           : ['liste',         u'Articles de qualité', 3],
                'propositions adq'  : ['liste',     'Propositions',         4],
                'ba'            : ['liste',         'Bons articles',        3],
                'propositions ba'   : ['liste',     'Propositions',         4],
                u'actualités'       : ['actualites', u'Actualités'],
                u'médias'       : ['liste',         'Revue de presse',      2],
                'entretien'     : ['signe',         'Interview',            'entretien avec'],
                'tribune'       : ['signe',         'Tribune',              'signature'],
                'histoire'      : ['paragraphe',    'Histoire'],
                'citation'      : ['paragraphe',    'Citation'],
                'planete'       : ['planete',       u'Planète Wikimédia'],
                u'rédaction'    : ['redaction',     u'Rédaction']
                } # Les paramètres reconnus: ce qu'il faut en faire, titre de la section, option
        ordre_parametres = [ u'édito', 'annonces', 'bistro', 'adq', 'propositions adq', \
                'ba', 'propositions ba', u'actualités', u'médias', 'entretien', \
                'tribune', 'histoire', 'citation', 'planete', u'rédaction' ] # Ordre de placement des paramètres

        text = self.exps['='].sub(r'&#x3D;', text)
        text = self.exps['User'].sub(r'{{u|\1}}', text)
        text = self.exps['formatnum'].sub(r'\2', text)
        text = self.exps['annonces'].sub(r'* \1 : \2', text)
        text = self.exps['transclu'].sub(self.transclusion, text)
        text = self.exps['modele'].sub(self.modele, text)

        text = self.exps['ref'].sub(r' (\1)', text)
        text = BeBot.retirer( [self.exps['comment'], self.exps['image_seule'], \
                self.exps['image'], self.exps['W___'], self.exps['noinclude']], text)
        text = self.exps['W_br'].sub(r'<br />\n', text)
        text = self.exps['b'].sub(r'<b>\2</b>', text)
        text = self.exps['i'].sub(r'<i>\2</i>', text)
        text = self.exps['tableau'].sub(self.tableau, text)
        self.sommaire = '<span style="padding-left:6ex; font-weight:bolder;">Sommaire</span>\n<ol class="sommaire">\n'
        self.sommaire_index = 0

        # HEAD
        r = u'<html>\n<head>\n'
        r +=  '\t<title>Wikimag '+str(self.numero)+'</title>\n' \
            + '\t<meta http-equiv="Content-language" content="fr" />\n' \
            + '\t<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
        r +=  '<style type="text/css">\n' \
            + '\th1 { text-align:center; }\n' \
            + '\t.sommaire { padding-left:8ex; }\n' \
            + '</style>\n'
        # BODY
        r += '</head>\n<body>\n'
        r += u'<h1>' + self.html_lien( \
                u'http://fr.wikipedia.org/wiki/%s' % (self.mag.title()), \
                'Wikimag '+str(self.numero)) \
                + u' (semaine ' + self.semaine + u')</h1>\n'
        r += self.html_paragraphe(u'Du lundi ' + self.lundi.strftime("%e %B %Y").lstrip(' ') \
                + ' au dimanche ' + (self.lundi + datetime.timedelta(days=6)).strftime("%e %B %Y").lstrip(' '))
        r += '<div style="float:right;"><img src="http://upload.wikimedia.org/wikipedia/commons/7/72/Wikimag-fr.svg" alt="Logo Wikimag" width="120px" /></div>\n'
        if self.epreuve: r += self.html_paragraphe(u'<b style="font-color:red;">Ce mail est une épreuve du prochain mag.</b>')
        r += self.sommaire_jocker

        params = {} # Les paramètres du mag
        params['planete'] = '&nbsp;' # Paramètre ajouté même s'il est vide
        a = re.split(self.exps['split'], text)
        for i in range(1, len(a), 2):
            params[a[i].lower()] = a[i+1].rstrip('\n').strip(' ')

        for p in ordre_parametres:
            if p == 'adq':
                r += self.html_chapitre(u'Articles labellisés cette semaine')
            if params.has_key(p) and len(params[p]) > 0:
                action = parametres[p][0]
                titre = parametres[p][1]
                if   action == 'paragraphe':
                    r += self.html_chapitre(titre)
                    r += self.html_paragraphe(params[p])
                elif action == 'liste':
                    r += self.html_chapitre(titre, parametres[p][2])
                    r += self.html_liste(params[p])
                elif action == 'signe' and len(params[parametres[p][2]]) > 0: # Signé : Entretien, Tribune
                    r += self.html_chapitre(titre)
                    r += self.html_paragraphe(params[p])
                    r += self.html_paragraphe(self.exps['html'].sub(r'', params[parametres[p][2]]), 'text-align:right;')
                elif action == 'annonces':
                    r += self.html_chapitre(titre)
                    tmp = self.html_liste(self.exps['html'].sub(r'', params[p]))
                    r += self.exps[p].sub(r'\1 : \2', tmp)
                elif action == 'actualites':
                    r += self.html_chapitre(titre)
                    q = params[p]
                    if self.exps['W_liste'].search(q):
                        r += self.html_liste(q)
                    else:
                        r += self.html_paragraphe(q)
                elif action == 'planete':
                    r += self.html_chapitre(titre)
                    r += self.html_paragraphe(u'Ce qui se dit dans ' \
                            + self.html_lien(u'http://fr.planet.wikimedia.org', u'la planète wikimédia') + u'.')
                    r += self.html_liste(params[p].rstrip('}'))
                elif action == 'redaction':
                    r += self.html_chapitre(titre)
                    p = self.exps['html'].sub(r'\2', params[p])
                    r += self.html_paragraphe(u'Les membres de la rédaction pour ce numéro : '+ \
                            BeBot.retirer([self.exps['User talk']], p) )
        r += self.html_paragraphe(self.disclaimer)

        r = self.remplacer_les_liens(r)
        r = self.exps['sommaire'].sub(self.sommaire+'</ol>\n', r)
        return r + u'</body>\n</html>'

    def html_liste(self, param):
        """ Créer une liste au format html """
        r = u'<ul>\n'
        for l in re.finditer(self.exps['liste'], param):
            r += u'<li>' + l.group(1) + u'</li>\n'
        r += u'</ul>\n'
        if len(r) > 11:
            return r
        else:
            return '' # Rien de plus que la paire <ul>

    def html_lien(self, cible, nom, url=True):
        """ Créer un lien au format html """
        if (len(nom) == 0):
            nom = u'[lien]'
        if url:
            cible = self.exps['http'].sub(r'\1:', urllib.quote(cible.encode('utf8')))
        return u'<a href="' + cible + u'">' + nom + u'</a>'

    def html_chapitre(self, nom, niveau=2):
        """ Créer un chapitre au format html """
        #nom = self.exps['html'].sub(r'\2', nom)
        if niveau == 2:
            self.sommaire_index += 1
            self.sommaire += '\t<li>'+self.html_lien(u'#chap'+str(self.sommaire_index), nom, url=False)+'</li>\n'
            nom = '<a name="chap%i">%s</a>' % (self.sommaire_index, nom)
        return u'\n<h'+str(niveau)+u'>' + nom + u'</h'+str(niveau)+u'>\n'

    def html_paragraphe(self, text, style=''):
        """ Créer un paragraphe au format html """
        if len(style) > 0:
            style = ' style="%s"' % style
        return u'<p'+style+'>'+text+u'</p>\n'

    def run(self):
        # Fichier de configuration
        conf = self.conf
        if 'mailinglist' not in conf:
            conf['mailinglist'] = u'a@a.com'
            self.debug = True
        if 'from' not in conf:
            pywikibot.error(u"fichier de configuration incomplet ; manque l'expéditeur d'origine")
            sys.exit(3)
        if 'mode' not in conf:
            conf['mode'] = 'text'
        if self.debug:
            pywikibot.output(u"# Mode debug ; pas de publication")

        pagetmp = pywikibot.Page(self.site, self.tmp)
        # Numéro du mag
        num = re.compile(u"\|numéro *= *(\d+)", re.LOCALE|re.UNICODE)
        m = num.search(self.mag.text)
        if m is not None:
            self.numero = m.group(1)

        # Génération du message
        if conf['mode'] == "text":
            text = self.gen_plaintext(pagetmp)
            if self.debug : pywikibot.output(text)
            msg = MIMEText(text.encode('utf-8'), 'plain', 'utf8')
        elif conf['mode'] == "html":
            text = self.gen_html().encode('utf-8')
            if self.debug : pywikibot.output(text)
            msg = MIMEText(text, 'html', 'utf8')
        elif conf['mode'] == "multi":
            msg = MIMEMultipart('alternative', '-==_Partie_57696B696D6167204265426F74')
            text = self.gen_plaintext(pagetmp)
            if self.debug : pywikibot.output(text)
            msg1 = MIMEText(text.encode('utf-8'), 'plain', 'utf8')
            msg.attach(msg1)
            text = self.gen_html().encode('utf-8')
            if self.debug : pywikibot.output(text)
            msg2 = MIMEText(text, 'html', 'utf8')
            msg.attach(msg2)
        else:
            pywikibot.error(u"mode d'envoi du mail inconnu (text, html ou multi)")
            sys.exit(4)

        # Publication
        msg['From'] = conf['from']
        if self.epreuve:
            msg['To'] = conf['epreuve']
        else:
            msg['To'] = conf['mailinglist']
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = u'#%s, semaine %s - %s' % \
                (self.numero, self.semaine, \
                 unicode(self.lundi_pre.strftime("%e %b %Y").lstrip(' '), 'utf-8') )
        if self.epreuve: msg['Subject'] += u' # ÉPREUVE'
        f = open(self.fichier_mail, "w")
        f.write(msg.as_string())
        f.close()
        if not self.debug:
            pywikibot.output(u"# Publication sur la mailing list")
            try:
                cmd = u'cat %s | mail -s "%s" %s' % (self.fichier_mail, msg['Subject'], msg['To'])
                os.system(cmd)
            except:
                pywikibot.error(u"Erreur l'ors de l'envoie du mail")

def main():
    epreuve = False
    if len(sys.argv) in (2, 3):
        fichier_conf = sys.argv[1]
        if len(sys.argv) == 3 and sys.argv[2] == u'-e':
            epreuve = True
    else:
        fichier_conf = u''
    if os.path.exists(fichier_conf):
        site = pywikibot.getSite()
        mw = MailWikimag(site, fichier_conf, epreuve)
        mw.run()
    else:
        pywikibot.output(u"Argument invalide: Ce script attend un fichier de configuration comme premier argument (voir doc).")

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
