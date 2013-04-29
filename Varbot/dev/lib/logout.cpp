/*location: dev/lib/logout.cpp*/

/* includes ============================================================ */

#include "../constantes.h"
#include "../main.h"
#include "../api/io.h"
#include "fonctions.h"

/* macros ============================================================== */
/* types =============================================================== */
/* structures ========================================================== */
/* public variables ==================================================== */
/* constants =========================================================== */
/* internal public functions =========================================== */
/* private variables =================================================== */
/* private functions =================================================== */
/* entry points ======================================================== */


//fonctions.h
void logout(void)
{
	if(strlen(pseudo) == 0)
	{
		char requete[128];
		sprintf(requete,"\tLOGOUT => NOT LOGGED IN\n");
		printf("%s",requete);
		ecrireFichier(fichierLogs, requete);
		return;
	}
	char requete[1024];
	sprintf(requete,"wget --quiet -O logout.gz %s http://fr.wikipedia.org/w/api.php?action=logout", usragent);
	system(requete);
	system("gunzip logout.gz");
	sprintf(requete,"\tLOGOUT => SUCCESS %s\n", pseudo);
	printf("%s",requete);
	ecrireFichier(fichierLogs, requete);
	system("rm -f logout");
	pseudo[0] = '\0';
}

