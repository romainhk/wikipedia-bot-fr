/*location: dev/lib/fonctions.h*/

#ifndef H_VARBOT_FONCTIONS_2013
#define H_VARBOT_FONCTIONS_2013



/* includes ============================================================ */

#include <cstdio>
#include <cstdlib>
#include <string.h>
#include <time.h>
#include <termios.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <algorithm>

/* macros ============================================================== */
/* types =============================================================== */
/* structures ========================================================== */
/* public variables ==================================================== */
/* constants =========================================================== */
/* internal public functions =========================================== */
/* inline public functions  ============================================ */
/* entry points ======================================================== */


void help(char* req);
/**
 * @fn help(char* req);
 * @command help
 * @command man
 * @brief Affiche l'aide
 * @param (optionnel) char* : une fonction particulière qui nécessite documentation
 * @return ne renvoie rien
 */


void login(char* req);
/**
 * @fn login(char* req);
 * @command login
 * @brief Permet de se connecter sur fr.wikipedia.org
 * @param --login char* : le login de l'utilisateur
 * @return ne renvoie rien
 */


void logout(void);
/**
 * @fn logout(void);
 * @command logout
 * @brief Permet de se déconnecter sur fr.wikipedia.org
 * @return ne renvoie rien
 */


void sendNAM(char* req);
/**
 * @fn sendNAM(char* req);
 * @command sendNAM
 * @brief Permet d'envoyer le mensuel du projet:Arménie nommé "Des nouvelles d'Arménie"
 * @param --number char* : le numéro (sous forme d'entier) du mois
 * @return ne renvoie rien
 */



#endif
