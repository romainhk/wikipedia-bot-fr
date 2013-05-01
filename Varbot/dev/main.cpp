/*location: dev/main.cpp*/

/* includes ============================================================ */

#include <cstdio>
#include <cstdlib>
#include <string.h>
#include <time.h>
#include <termios.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <algorithm>

#include "constantes.h"
#include "main.h"
#include "api/io.h"
#include "api/api.h"

/* macros ============================================================== */

using namespace std;

/* types =============================================================== */
/* structures ========================================================== */
/* public variables ==================================================== */

char pseudo[128];        //Pseudo de l'utilisateur = "" si pas connecté
time_t dateInscr;        //Date d'inscription de l'utilisateur

/* constants =========================================================== */
/* internal public functions =========================================== */
/* private variables =================================================== */
/* private functions =================================================== */
/* entry points ======================================================== */

int main(void)
{
    /*Initialisation du programme*/
	char req[4096] = "start";
	pseudo[0] = '\0';
	ecrireFichier(fichierLogs, "\n");
	logs(fichierLogs, req);
	ecrireFichier(fichierLogs, "\n");
	
	/*Terminal utilisateur*/
	while(1)
	{
		printf(":");
		fgets(req,256,stdin);
		logs(fichierLogs, req);
		analyse(req);
#if DEBUGNORM==1
        getchar();
#endif
		/*Nettoyage des requetes wget*/
		system("rm -rf fr.wikipedia.org/");
		system("rm -f *.php*");
		system("rm -f *.gz");
	}

	return 0;
}



