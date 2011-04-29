#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys, smtplib, os, urllib
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
mailinglist=    # sur laquel on va publier le mag
serveur=        # smtp à utiliser, smtp.
port=
from=           # adresse de l'expédieur, truc@toto.fr
motdepasse=
#utilisateur=   # (facultatif) nom du compte sur le serveur smtp si différent du from
#mode=          # (facultatif) format d'envoi : text (*), html ou multi

        TODO  gérer les interwiki/interlangue
    """
    def __init__(self, site, fichier_conf):
        self.site = site
        self.conf_mail = fichier_conf
        self.tmp = u'Utilisateur:BeBot/MailWikimag'
        self.modele_de_presentation = u'Wikimag_par_mail'
        date = datetime.date.today()
        self.lundi = date - datetime.timedelta(days=date.weekday())
        self.lundi_pre = self.lundi - datetime.timedelta(weeks=1)
        self.semaine = self.lundi_pre.strftime("%W").lstrip('0')
        self.mag = pywikibot.Page(site, u'Wikipédia:Wikimag/%s/%s' % \
                (self.lundi_pre.strftime("%Y"), self.semaine) )
        self.numero = 0
        if self.mag.isRedirectPage():
            self.mag = self.mag.getRedirectTarget()

        self.sommaire_jocker = '###141### SOMMAIRE ###592###'
        self.exps = {
                'split'     : re.compile("\|([\w \xe9]+?)=", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'br'        : re.compile("<br[ /]*>", re.LOCALE|re.UNICODE),
                'W_br'      : re.compile("\n\n", re.LOCALE|re.UNICODE|re.MULTILINE),
                'http'      : re.compile("(http)%3A", re.LOCALE|re.UNICODE|re.MULTILINE),
                'annonces'  : re.compile("\*? ?\{\{[Aa]nnonce[ \w\xe9]*\|(\d+)\|(.+?)\}\}", re.LOCALE|re.UNICODE),
                'image'     : re.compile("\[\[([iI]mage|[fF]ile|[fF]ichier):[^\]]+\]\]\s*", re.LOCALE|re.UNICODE),
                'lien_ext'  : re.compile("\[(http:[^\] ]+) ?([^\]]*)\]", re.LOCALE|re.UNICODE),
                'lien_int'  : re.compile("\[\[([^\]\|]+)\|?([^\]]*)\]\]", re.LOCALE|re.UNICODE),
                'modele'    : re.compile("\{\{[^\|\}:]*[\|:]?([^\|\}:]*)\}\}", re.LOCALE|re.UNICODE),
                'html'      : re.compile("<(?P<balise>\w+)[^<>]*>(.*?)</(?P=balise)>", re.LOCALE|re.UNICODE|re.DOTALL),
                'quote'     : re.compile("(?P<quote>'{2,5})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'b'         : re.compile("(?P<quote>'{3})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'i'         : re.compile("(?P<quote>'{2})(.*?)(?P=quote)", re.LOCALE|re.UNICODE),
                'comment'   : re.compile("<!--(.*?)-->", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL),
                'liste'     : re.compile("\*\s?(.*)", re.LOCALE|re.UNICODE),
                'W_uma'     : re.compile("\{\{[uma][']*\|(\w+)\}\}", re.LOCALE|re.UNICODE),
                'sommaire'  : re.compile(self.sommaire_jocker, re.LOCALE|re.UNICODE)
                }

    def url_(self, match):
        #return match.group(1).replace(' ', '_')
        return self.exps['http'].sub(r'\1:', urllib.quote(match.group(1).encode('utf8')))

    def gen_plaintext(self, pagetmp):
        """ Génération du format texte brut
        """
        self.jocker = u'%$!' #Pour repérer les liens http
        self.ajocker = BeBot.reverse(self.jocker)
        modele = re.compile("\{\{[cC]omposition wikimag", re.LOCALE)
        pagetmp.text = modele.sub(u'{{subst:%s|' % self.modele_de_presentation, self.mag.text)
        try:
            pagetmp.save(comment=u'Préparation pour le mail du Wikimag', minor=False)
        except:
            pywikibot.error(u"Impossible d'effectuer la substitution")
            sys.exit(2)
        text = pywikibot.Page(self.site, self.tmp).text
        text = self.exps['br'].sub(r'', text)
        text = self.exps['annonces'].sub(r'* \1 : \2', text)
        text = self.exps['image'].sub(r'', text)
        # Liens externes
        text = self.exps['lien_ext'].sub(r'\2 [ %s\1%s ]' % ( self.jocker, self.ajocker), text)
        # Liens internes
        text = self.exps['lien_int'].sub(r'\2 ( %shttp://fr.wikipedia.org/wiki/\1%s )' % ( self.jocker, self.ajocker), text)

        text = self.exps['modele'].sub(r'\1', text)
        text = self.exps['html'].sub(r'\2', text)
        text = self.exps['quote'].sub(r'\2', text)
        # Modification des liens http ( -> url_() )
        r = re.compile("%s(.*?)%s" % ( re.escape(self.jocker), re.escape(self.ajocker)), re.LOCALE|re.UNICODE)
        text = r.sub(self.url_, text)
        return text;

    def gen_html(self):
        """ Génération au format Html
        """
        text = self.mag.text
        text = self.exps['b'].sub(r'<b>\2</b>', text)
        text = self.exps['i'].sub(r'<i>\2</i>', text)
        text = self.exps['comment'].sub(r'', text)
        text = self.exps['W_uma'].sub(r'\1', text)
        text = self.exps['W_br'].sub(r'<br />\n', text)
        self.sommaire = '<span style="padding-left:6ex; font-weight:bolder;">Sommaire</span>\n<ol class="sommaire">\n'

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
        r += u'<h1>Wikimag '+str(self.numero)+u' (semaine '+self.semaine+u')</h1>\n'
        r += self.html_paragraphe(u'Du lundi ' + self.lundi.strftime("%e %b %Y").lstrip(' ') \
                + ' au dimanche ' + (self.lundi + datetime.timedelta(days=6)).strftime("%e %b %Y").lstrip(' '))
        r += '<div style="float:right;"><img src="http://upload.wikimedia.org/wikipedia/commons/7/72/Wikimag-fr.svg" alt="Logo Wikimag" width="120px" /></div>\n'
        r += self.sommaire_jocker + '\n'

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
        if (len(params[u'ba']) > 0):
            r += self.html_chapitre(u'Bon articles', 3)
            r += self.html_liste(params[u'ba'])
        #image gauche / image droite ------
        if (len(params[u'actualités']) > 0):
            r += self.html_chapitre(u'Actualités')
            r += self.html_liste(params[u'actualités'])
        if (len(params[u'médias']) > 0):
            r += self.html_chapitre(u'Wikipédia dans les médias')
            r += self.html_liste(params[u'médias'])
        if (len(params[u'entretien'])>0 and (len(params[u'entretien avec'])>0) ):
            r += self.html_chapitre(u'Entretien')
            r += self.html_paragraphe(u'Entretien proposé par ' \
                    + self.exps['html'].sub(r'', params[u'entretien avec']), 'text-align:right;')
            r += self.html_paragraphe(params[u'entretien'])
        if (len(params[u'tribune'])>0 and (len(params[u'signature'])>0) ):
            r += self.html_chapitre(u'Tribune')
            r += self.html_paragraphe(params[u'tribune'])
            r += self.html_paragraphe(self.exps['html'].sub(r'', params[u'signature']), 'text-align:right;')
        #BROIN -----
        if (len(params[u'histoire']) > 0):
            r += self.html_chapitre(u'Histoire')
            r += self.html_paragraphe(params[u'histoire'])
        if (len(params[u'citation']) > 0):
            r += self.html_chapitre(u'Citation')
            r += self.html_liste(params[u'citation'])
        #astuce ----
        if (len(params[u'planete']) > 0):
            r += self.html_chapitre(u'Planète Wikimédia')
            r += self.html_liste(params[u'planete'].rstrip('}'))
        if (len(params[u'rédaction']) > 0):
            r += self.html_chapitre(u'Rédaction')
            r += self.html_paragraphe(u'Les membres de la rédaction pour ce numéro : '+params[u'rédaction'])

        # Remplacement des liens
        for lien in re.finditer(self.exps['lien_ext'], r):
            b = r.partition(lien.group(0))
            r = b[0] +  self.html_lien(lien.group(1), lien.group(2)) + b[2]
        for lien in re.finditer(self.exps['lien_int'], r):
            b = r.partition(lien.group(0))
            nom = lien.group(2)
            if (len(nom) == 0):
                nom = lien.group(1)
            r = b[0] +  self.html_lien(u'http://fr.wikipedia.org/wiki/'+lien.group(1), nom) + b[2]
        r = self.exps['modele'].sub(r'\1', r)
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
            #cible = cible.replace(' ', '_').replace("'", '%27')
            cible = self.exps['http'].sub(r'\1:', urllib.quote(cible.encode('utf8')))
        return u'<a href="' + cible + u'">' + nom + u'</a>'

    def html_chapitre(self, nom, niveau=2):
        """ Créer un chapitre au format html """
        if niveau == 2:
            self.sommaire += '\t<li>'+self.html_lien(u'#'+nom, nom, url=False)+'</li>\n'
            nom = '<a name="%s">%s</a>' % (nom, nom)
        return u'\n<h'+str(niveau)+u'>' + nom + u'</h'+str(niveau)+u'>\n'

    def html_paragraphe(self, text, style=''):
        """ Créer un paragraphe au format html """
        if len(style) > 0:
            style = ' style="'+style+'"'
        return u'<p'+style+'>'+text+u'</p>\n'

    def run(self):
        # Fichier de configuration
        conf = BeBot.fichier_conf(self.conf_mail)
        if 'from' not in conf or 'mailinglist' not in conf or 'serveur' not in conf or 'port' not in conf:
            pywikibot.error(u"fichier de configuration incomplet")
            sys.exit(3)
        if 'utilisateur' not in conf:
            conf['utilisateur'] = conf['from'].split('@', 1)[0]
        if 'mode' not in conf:
            conf['mode'] = 'text'

        pagetmp = pywikibot.Page(self.site, self.tmp)
        # Numéro du mag
        num = re.compile(u"\|numéro *= *(\d+)", re.LOCALE|re.UNICODE)
        m = num.search(self.mag.text)
        if m is not None:
            self.numero = m.group(1)

        # Génération du message
        if conf['mode'] == "text":
            text = self.gen_plaintext(pagetmp)
            msg = MIMEText(text.encode('utf-8'), 'plain', 'utf8')
        elif conf['mode'] == "html":
            text = self.gen_html()
            msg = MIMEText(text.encode('utf-8'), 'html', 'utf8')
        elif conf['mode'] == "multi":
            msg = MIMEMultipart('alternative', '-==_Partie_57696B696D6167204265426F74')
            text = self.gen_plaintext(pagetmp)
            #print text
            msg1 = MIMEText(text.encode('utf-8'), 'plain', 'utf8')
            msg.attach(msg1)
            #print self.gen_html().encode('utf-8')
            msg2 = MIMEText(self.gen_html().encode('utf-8'), 'html', 'utf8')
            msg.attach(msg2)
        else:
            pywikibot.error(u"mode d'envoi du mail inconnu (text, html ou multi)")
            sys.exit(4)

        # Publication sur la ml
        msg['From'] = conf['from']
        msg['To'] = conf['mailinglist']
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = u'#%s, semaine %s - %s' % \
                (self.numero, self.semaine, \
                 unicode(self.lundi_pre.strftime("%e %b %Y").lstrip(' '), 'utf-8') )
        try:
            smtp = smtplib.SMTP(conf['serveur'], conf['port'])
            smtp.starttls()
            smtp.login(conf['utilisateur'], conf['motdepasse'])
            smtp.sendmail(conf['from'], conf['mailinglist'], msg.as_string())
            smtp.quit()
        except smtplib.SMTPException, esmtp:
            print esmtp

def main():
    if len(sys.argv) > 1:
        fichier_conf = sys.argv[1]
    else:
        fichier_conf = u''
    if os.path.exists(fichier_conf):
        site = pywikibot.getSite()
        mw = MailWikimag(site, fichier_conf)
        mw.run()
    else:
        pywikibot.output(u"Argument invalide: Ce script attend un fichier de configuration comme unique argument (voir doc).")

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
