#!/usr/bin/python
# -*- coding: utf-8  -*-
import BeBot, re, pywikibot
site = pywikibot.getSite()

pywikibot.output(BeBot.userdailycontribs(site, u'Romainhk'))

