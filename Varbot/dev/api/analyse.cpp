/*location: dev/api/analyse.cpp*/

/* includes ============================================================ */

#include <time.h>

#include "../constantes.h"
#include "../main.h"
#include "io.h"
#include "api.h"
#include "../lib/fonctions.h"

/* macros ============================================================== */

using namespace std;

/* types =============================================================== */
/* structures ========================================================== */
/* public variables ==================================================== */
/* constants =========================================================== */
/* internal public functions =========================================== */
/* private variables =================================================== */
/* private functions =================================================== */
/* entry points ======================================================== */


//api.h
void analyse (char* req)
{
	if(strncmp(req,"exit",4) == 0)
	{
	    if(strlen(pseudo) != 0)
	    {
	        logout();
	    }
		exit(0);
	}
	else if(strncmp(req, "help",4) == 0)
	{
	    help(req);
	}
	else if(strncmp(req, "login",5) == 0)
	{
		login(req);
	}
	else if(strncmp(req, "logout",6) == 0)
	{
		logout();
	}
	else if(strncmp(req, "man",3) == 0)
	{
	    help(req);
	}
	else if(strncmp(req, "sendNAM",7) == 0)
	{
		sendNAM(req);
	}
}

