/*location: dev/api/io.h*/

#ifndef H_VARBOT_IO_2013
#define H_VARBOT_IO_2013



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

#if DEBUG == 1
#define localUsername() "DEBUG"
#elif DEBUG == 0
#define localUsername() getenv("USER")
#endif
/**
 * @fn localUsername();
 * @brief Permet de récupérer le nom de la session sur laquelle est ouvert le programme
 * @return char : le nom de la session
 */

/* types =============================================================== */
/* structures ========================================================== */
/* public variables ==================================================== */
/* constants =========================================================== */
/* internal public functions =========================================== */
/* inline public functions  ============================================ */
/* entry points ======================================================== */


#endif


void ecrireFichier(const char* adresse, const char* str);
void viderBuffer(void);
void saisieHidden(char* str);
void logs(const char* adresse, const char* req);
char* argument(const char* nom, char* req, char* arg, bool obligatoire);
char* variable(const char* nom, const char* req, char*  var);
time_t completerDate(char* chaine);
bool confirmation(char* message);
