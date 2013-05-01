/*location: dev/api/api.h*/

#ifndef H_VARBOT_API_2013
#define H_VARBOT_API_2013



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

void analyse(char*);
/**
 * @fn analyse(char* req);
 * @brief Analyse l'entrée utilisateur et appelle la fonction correspondante dans /lib voir :help pour plus d'infos
 * @param req l'entrée utilisateur dans son intégralité
 * @return ne renvoie rien
 */

#endif
