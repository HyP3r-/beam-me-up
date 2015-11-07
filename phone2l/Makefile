INSTALL_DIR=/usr/local/bin

CC = g++
LIBLINPHONE = /opt/linphone

CFLAGS = -I$(LIBLINPHONE)/include -g -Wall -pthread -DVERSION=\"`date +%Y-%m-%d`\" # -O3
LDFLAGS = -pthread -L$(LIBLINPHONE)/lib/ -llinphone -lbellesip -lSDL2 -lSDL2_ttf \
          -lmediastreamer_base -lmediastreamer_voip -lortp -lsqlite3 \
          -lxml2 -ldl -lm -lsoup-2.4 -lgobject-2.0 -lglib-2.0 -lantlr3c -lpolarssl \
          -lspeex -lspeexdsp -lasound -lv4l2 -lavcodec -lavutil -lswscale \
          -lX11 -lXext # -lXv \
  # Line 1: directly required by this tools
  # Line 2: required by liblinphone
  # Line 3: required by bellesip
  # Line 4: required by mediastreamer
  # Line 5: required by libSDL2

BIN = phone2l
SRC = beam-render.c phone2l.c
OBJ = beam-render.o phone2l.o


build: $(BIN)

install: $(BIN)
	cp $(BIN) $(INSTALL_DIR)

clean:
	rm -f *.o $(BIN)

depend:
	makedepend -Y $(SRC)

$(BIN): $(OBJ)
	$(CC) -o $(BIN) $(OBJ) $(LDFLAGS)

%.o: %.c
	$(CC) -c $(CFLAGS) $<


# DO NOT DELETE

beam-render.o: beam-render.h
phone2l.o: beam-render.h
