/*location: dev/lib/login.cpp*/

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
void login(char* req)
{
	char requete[1024];
	char chaine[256];
	char entree[1024];
	char arg[256];
	char arg2[256];
	char var[1024];
	char *trouve = NULL;


	if(strlen(pseudo) != 0)
	{
		char requete2[128];
		sprintf(requete2,"\tLOGIN => ALREADY LOGGED IN\n");
		printf("%s",requete2);
		ecrireFichier(fichierLogs, requete2);
		return;
	}
	argument(" --login ",req, arg, true);

	printf("PASSWORD : ");
	saisieHidden(chaine);

	sprintf(requete,"wget %s --save-cookies cookies.txt -O login.gz --quiet --keep-session-cookies --post-data 'lgname=%s&lgpassword=%s' http://fr.wikipedia.org/w/api.php?action=login",usragent, arg, chaine);
	system(requete);
	system("gunzip login.gz");
	FILE *reponse = fopen("login","r+");
	if(reponse != NULL)
	{
		while(fgets(entree,1024,reponse) != NULL)
		{
			trouve = variable("token=&quot;",entree, var);

			if(trouve != NULL)
			{
				sprintf(requete,"wget %s --quiet -O login.gz --load-cookies cookies.txt --save-cookies cookies.txt --keep-session-cookies --post-data 'lgname=%s&lgpassword=%s&lgtoken=%s' http://fr.wikipedia.org/w/api.php?action=login", usragent,arg, chaine,variable("token=&quot;",entree, var));
				system(requete);
				fclose(reponse);
				system("rm -f login");
				system("gunzip login.gz");
				FILE *reponse = fopen("login","r+");
				if(reponse != NULL)
				{
					trouve = NULL;
					while(fgets(entree,1024,reponse) != NULL)
					{
						trouve = variable("result=&quot;",entree, arg2);
						if(trouve != NULL)
						{
							sprintf(requete,"\tLOGIN => %s\n", variable("result=&quot;",entree, var));
							printf("%s",requete);
							ecrireFichier(fichierLogs, requete);
							if(strncmp(variable("result=&quot;",entree, var),"Success",7) == 0)
								strcpy(pseudo,arg);
						}
					}
				}
				break;
			}
		}
		fclose(reponse);
		system("rm -f login");
	}

	if(strlen(pseudo) == 0)
	{
		sprintf(requete,"\tLOGIN => FAILED\n");
		printf("%s",requete);
		ecrireFichier(fichierLogs, requete);
	}
	else
	{
		char dateReg[128];
		sprintf(requete,"wget %s --load-cookies cookies.txt --keep-session-cookies --quiet -O connect.gz \"http://fr.wikipedia.org/w/api.php?action=userdailycontribs&user=%s&daysago=0\"", usragent, pseudo);
		system(requete);
		sleep(1);
		system("gunzip connect.gz");

		FILE *reponse = fopen("connect","r+");
		if(reponse != NULL)
		{
			trouve = NULL;
			while(fgets(entree,1024,reponse) != NULL)
			{
				trouve = variable("registration=&quot;",entree, var);
				if(trouve != NULL)
				{
					strcpy(dateReg, trouve);
				}
			}
		}
		dateInscr = completerDate(dateReg);
		strftime(dateReg,128,formatDate,localtime(&dateInscr));
		sprintf(requete,"\tLOGIN => PSEUDO : %s\n\t\tDATE INSCRIPTION : %s\n", pseudo, dateReg);
		printf("%s",requete);
		ecrireFichier(fichierLogs, requete);
		system("rm -f connect");
	}
}



