#!/usr/bin/python
# -*- coding: utf-8  -*-
import BeBot
import pywikibot

site = pywikibot.getSite()
page = pywikibot.Page(site, u'Utilisateur:BeBot/Test')
page.text = u''
page.save(comment=u'Login', minor=True, async=False)
