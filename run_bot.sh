#!/bin/bash
# > Lance le script d'un bot
# Paramètre 1 : chemin du script à lancer
# Paramètre 2... : arguments
export PYTHONPATH=$PYTHONPATH:$HOME/pywikibot/core
export LC_ALL="fr_FR.UTF-8"

NOMCAN=`echo $1 | sed -E "s/.*wikipedia-bot-fr\/(.*)/\\1/"`
BOT=`echo $NOMCAN|cut -d'/' -f1`
SCRIPT=`echo $NOMCAN | sed -E "s/.*\/(.*).py/\\1/"`
export LOG="$HOME/$BOT.log"
#echo $BOT
#echo $SCRIPT

echo -ne "\n%%%%% $SCRIPT %% " >> $LOG
echo `date` >> $LOG
`python2 $@ &>> $LOG`
echo `date` >> $LOG

