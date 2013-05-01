/*location: dev/api/io.cpp*/

/* includes ============================================================ */

#include "../constantes.h"
#include "../main.h"
#include "io.h"

/* macros ============================================================== */

using namespace std;

/* types =============================================================== */
/* structures ========================================================== */
/* public variables ==================================================== */
/* constants =========================================================== */
/* internal public functions =========================================== */
/* private variables =================================================== */

time_t heureCur;

/* private functions =================================================== */
/* entry points ======================================================== */





char* argument(const char* nom, char* req, char* arg, bool obligatoire)
{
	char entree[1024];
	const char* conspos = strstr(req, nom);
	char* pos = (char*) conspos;
	if(pos==NULL && obligatoire)
	{
		printf("%s: ",nom);
		fgets(entree,1024,stdin);
		strcat(req,nom);
		strcat(req,entree);
		if((pos=strchr(req,'\n')) != NULL)
		{
			*pos = ' ';
		}
		return argument(nom,req, arg, obligatoire);
	}
	else if(pos==NULL && !obligatoire)
	{
	    arg[0] = '\0';
	}

	pos+= strlen(nom);
	int i=0;
	for(;*pos != '-' && *pos != '\0';i++)
	{
		arg[i] = *pos++;
	}
	arg[i-1] = '\0';
	return arg;
}

char* variable(const char* nom, const char* req, char* var)
{
	const char* conspos = strstr(req, nom);
	char* pos = (char*) conspos;
	if(pos== NULL)
	{
		return NULL;
	}
	pos+= strlen(nom);
	int i=0;
	for(;*pos != '&' && *pos != '\0';i++)
	{
		var[i] = *pos++;
	}
	var[i] = '\0';
	return var;
}

void viderBuffer(void)
{
	int c = 0;
    while (c != '\n' && c != EOF)
        c = getchar();
}


void logs(const char* adresse, const char* req)
{
	char format[256];
    
	FILE* fichier = fopen(adresse,"r+");
	fseek(fichier,0,SEEK_END);

	time(&heureCur);
	strftime(format,256,formatDate,localtime(&heureCur));
	fprintf(fichier,"%s\t%s\t%s", format, localUsername(), req);
	fclose(fichier);
}

void ecrireFichier(const char* adresse, const char* str)
{
	FILE* fichier = fopen(adresse,"r+");
	fseek(fichier,0,SEEK_END);
	fprintf(fichier,"%s", str);

	fclose(fichier);
}

void saisieHidden(char* str)
{
	struct termios t;
	ioctl(0, TCGETS, &t);
	t.c_lflag &= ~ECHO;
	ioctl(0, TCSETS, &t);
	scanf("%s",str);
	t.c_lflag |= ECHO;
	ioctl(0, TCSETS, &t);
	printf("\n");
	viderBuffer();
}


time_t completerDate(char* chaine)
{
	struct tm date;
	time_t temps;
	int remplir = 0;
	for(int i = 0; i < 4;i++)
	{
		remplir*= 10;
		remplir+= (chaine[i]-'0');
	}
	date.tm_year = remplir-1900;
	remplir = 0;
	for(int i = 4; i < 6;i++)
	{
		remplir*= 10;
		remplir+= (chaine[i]-'0');
	}
	date.tm_mon=remplir-1;
	remplir = 0;
	for(int i = 6; i < 8;i++)
	{
		remplir*= 10;
		remplir+= (chaine[i]-'0');
	}
	date.tm_mday=remplir;
	remplir = 0;
	for(int i = 8; i < 10;i++)
	{
		remplir*= 10;
		remplir+= (chaine[i]-'0');
	}
    date.tm_hour=remplir;
    remplir = 0;
    for(int i = 10; i < 12;i++)
	{
		remplir*= 10;
		remplir+= (chaine[i]-'0');
	}
	date.tm_min=remplir;
	remplir = 0;
	for(int i = 12; i < 14;i++)
	{
		remplir*= 10;
		remplir+= (chaine[i]-'0');
	}
    date.tm_sec=remplir;
	temps = mktime(&date);
	return temps;
}


bool confirmation(char* message)
{
	char entree[1024];
	printf("%s",message);
	ecrireFichier(fichierLogs, message);
	fgets(entree, 1024, stdin);
	if(entree[0] == 'y')
		return true;
	return false;
}

