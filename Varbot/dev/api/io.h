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

void viderBuffer(void);
/**
 *@fn viderBuffer(void);
 *@brief permet de vider le buffer après une entrée utilisateur (stdin)
 */
 
/* inline public functions  ============================================ */
/* entry points ======================================================== */


char* argument(const char* nom, char* req, char* arg, bool obligatoire);
/**
 * @fn argument(const char* nom, char* req, char* arg, bool obligatoire);
 * @brief permet de récupérer la valeur d'un argument passée en paramètre
 * @param const char* : le nom du paramètre
 * @param char* : la chaîne dans laquelle la fonction doit extraire la valeur du paramètre
 * @param char* : la chaîne dans laquelle la fonction doit copier la valeur du paramètre
 * @param bool : si cette valeur est à true, la fonction demande à l'utilisateur de saisir la valeur du paramètre s'il n'est pas contenu dans la requête
 * @return char* l'adresse de la chaîne arg
 */

 
bool confirmation(char* message, char lettre);
/**
 *@fn confirmation(char* message);
 @brief permet de demander une confirmation à l'utilisateur sous forme d'une lettre pour confirmer (Y par exemple), toutes les autres lettres servant à signifier une infirmation7
	 la confirmation ne tient pas compte de la casse ni des lettres suivant la première, ainsi Y,y,Yes auront la même valeur pour la fonction
 @param char* : le message à afficher pour demander confirmation
 @param char : la lettre ayant pour valeur confirmation (par défaut à Y si une valeur autre qu'alphanumérique est spécifiée)
 @return bool : true si l'utilisateur a confirmé, false sinon
 */



#endif


void ecrireFichier(const char* adresse, const char* str);

void saisieHidden(char* str);
void logs(const char* adresse, const char* req);

char* variable(const char* nom, const char* req, char*  var);
time_t completerDate(char* chaine);

