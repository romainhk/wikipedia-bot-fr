#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys, smtplib
from email.MIMEText import MIMEText
from email.Utils import formatdate
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class MailWikimag:
    """ Mail Wikimag
        Publie une version mail du wikimag
    """
    def __init__(self, site):
        self.site = site
        self.tmp = u'Utilisateur:BeBot/MailWikimag'
        self.modele_de_presentation = u'Utilisateur:Romainhk/Souspage2'
        self.date = datetime.date.today()
        self.mag = pywikibot.Page(site, u'Wikipédia:Wikimag/%s' % \
                unicode(self.date.strftime("%Y/%W"), "utf-8"))
        # Mail
        self.mailing_list = u'romainhk@gmail.com'
        self.conf_mail = u'mail_wikimag.conf'

    def run(self):
        # Préparation du contenu du mail
        modele = re.compile("\{\{[cC]omposition wikimag", re.LOCALE)
        pagetmp = pywikibot.Page(self.site, self.tmp)
        pagetmp.text = modele.sub(u'{{subst:%s|' % self.modele_de_presentation, self.mag.text)
        try:
            pagetmp.save(comment=u'Préparation du mail pour le Wikimag', minor=False)
        except:
            pywikibot.error(u"Impossible d'effectuer la substitution")
            sys.exit(2)

        text = pywikibot.Page(self.site, self.tmp).text
        #text = u'{{annonces|4|bonjour àààà.}}\n[[Image:Salut.jpg|thumb|24px|AAAAAAA]]\n'
        #text += u'[http://fr.planet.wikimedia.org/ Planète]\n[http://meta.wikimedia.org]\n'
        #text += u'[[Nord]]\n[[Utilisateur:BeBot|Bebot]]'
        #Annonces
        r = re.compile(u"\{\{[aA]nnonces\|(\d+)\|([^\|\]]+)\}\}", re.LOCALE)
        text = r.sub(r'* \1 : \2', text)
        #Images
        r = re.compile(u"\[\[([iI]mage|[fF]ile|[fF]ichier):[^\]]+\]\]\s*", re.LOCALE)
        text = r.sub(r'', text)
        #Liens externes
        r = re.compile(u"\[(http:[^\] ]+) ([^\]]+)\]", re.LOCALE)
        text = r.sub(r'\2 [ \1 ]', text)
        r = re.compile(u"\[(http:[^\] ]+)\]", re.LOCALE)
        text = r.sub(r'\1', text)
        #Liens internes
        #Pas d'interwiki, ni d'interlangue
        r = re.compile(u"\[\[([^\]\|]+)\|([^\]]+)\]\]", re.LOCALE)
        text = r.sub(r'\2 ( http:/fr.wikipedia.org/wiki/\1 )', text)
        r = re.compile(u"\[\[([^\]]+)\]\]", re.LOCALE)
        text = r.sub(r'http:/fr.wikipedia.org/wiki/\1', text)

        conf = BeBot.fichier_conf(self.conf_mail)
        # Publication du mail sur la ml
#        mail = email.message_from_string(text)
        #text = 'testestset sdsgggéàà@@@ççÉÀÀÀÀÀ:«»«»ø~´`}]d'
        msg = MIMEText(text, 'plain', 'utf8')
        #msg = MIMEText(text, 'plain', 'iso8859-15')
        msg['From'] = conf['from']
        msg['To'] = self.mailing_list
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = u'Wikimag du %s' % \
                unicode(self.date.strftime("%e/%m/%Y - semaine %W"), "utf-8")
        try:
            smtp = smtplib.SMTP(conf['serveur'], conf['port'])
            smtp.starttls()
            smtp.login(conf['utilisateur'], conf['motdepasse'])
            smtp.sendmail(conf['from'], self.mailing_list, msg.as_string())
            smtp.quit()
        except smtplib.SMTPException, mssg:
            print mssg
        #pywikibot.output(msg.as_string())

def main():
    site = pywikibot.getSite()
    mw = MailWikimag(site)
    mw.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
