#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys, smtplib, os
from email.MIMEText import MIMEText
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
#utilisateur=    # (facultatif) nom du compte sur le serveur smtp si différent du from

        TODO : * gérer les interwiki/interlangue
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
        self.jocker = u'%$!' #Pour repérer les liens http
        self.ajocker = BeBot.reverse(self.jocker)

    def url_(self, match):
        return match.group(1).replace(' ', '_')
        #return match.group(1).replace(' ', '_').replace("'", "\\'").replace('"', '\\"')

    def run(self):
        # Préparation du contenu
        modele = re.compile("\{\{[cC]omposition wikimag", re.LOCALE)
        pagetmp = pywikibot.Page(self.site, self.tmp)
        pagetmp.text = modele.sub(u'{{subst:%s|' % self.modele_de_presentation, self.mag.text)
        # Numéro du mag
        num = re.compile(u"\|numéro *= *(\d+)", re.LOCALE|re.UNICODE)
        m = num.search(pagetmp.text)
        if m is not None:
            self.numero = m.group(1)
        try:
            pagetmp.save(comment=u'Préparation du mail pour le Wikimag', minor=False)
        except:
            pywikibot.error(u"Impossible d'effectuer la substitution")
            sys.exit(2)

        text = pywikibot.Page(self.site, self.tmp).text
        r = re.compile(u"<br[ /]*>", re.LOCALE)
        text = r.sub(r'', text)
        # Annonces
        r = re.compile("\{\{[Aa]nnonce[ \w]*\|(\d+)\|(.+?)\}\}", re.LOCALE|re.UNICODE)
        text = r.sub(r'* \1 : \2', text)
        # Images
        r = re.compile("\[\[([iI]mage|[fF]ile|[fF]ichier):[^\]]+\]\]\s*", re.LOCALE|re.UNICODE)
        text = r.sub(r'', text)
        # Liens externes
        r = re.compile("\[(http:[^\] ]+) ([^\]]+)\]", re.LOCALE|re.UNICODE)
        text = r.sub(r'\2 [ %s\1%s ]' % ( self.jocker, self.ajocker), text)
        r = re.compile("\[(http:[^\] ]+)\]", re.LOCALE|re.UNICODE)
        text = r.sub(r'%s\1%s' % ( self.jocker, self.ajocker), text)
        # Liens internes
        #Pas d'interwiki, ni d'interlangue
        r = re.compile("\[\[([^\]\|]+)\|([^\]]+)\]\]", re.LOCALE|re.UNICODE)
        text = r.sub(r'\2 ( %shttp://fr.wikipedia.org/wiki/\1%s )' % ( self.jocker, self.ajocker), text)
        r = re.compile("\[\[([^\]]+)\]\]", re.LOCALE|re.UNICODE)
        text = r.sub(r'%shttp://fr.wikipedia.org/wiki/\1%s' % ( self.jocker, self.ajocker), text)
        # Modification des liens http ( -> url_() )
        r = re.compile("%s(.*?)%s" % ( re.escape(self.jocker), re.escape(self.ajocker)), re.LOCALE|re.UNICODE)
        text = r.sub(self.url_, text)
        #pywikibot.output(text)

        conf = BeBot.fichier_conf(self.conf_mail)
        if 'from' not in conf or 'mailinglist' not in conf or 'serveur' not in conf or 'port' not in conf:
            pywikibot.error(u"fichier de configuration incomplet")
            sys.exit(3)
        if 'utilisateur' not in conf:
            conf['utilisateur'] = conf['from'].split('@', 1)[0]
        # Publication du mail sur la ml
        msg = MIMEText(text.encode('utf-8'), 'plain', 'utf8')
        msg['From'] = conf['from']
        msg['To'] = conf['mailinglist']
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = u'#%s, semaine %s - %s' % \
                (self.numero, self.semaine, \
                 self.lundi_pre.strftime("%e %b %Y").lstrip(' ') )
        try:
            smtp = smtplib.SMTP(conf['serveur'], conf['port'])
            smtp.starttls()
            smtp.login(conf['utilisateur'], conf['motdepasse'])
            smtp.sendmail(conf['from'], conf['mailinglist'], msg.as_string())
            smtp.quit()
        except smtplib.SMTPException, mssg:
            print mssg
        #pywikibot.output(msg.as_string())

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
        pywikibot.output(u"Argument invalide: Ce script attend l'adresse d'un fichier de configuration comme unique argument (voir doc).")

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
