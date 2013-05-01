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
 * @brief Permet de r�cup�rer le nom de la session sur laquelle est ouvert le programme
 * @return char : le nom de la session
 */

/* types =============================================================== */
/* structures ========================================================== */
/* public variables ==================================================== */
/* constants =========================================================== */
/* internal public functions =========================================== */

void viderBuffer(void);
/**
 *@fn viderBuffer(void);
 *@brief permet de vider le buffer apr�s une entr�e utilisateur (stdin)
 */
 
/* inline public functions  ============================================ */
/* entry points ======================================================== */

char* argument(const char* nom, char* req, char* arg, bool obligatoire);
/**
 * @fn argument(const char* nom, char* req, char* arg, bool obligatoire);
 * @brief permet de r�cup�rer la valeur d'un argument pass�e en param�tre
 * @param nom : le nom du param�tre
 * @param req : la cha�ne dans laquelle la fonction doit extraire la valeur du param�tre
 * @param arg : la cha�ne dans laquelle la fonction doit copier la valeur du param�tre
 * @param obligatoire : si cette valeur est � true, la fonction demande � l'utilisateur de saisir la valeur du param�tre s'il n'est pas contenu dans la requ�te
 * @return l'adresse de la cha�ne arg
 */

#endif


void ecrireFichier(const char* adresse, const char* str);

void saisieHidden(char* str);
void logs(const char* adresse, const char* req);

char* variable(const char* nom, const char* req, char*  var);
time_t completerDate(char* chaine);
bool confirmation(char* message);
