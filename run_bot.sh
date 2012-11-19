#!/bin/bash
# > Lance le script d'un bot
# Paramètre 1 : nom du bot
# Paramètre 2 : nom du script
# Paramètre 3..9 : arguments
export PYTHONPATH=$PYTHONPATH:$HOME/rewrite
export LC_ALL="fr_FR.UTF-8"
export WP_BOT_FR="$HOME/wikipedia-bot-fr"
export LOG="$HOME/$1.log"

echo -ne "\n%%%%% $2 %% " >> $LOG
echo `date` >> $LOG
`python2 $WP_BOT_FR/$1/$2 $3 $4 $5 $6 $7 $8 $9 &>> $LOG`
#`cronsub -s bebot python2.7 $1/$2 $3 $4 $5 $6 $7 $8 $9`
echo `date` >> $LOG

