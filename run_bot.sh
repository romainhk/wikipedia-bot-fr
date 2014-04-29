#!/bin/bash
# > Lance le script d'un bot
# Paramètre 1 : chemin relatif du script à lancer
# Paramètre 2... : arguments
BASEDIR=$(dirname $0)
export PYTHONPATH=$PYTHONPATH:$BASEDIR/core/:$BASEDIR/core/externals
export LC_ALL="fr_FR.UTF-8"

WPBOTFR=`readlink -f $0 | sed -E "s/(.*)\/[^\/]*/\\1/"`
BOT=`echo $1|cut -d'/' -f1`
SCRIPT=`echo $1 | sed -E "s/.*\/(.*).py/\\1/"`
export LOG="$HOME/$BOT.log"
#echo $WPBOTFR
#echo $BOT
#echo $SCRIPT

echo -ne "\n%%%%% $SCRIPT %% " >> $LOG
echo `date` >> $LOG
`python2 $WPBOTFR/$@ &>> $LOG`
echo `date` >> $LOG

