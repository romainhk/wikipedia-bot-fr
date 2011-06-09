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
        Publie une version mail du wikimag

        Nécessite en argument l'adresse d'un fichier de configuration du type :
mailinglist=    # sur laquel on va publier le mag (mode debug si omis)
epreuve=        # adresse mail des relecteurs
from=           # adresse de l'expédieur, truc@toto.fr
#mode=          # (facultatif) format d'envoi : text (*), html ou multi
#semaine=       # (facultatif) forcer l'usage d'une semaine en particulier ; pratique pour le debug
        L'option finale -e permet de faire une épreuve (tirage limité aux relecteurs)

        TODO
        gérer les interwiki/interlangue
        transclusion complète ?
        html : inclure les images ?
        problème avec les descriptions d'images contenant un lien : [[File:Welcome2WP French WEB.pdf|140px|thumb|right|[[:File:Welcome2WP French WEB.pdf|Feuilletez-moi !]] ahaha.]]
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

        self.sommaire_jocker = '###141### SOMMAIRE ###592###'
        self.exps = {
                'split'     : re.compile("\|([\w \xe9]+?)=", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'sommaire'  : re.compile(self.sommaire_jocker, re.LOCALE|re.UNICODE),
                'W_liste'   : re.compile("^\s*\*", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'http'      : re.compile("(http)%3A", re.LOCALE|re.UNICODE|re.MULTILINE),
                'html'      : re.compile("<(?P<balise>\w+)[^<>]*>(.*?)</(?P=balise)>", re.LOCALE|re.UNICODE|re.DOTALL),
                'comment'   : re.compile("<!--(.*?)-->", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'center'    : re.compile("<center>(.*?)</center>", re.LOCALE|re.UNICODE|re.DOTALL),
                'hr'        : re.compile("<hr[ /]*>", re.LOCALE|re.UNICODE),
                'br'        : re.compile("<br[ /]*>", re.LOCALE|re.UNICODE),
                'W_br'      : re.compile("\n\n", re.LOCALE|re.UNICODE|re.MULTILINE),
                'annonces'  : re.compile("\*? ?\{\{Annonce[ \w\xe9]*\|(\d+)\|(.+?)\}\}", re.LOCALE|re.UNICODE|re.IGNORECASE),
                #'image'     : re.compile("\[\[(?:Image|File|Fichier):.*?(\[{1,2})?.+?(?(1)\]).*?\]\]\s*", re.LOCALE|re.UNICODE|re.IGNORECASE|re.DOTALL),
                'image'     : re.compile("\[\[(?:Image|File|Fichier):([^\]]+)\]\]\s*", re.LOCALE|re.UNICODE|re.IGNORECASE),
                'lien_ext'  : re.compile("\[(http:[^\] ]+) ?([^\]]*)\]", re.LOCALE|re.UNICODE),
                'lien_int'  : re.compile("\[\[([^\]\|]+)\|?([^\]]*)\]\]", re.LOCALE|re.UNICODE),
                'lien_intA' : re.compile("\[\[([^\]\|]+)\]\]", re.LOCALE|re.UNICODE),
                'label'     : re.compile("\{\{[aA]-label\|([^\}]+)\}\}", re.LOCALE|re.UNICODE),
                'modele'    : re.compile("\{\{([^\|\}:]*)\|?([^\}:]*)\}\}", re.LOCALE|re.UNICODE),
                'formatnum' : re.compile("\{\{(formatnum):([^\}:]*)\}\}", re.LOCALE|re.UNICODE),
                'quote'     : re.compile("(?P<quote>'{2,5})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'b'         : re.compile("(?P<quote>'{3})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'i'         : re.compile("(?P<quote>'{2})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'liste'     : re.compile("\*\s?(.*)", re.LOCALE|re.UNICODE),
                #'W_uma'     : re.compile("\{\{[uma][']*\|(\w+)\}\}", re.LOCALE|re.UNICODE),
                'User'      : re.compile("\[\[Utilisateur:(\w+)(\|\w+)?\]\]", re.LOCALE|re.UNICODE|re.IGNORECASE),
                'User talk' : re.compile("\[\[Discussion utilisateur:(\w+)(\|\w+)?\]\]", re.LOCALE|re.UNICODE|re.IGNORECASE),
                'W___'      : re.compile("__[A-Z]+__\s*", re.LOCALE),
                'transclu'  : re.compile("\{\{([^\|\}]+)\}\}", re.LOCALE|re.UNICODE),
                'noinclude' : re.compile("<noinclude>(.*?)</noinclude>\s*", re.LOCALE|re.UNICODE|re.DOTALL)
                } # Toute les expressions qui seront détectée
        self.disclaimer = u'Des erreurs ? Consulter [[%s|la dernière version sur le wiki]]' % self.mag.title() # Message de fin
        self.fichier_mail = u'./wikimag_mail.tmp' # Fichier temporaire pour le mail
        self.mode = u'' # Mode de génération en cours

    def url_(self, match):
        return self.exps['http'].sub(r'\1:', urllib.quote(match.group(1).encode('utf8')))

    def transclusion(self, match):
        """ Traitement spécifique pour les transclusions
        """
        page = match.group(1)
        if page[0] == u'/':
            page = self.mag.title() + page
        elif not pywikibot.Page(self.site, page).exists():
            return u'' #page
        # Lien
        #intitule = u'Retrouvez la page « %s » sur le wiki'%page.split('/').pop()
        #if self.mode == u'html':
        #    return self.html_lien('http://fr.wikipedia.org/wiki/'+page, u'[ '+intitule+u' ]')
        #else:
        #    return u'[ %s : %shttp://fr.wikipedia.org/wiki/%s%s ]' % \
        #            (intitule, page.split('/').pop(), self.jocker, page, self.ajocker)

        # Recopiage
        text = pywikibot.Page(self.site, page).text
        text = self.exps['noinclude'].sub(r'', text)
        return text

    def modele(self, match):
        """ Traitement spécifiques pour les modèles à paramètres
        """
        nom = match.group(1).lower()
        params = match.group(2).split('|')
        if nom in ('clin', 'pdf', 'sourire'):
            return u''  # rien
        elif nom in ('er', 'u', "u'", 'm', 'a', 'l', 'citation'):
            return params[0]  # tel-quel
        elif nom == u'unité':
            return params[0] + u' ' + params[1]
        else:
            return u''

    def retirer(self, exprs, text):
        """ Retire les ER de exprs dans text """
        for a in exprs:
            text = a.sub(r'', text)
        return text

    def gen_plaintext(self, pagetmp):
        """ Génération du format texte brut
        """
        self.mode = u'text'
        self.jocker = u'%$!' #Pour repérer les liens http
        self.ajocker = BeBot.reverse(self.jocker)
        modele_de_presentation = u'Wikimag_par_mail'
        modele = re.compile("\{\{[cC]omposition wikimag", re.LOCALE)

        pagetmp.text = modele.sub(u'{{subst:%s|' % modele_de_presentation, self.mag.text)
        try:
            pagetmp.save(comment=u'Préparation pour le mail du Wikimag', minor=False)
        except:
            pywikibot.error(u"Impossible d'effectuer la substitution")
            sys.exit(2)
        if self.epreuve: text = u'CE MAIL EST UNE ÉPREUVE DU PROCHAIN MAG.\n' + text
        text = pywikibot.Page(self.site, self.tmp).text + self.disclaimer
        text = self.exps['transclu'].sub(self.transclusion, text)
        text = self.retirer( [self.exps['br'],self.exps['image'],self.exps['W___'], \
                self.exps['noinclude']], text)
        text = self.exps['User'].sub(r'{{u|\1}}', text)
        text = self.exps['annonces'].sub(r'* \1 : \2', text)
        # Liens externes
        text = self.exps['lien_ext'].sub(r'\2 [ %s\1%s ]' % ( self.jocker, self.ajocker), text)
        # Liens internes
        text = self.exps['lien_intA'].sub(r'[[\1|\1]]', text)
        text = self.exps['lien_int'].sub(r'\2 ( %shttp://fr.wikipedia.org/wiki/\1%s )' \
                % ( self.jocker, self.ajocker), text)
        text = self.exps['label'].sub(r'%shttp://fr.wikipedia.org/wiki/\1%s' % ( self.jocker, self.ajocker), text)

        text = self.exps['hr'].sub(r'-----  -----  -----', text)
        text = self.exps['formatnum'].sub(r'\2', text)
        text = self.exps['modele'].sub(self.modele, text)
        text = self.exps['center'].sub(r'    \1', text)
        text = self.exps['html'].sub(r'\2', text)
        text = self.exps['quote'].sub(r'\2', text)
        # Modification des liens http ( -> url_() )
        r = re.compile("%s(.*?)%s" % ( re.escape(self.jocker), re.escape(self.ajocker)), re.LOCALE|re.UNICODE)
        text = r.sub(self.url_, text)
        return text;

    def gen_html(self):
        """ Génération au format Html
        """
        self.mode = u'html'
        text = self.mag.text
        if self.epreuve: text = u'<b style="font-color:red;">Ce mail est une épreuve du prochain mag.</b>\n' + text

        text = self.exps['transclu'].sub(self.transclusion, text)
        text = self.retirer( [self.exps['comment'],self.exps['image'],self.exps['W___'], \
                self.exps['noinclude']], text)
        text = self.exps['User'].sub(r'{{u|\1}}', text)
        text = self.exps['formatnum'].sub(r'\2', text)
        text = self.exps['label'].sub(r'[[\1]]', text)
        text = self.exps['W_br'].sub(r'<br />\n', text)
        text = self.exps['b'].sub(r'<b>\2</b>', text)
        text = self.exps['i'].sub(r'<i>\2</i>', text)
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
        r += self.html_paragraphe(u'Du lundi ' + self.lundi.strftime("%e %b %Y").lstrip(' ') \
                + ' au dimanche ' + (self.lundi + datetime.timedelta(days=6)).strftime("%e %b %Y").lstrip(' '))
        r += '<div style="float:right;"><img src="http://upload.wikimedia.org/wikipedia/commons/7/72/Wikimag-fr.svg" alt="Logo Wikimag" width="120px" /></div>\n'
        r += self.sommaire_jocker

        params = {} # Les paramètres du mag
        a = re.split(self.exps['split'], text)
        for i in range(1, len(a), 2):
            params[a[i].lower()] = a[i+1].rstrip('\n').strip(' ')

        if (len(params[u'édito']) > 0):
            r += self.html_chapitre(u'Édito')
            r += self.html_paragraphe(params[u'édito'])
        if (len(params[u'annonces']) > 0):
            r += self.html_chapitre(u'Annonces')
            tmp = self.html_liste(self.exps['html'].sub(r'', params[u'annonces']))
            r  += self.exps['annonces'].sub(r'\1 : \2', tmp)
        if (len(params[u'bistro']) > 0):
            r += self.html_chapitre(u'Échos du bistro')
            r += self.html_liste(params[u'bistro'])
        r += self.html_chapitre(u'Articles labellisés cette semaine')
        if (len(params[u'adq']) > 0):
            r += self.html_chapitre(u'Articles de qualité', 3)
            r += self.html_liste(params[u'adq'])
        if (len(params[u'propositions adq']) > 0):
            r += self.html_chapitre(u'Propositions', 4)
            r += self.html_liste(params[u'propositions adq'])
        if (len(params[u'ba']) > 0):
            r += self.html_chapitre(u'Bon articles', 3)
            r += self.html_liste(params[u'ba'])
        if (len(params[u'propositions ba']) > 0):
            r += self.html_chapitre(u'Propositions', 4)
            r += self.html_liste(params[u'propositions ba'])
        #image gauche / image droite ------
        if (len(params[u'actualités']) > 0):
            r += self.html_chapitre(u'Actualités')
            p = params[u'actualités']
            if self.exps['W_liste'].search(p):
                r += self.html_liste(p)
            else:
                r += self.html_paragraphe(p)
        if (len(params[u'médias']) > 0):
            r += self.html_chapitre(u'Wikipédia dans les médias')
            r += self.html_liste(params[u'médias'])
        if (len(params[u'entretien'])>0 and (len(params[u'entretien avec'])>0) ):
            r += self.html_chapitre(u'Entretien')
            r += self.html_paragraphe(params[u'entretien'])
            r += self.html_paragraphe(self.exps['html'].sub(r'', params[u'entretien avec']), 'text-align:right;')
        if (len(params[u'tribune'])>0 and (len(params[u'signature'])>0) ):
            r += self.html_chapitre(u'Tribune')
            r += self.html_paragraphe(params[u'tribune'])
            r += self.html_paragraphe(self.exps['html'].sub(r'', params[u'signature']), 'text-align:right;')
        #BROIN -----
        if (len(params[u'histoire']) > 0):
            r += self.html_chapitre(u'Histoire')
            r += self.html_paragraphe(params[u'histoire'])
        if (len(params[u'citation']) > 0):
            r += self.html_chapitre(u'Citation de la semaine')
            r += self.html_paragraphe(params[u'citation'])
        #astuce ----
        r += self.html_chapitre(u'Planète Wikimédia')
        r += self.html_paragraphe(u'Ce qui se dit dans ' \
                + self.html_lien(u'http://fr.planet.wikimedia.org', u'la planète wikimédia') + u'.')
        if (len(params[u'planete']) > 0):
            r += self.html_liste(params[u'planete'].rstrip('}'))
        if (len(params[u'rédaction']) > 0):
            r += self.html_chapitre(u'Rédaction')
            p = self.exps['html'].sub(r'\2', params[u'rédaction'])
            r += self.html_paragraphe(u'Les membres de la rédaction pour ce numéro : '+ \
                    self.retirer([self.exps['User talk']], p) )
        r += self.html_paragraphe(self.disclaimer)

        # Remplacement des liens
        for lien in re.finditer(self.exps['lien_ext'], r):
            b = r.partition(lien.group(0))
            r = b[0] + self.html_lien(lien.group(1), lien.group(2)) + b[2]
        for lien in re.finditer(self.exps['lien_int'], r):
            b = r.partition(lien.group(0))
            nom = lien.group(2)
            if (len(nom) == 0):
                nom = lien.group(1)
            r = b[0] + self.html_lien(u'http://fr.wikipedia.org/wiki/'+lien.group(1), nom) + b[2]
        r = self.exps['modele'].sub(self.modele, r)
        # Sommaire
        r = self.exps['sommaire'].sub(self.sommaire+'</ol>\n', r)
        return r + u'</body>\n</html>'

    def html_liste(self, param):
        """ Créer une liste au format html """
        r = u'<ul>\n'
        for l in re.finditer(self.exps['liste'], param):
            r += u'<li>' + l.group(1) + u'</li>\n'
        r += u'</ul>\n'
        return r

    def html_lien(self, cible, nom, url=True):
        """ Créer un lien au format html """
        if (len(nom) == 0):
            nom = u'[lien]'
        if url:
            cible = self.exps['http'].sub(r'\1:', urllib.quote(cible.encode('utf8')))
        return u'<a href="' + cible + u'">' + nom + u'</a>'

    def html_chapitre(self, nom, niveau=2):
        """ Créer un chapitre au format html """
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
        if self.epreuve: msg['Subject'] += u' // ÉPREUVE'
        f = open(self.fichier_mail, "w")
        f.write(msg.as_string())
        f.close()
        if not self.debug:
            pywikibot.output(u"# Publication sur la mailing liste")
            try:
                cmd = u'cat %s | mail -s "%s" %s' % (self.fichier_mail, msg['Subject'], conf['mailinglist'])
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
