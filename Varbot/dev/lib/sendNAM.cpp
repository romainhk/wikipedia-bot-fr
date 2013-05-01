/*location: dev/lib/sendNAM.cpp*/

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
void sendNAM(char* req)
{
	if(strlen(pseudo) == 0)
	{
		char requete[128];
		sprintf(requete,"\tSEND => NOT LOGGED IN\n");
		printf("%s",requete);
		ecrireFichier(fichierLogs, requete);
	}
	else
	{
		char arg[256];
		char requete[1024];
		char entree[1024];
		char trouve[1024];
		char chaine[1024];
		char *pos;
		int nbAbonnes;
		argument(" --number ",req, arg, true);

		sprintf(requete,"wget --quiet -O list.gz %s \"http://fr.wikipedia.org/w/api.php?action=parse&text={{Utilisateur:Varmin/NAM}}\"", usragent);
		system(requete);
		system("gunzip list.gz");
		FILE *reponse = fopen("list","r+");
		if(reponse != NULL)
		{
			while(fgets(entree,1024,reponse) != NULL)
			{
				pos = variable("&amp;lt;p&amp;gt;&amp;lt;br /&amp;gt;", entree, trouve);
				if(pos != NULL)
				{
					fgets(entree,1024,reponse);
					nbAbonnes = strtol(entree,NULL,10);
					for(int i = 0; i < nbAbonnes;i++)
					{
						char pseudoDest[250];
						fgets(entree,1024,reponse);
						for(int j = 0; entree[j] != '\0' && entree[j] != '&';j++)
						{
							pseudoDest[j] = entree[j];
							pseudoDest[j+1] = '\0';
						}
						sprintf(chaine,"\tSending n° %s to %s (y/n) : ", arg, pseudoDest);
						if(confirmation(chaine, 'Y') == true)
						{
							sprintf(requete,"wget --quiet --load-cookies cookies.txt --save-cookies cookies.txt --keep-session-cookies -O token.gz %s \"http://fr.wikipedia.org/w/api.php?action=query&prop=info&intoken=edit&titles=Discussion_utilisateur:%s\"", usragent, pseudoDest);
							system(requete);
							system("gunzip token.gz");
							FILE* ftoken = fopen("token","r+");
							if(ftoken != NULL)
							{
								while(fgets(entree,1024,ftoken) != NULL)
								{
									pos = variable("edittoken=&quot;", entree, trouve);
									if(pos != NULL)
									{
										int n = strlen(trouve)-2;
										trouve[n++] = '%';
										trouve[n++] = '2';
										trouve[n++] = 'B';
										trouve[n++] = '%';
										trouve[n++] = '5';
										trouve[n++] = 'C';
										trouve[n] = '\0';
										sprintf(requete,"wget --quiet --load-cookies cookies.txt --save-cookies cookies.txt --keep-session-cookies -O edit.gz %s --post-data \"title=Discussion_utilisateur:%s&summary=Nouvelles d\'Arménie n° %s&section=new&bot&text={{Projet:Arménie/Des Nouvelles d\'Arménie/%s}}&token=%s\" \"http://fr.wikipedia.org/w/api.php?action=edit\"", usragent, pseudoDest, arg, arg, trouve);
										system(requete);
										system("gunzip edit.gz");
										system("rm -f edit");
										break;
									}
								}

							}

							sprintf(chaine,"\tSent n° %s to %s\n", arg, pseudoDest);
							printf("%s",chaine);
							ecrireFichier(fichierLogs, chaine);
							system("rm -f token");
						}
						else
						{
							sprintf(chaine,"\tNot sent to %s\n", pseudoDest);
							printf("%s",chaine);
							ecrireFichier(fichierLogs, chaine);
						}
					}
					system("rm -f list");
					return;
				}
			}
		}
		system("rm -f list");
	}
}

