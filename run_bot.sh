#!/bin/bash
# > Lance le script d'un bot
# Paramètre 1 : nom du bot
# Paramètre 2 : nom du script
# Paramètre 3 : arguments
export PYTHONPATH=$HOME/rewrite
export LC_ALL="fr_FR.UTF-8"
export WP_BOT_FR="$HOME/wikipedia-bot-fr"
echo -ne "\n%%%%% $2 %% "
echo `date`
`python $WP_BOT_FR/$1/$2 $3 $4 $5 $6 $7 $8 $9`
#`cronsub -s bebot python2.6 $1/$2 $3 $4 $5 $6 $7 $8 $9`
echo `date`

