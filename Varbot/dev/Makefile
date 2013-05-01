CFLAGS=-W -Wall -pedantic
EXEC=BOT
HEADERS=constantes.h main.h api/io.h api/api.h lib/fonctions.h
LINKS=main.o analyse.o io.o  login.o logout.o sendNAM.o help.o

Bot: $(LINKS)
	g++ -o Bot $(LINKS)
	mv Bot ../
	touch ../logs/terminal.log
	
#Sources

#main
main.o: main.cpp $(HEADERS)
	g++ -c main.cpp -o main.o $(CFLAGS)

#/api
analyse.o: api/analyse.cpp $(HEADERS)
	g++ -c api/analyse.cpp $(CFLAGS)
	
io.o: api/io.cpp $(HEADERS)
	g++ -c api/io.cpp $(CFLAGS)

#/lib
login.o: lib/login.cpp $(HEADERS)
	g++ -c lib/login.cpp -o login.o $(CFLAGS)

logout.o: lib/logout.cpp $(HEADERS)
	g++ -c lib/logout.cpp -o logout.o $(CFLAGS)

sendNAM.o: lib/sendNAM.cpp $(HEADERS)
	g++ -c lib/sendNAM.cpp -o sendNAM.o $(CFLAGS)
	
help.o: lib/help.cpp $(HEADERS)
	g++ -c lib/help.cpp -o help.o $(CFLAGS)


#Autres fonctions
clean:
	rm *.o
	
svn:
	rm ../logs/*.log
