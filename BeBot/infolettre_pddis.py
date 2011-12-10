#!/usr/bin/python
# -*- coding: utf-8  -*-
import re, datetime, locale, sys
import BeBot
import pywikibot
locale.setlocale(locale.LC_ALL, '')

class Infolettre:
    """ Infolettre
        Publie une infolettre sur la page de discussion des abonnées (wikimag et RAW)
        TODO : si une lettre n'est pas prête
    """
    def __init__(self, site, infolettre):
        self.site = site
        self.infolettre = infolettre
        pywikibot.output("# Publication de l'infolettre %s" % self.infolettre)
        self.date = datetime.date.today()
        self.lundi = self.date - datetime.timedelta(days=self.date.weekday())
        self.lundi_pre = self.lundi - datetime.timedelta(weeks=1)
        self.semaine = self.lundi_pre.strftime("%W").lstrip('0')
        self.annee = self.lundi_pre.strftime("%Y")
        self.abn = {
                "wikimag" : u"Wikipédia:Wikimag/Abonnement",
                "raw"     : u"Wikipédia:Regards sur l'actualité de la Wikimedia/Inscription" }

    def adl(self):
        """ (Wikimag) Ajoute les adq/ba de la semaine à l'Atelier de Lecture
        """
        separation = u'<center><hr style="width:42%;" /></center>'
        # Infos
        split = re.compile("\|([\w \xe9]+?)=", re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
        params = {  'adq': u'', u'propositions adq' : u'',
                    'ba' : u'', u'propositions ba'  : u'' } # Les paramètres du mag
        a = re.split(split, self.mag.text)
        for i in range(1, len(a), 2):
            params[a[i].lower()] = a[i+1].rstrip('\n').strip(' ')

        # Résultat
        lumiere = pywikibot.Page(self.site, u'Wikipédia:Atelier de lecture/Lumière sur...')
        #Retrait des a-label
        alabel = re.compile("\{\{[aA]-label\|([^\}]+)\}\}", re.LOCALE|re.UNICODE)
        params['adq'] = alabel.sub(r'[[\1]]', params['adq'])
        params['propositions adq'] = alabel.sub(r'[[\1]]', params['propositions adq'])
        params['ba']  = alabel.sub(r'[[\1]]', params['ba'])
        params['propositions ba'] = alabel.sub(r'[[\1]]', params['propositions ba'])
        propositions = params['propositions adq'] + u'\n' + params['propositions ba']
        #Ajout des icones
        icone = re.compile("^\* ", re.LOCALE|re.UNICODE|re.MULTILINE)
        params['adq'] = icone.sub(r'* {{AdQ|20px}} ', params['adq'])
        params['ba']  = icone.sub(r'* {{BA|20px}} ', params['ba'])
        lumiere.text = u'[[Fichier:HSutvald2.svg|left|60px]]\nLes articles labellisés durant la semaine dernière et les nouvelles propositions au label.{{Clr}}\n' \
                + u'\n{{colonnes|nombre=3|\n' + params['adq'] + u'\n}}\n' + separation \
                + u'\n{{colonnes|nombre=3|\n' + params['ba']  + u'\n}}\n' + separation \
                + u'\n{{colonnes|nombre=3|\n' + propositions  + u'\n}}\n' \
                + u'<noinclude>\n[[Catégorie:Wikipédia:Atelier de lecture|Lumière sur...]]\n</noinclude>'
        pywikibot.output(u"# Publication sur l'Atelier de lecture")
        try:
            lumiere.save(comment=u'Maj hebdomadaire de la liste', minor=False, async=True)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de sauvegarder la liste des Adq/BA pour le Projet:Adl" )

    def message(self):
        """ (Option wikimag) Ajoute un message après le mag
        """
        pm = pywikibot.Page(self.site, u'Utilisateur:BeBot/MessageWikimag')
        #pywikibot.output("== %s/%s == (.*?) ==" % (self.annee, self.semaine))
        r = re.compile("==\s*%s/%s\s*==\s*(.*?)(\s*==)?" % (self.annee, self.semaine), re.LOCALE|re.UNICODE|re.MULTILINE|re.DOTALL)
        m = r.search(pm.text)
        if (m):
            k = m.group(1)
            if len(k) > 0:
                return k + u' '
        return ''

    def wikimag(self):
        """ Wikimag """
        self.mag = pywikibot.Page(self.site, u'Wikipédia:Wikimag/%s/%s' % (self.annee, self.semaine) )
        numero = '???'
        num = re.compile(u"\|numéro *= *(\d+)", re.LOCALE|re.UNICODE)
        m = num.search(self.mag.text)
        if m is not None:
            numero = m.group(1)

        self.resume = u'Demandez [[Wikipédia:Wikimag/%s/%s|Cannes Midi (n°%s)]]. Le tueur de Cannes frappe encore... 5 cents' \
                % (self.annee, self.semaine, numero)
        # Message à distribuer
        msg  = u"\n\n== Wikimag n°%s - Semaine %s ==\n" % (numero, self.semaine)
        msg += u"{{Wikimag message|%s|%s|%s}}\n%s~~~~" % (numero, self.annee, self.semaine, self.message())
        # Travail pour l'atelier de lecture
        self.adl()
        return msg

    def raw(self):
        """ Regards sur l'actualité de la Wikimedia """
        self.semaine = self.lundi.strftime("%W").lstrip('0')
        self.resume = u"Regards sur l'actualité de la Wikimedia - semeine %s de %s" % (self.semaine, self.annee)
        msg  = u"\n\n== Regards sur l'actualité de la Wikimedia - Semaine %s ==\n" % (self.semaine)
        msg += u"{{Regards sur l'actualité de la Wikimedia/PdD|%s|%s}}\n~~~~" % (self.annee, self.semaine)
        return msg

    def newsboy(self, lecteur, msg):
        """ Distribut l'infolettre
        """
        if lecteur.isRedirectPage():
            lecteur = lecteur.getRedirectTarget()
        lecteur.text += msg
        try:
            lecteur.save(comment=self.resume, minor=False, async=True)
        except pywikibot.Error, e:
            pywikibot.warning(u"Impossible de refourger l'infolettre à %s" % lecteur.title(withNamespace=True) )

    def run(self):
        if   self.infolettre == u"wikimag":
            msg = self.wikimag()
        elif self.infolettre == u"raw":
            msg = self.raw()
        else:
            pywikibot.output(u"Infolettre '%s' inconnue. Abandon." % self.infolettre)
            sys.exit(1)

        # Liste des abonnés
        r = re.compile(u"\*\* \{\{u\|(.+?)\}\}", re.LOCALE|re.UNICODE)
        liste = []
        for i in BeBot.page_ligne_par_ligne(self.site, self.abn[self.infolettre]):
            m = r.search(i)
            if m is not None:
                liste.append(m.group(1))

        # Distribution
        for l in liste:
            self.newsboy(pywikibot.Page(self.site, u"Utilisateur:"+l).toggleTalkPage(), msg)

def main():
    if len(sys.argv) != 2:
        lettre = u"wikimag"
    else:
        lettre = sys.argv[1].lower()
    site = pywikibot.getSite()
    bw = Infolettre(site, lettre)
    bw.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
