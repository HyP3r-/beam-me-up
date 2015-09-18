/*************************************************************************

  This file is part of the 'Beam' project.

  (C) 2015 Gundolf Kiefer <gundolf.kiefer@hs-augsburg.de>
      Hochschule Augsburg, University of Applied Sciences

  Description:
    This is the main program of 'phone2l', a lightweight tool for video
    telephony.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

 *************************************************************************/



#include <stdio.h>
#include <stdlib.h>
#include <signal.h>

#include <linphone/linphonecore.h>

#include "beam-render.h"


#ifndef BOOL
#define BOOL int
#define TRUE 1
#define FALSE 0
#endif





// ***************** Global Variables **********************

static BOOL running = TRUE;
static BOOL error = FALSE;
static BOOL inCall = FALSE;

static char *argCallee = NULL, *argConfig = NULL;
static BOOL argHelp = FALSE, argVerbose = FALSE;
static const char *argFontFileName = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
static int argFontSize = 24;
static BOOL argSoftwareRenderer = FALSE;
static int argInterpolation = 0;





// ***************** Linphone callbacks ********************


static void ShowStatus (const char *msg, const char *var1, const char *var2) {
  char buf [200];

  snprintf (buf, 199, msg, var1, var2);
  printf ("S: %s\n", buf);
  fflush (stdout);
  BRDisplayMessage (buf);
}


static void cb_display_status (LinphoneCore * lc, const char *something) {
  //printf ("I: %s\n", something);
  printf ("S: %s\n", something);
  BRDisplayMessage (something);
}


static void cb_display_warning (LinphoneCore * lc, const char *something) {
  printf ("W: %s\n", something);
}



// *****


static void cb_call_state_changed (LinphoneCore *lc, LinphoneCall *call, LinphoneCallState st, const char *msg){
  char *from;

  from = linphone_call_get_remote_address_as_string (call);
  switch (st) {
    case LinphoneCallEnd:
      ShowStatus ("Call with %s ended (%s).", from, linphone_reason_to_string (linphone_call_get_reason (call)));
      inCall = FALSE;
      if (argCallee) running = FALSE;
      break;
    case LinphoneCallStreamsRunning:
      printf ("I: Media streams established with %s (%s).\n", from, (linphone_call_params_video_enabled( linphone_call_get_current_params(call)) ? "video":"audio"));
      break;
    case LinphoneCallIncomingReceived:
      ShowStatus ("Receiving new incoming call from %s", from, NULL);
      linphone_call_enable_camera (call, TRUE);  // necessary?
      if (inCall)
        linphone_core_decline_call (lc, call, LinphoneReasonBusy);
      else
        linphone_core_accept_call (lc, call);  // TBD: must this call be moved outside this handler?
      break;
    case LinphoneCallOutgoingInit:
      ShowStatus ("Establishing call to %s", from, NULL);
      break;
    case LinphoneCallOutgoingProgress:
      ShowStatus ("Call to %s in progress.", from, NULL);
      break;
    case LinphoneCallOutgoingRinging:
      ShowStatus ("Call to %s ringing.", from, NULL);
      break;
    case LinphoneCallConnected:
      ShowStatus ("Connected to %s.", from, NULL);
      inCall = TRUE;
      break;
    case LinphoneCallOutgoingEarlyMedia:
      printf ("I: Call with %s early media.", from);
      break;
    case LinphoneCallError:
      ShowStatus ("Call error with %s.", from, NULL);
      if (argCallee) error = TRUE;
      break;
    /*
    case LinphoneCallUpdatedByRemote:
      printf ("### cb_call_state_changed: Call %i with %s updated.\n", id, from);
      cp = linphone_call_get_current_params(call);
      // TBD: auto-start camera?
      if (!linphone_call_camera_enabled (call) && linphone_call_params_video_enabled (cp)){
        printf ("Far end requests to share video.\nType 'camera on' if you agree.\n");
      }
      break;
    case LinphoneCallPausing:
      printf ("### cb_call_state_changed: Pausing call %i with %s.\n", id, from);
      break;
    case LinphoneCallPaused:
      printf ("### cb_call_state_changed: Call %i with %s is now paused.\n", id, from);
      break;
    case LinphoneCallPausedByRemote:
      printf ("### cb_call_state_changed: Call %i has been paused by %s.\n",id,from);
      break;
    case LinphoneCallResuming:
      printf ("### cb_call_state_changed: Resuming call %i with %s.\n", id, from);
      break;
    */
    default:
      break;
  }
  ms_free(from);
}





// ***************** Main **********************************


#define MAX_PATH 200

static LinphoneCoreVTable lpcVtable = { 0 };
static LinphoneCore *lpc = NULL;
static char configFileName [MAX_PATH+1] = "";


static void signal_handler (int signo) {
  running = FALSE;
}


int main (int argc, char *argv[]) {
  char *arg;
  int n;

  printf ("I: Phone2l " VERSION " by Gundolf Kiefer <gundolf.kiefer@hs-augsburg.de>, University of Applied Sciences Augsburg, 2015\n");

  // Interpret command line...
  error = FALSE;
  for (n = 1; n < argc; n++) {
    arg = argv[n];
    if (arg[0] != '-') {
      if (!argCallee) argCallee = arg;
      else error = TRUE;
    }
    else switch (arg[1]) {
      case 'h':
        argHelp = TRUE;
        break;
      case 'v':
        argVerbose = TRUE;
        break;
      case 'c':
        if (arg[2] == '=') argConfig = arg + 3;
        else error = TRUE;
        break;
      case 'f':
        if (arg[2] == '=') argFontFileName = arg + 3;
        else error = TRUE;
        break;
      case 's':
        if (arg[2] != '=') error = TRUE;
        else {
          argFontSize = atoi (arg + 3);
          if (argFontSize < 8) error = TRUE;
            // we assume that smaller fonts do not make sense and are unreadable
        }
        break;
      case 'a':
        argSoftwareRenderer = TRUE;
        break;
      case 'i':
        argInterpolation = arg[2] - '0';
        if (argInterpolation < 0 || argInterpolation > 2) error = TRUE;
        break;
      default:
        error = TRUE;
    }
  }
  if (error || argHelp) {
    printf ("Usage: phone2l [<options>]           - run phone2l in listening mode\n"
            "       phone2l [<options>] <URL>     - call <URL> and terminate with call\n"
            "\n"
            "Options:\n"
            "  -h : show this help\n"
            "  -v : be verbose\n"
            "  -c=<config> : specify linphone configuration file (default: ~/.linphonerc)\n"
            "  -f=<font>: specify ttf font file (default: %s)\n"
            "  -s=<size>: specify font size (default: %i)\n"
            "  -a: disable hardware acceleration, force software rendering\n"
            "  -i[0|1|2]: set interpolation method - 0=auto, 1=nearest, 2=bilinear (default: 0)\n"
            "\n"
            "By default, debug messages from the underlying libraries (liblinphone,\n"
            "mediastreamer, ...) are sent to 'stderr' and can safely be redirected\n"
            "to /dev/null. Messages to 'stdout' can be automatically processed\n"
            "according to the following prefixes:\n"
            "  S:   Status messages, also shown on the screen\n"
            "  I:   Information messages\n"
            "  W:   Warnings\n"
            "  E:   Errors (typically causing the tool to exit)\n",
            argFontFileName, argFontSize
            );
    exit (error ? 3 : 0);
  }

  // Set signal handlers...
  signal (SIGTERM, signal_handler);   // for kill command / requested by project team
  signal (SIGINT, signal_handler);    // for keyboard interrupt

  // Init liblinphone_core...
  printf ("I: Initializing 'liblinphone'...\n");
  lpcVtable.display_status = cb_display_status;
  //lpcVtable.display_message = cb_display_message;
  lpcVtable.display_warning = cb_display_warning;
  //lpcVtable.display_url = cb_display_url;
  lpcVtable.call_state_changed = cb_call_state_changed;

  if (argVerbose) linphone_core_enable_logs (stderr);
  if (argConfig) strncpy (configFileName, argConfig, MAX_PATH);
  else snprintf (configFileName, MAX_PATH, "%s/.linphonerc", getenv ("HOME"));
  lpc = linphone_core_new (&lpcVtable, configFileName, NULL, NULL);
  linphone_core_set_user_agent (lpc, "Phone2l", VERSION);
  linphone_core_enable_video_capture (lpc, TRUE);
  linphone_core_enable_video_display (lpc, TRUE);
  linphone_core_enable_video_preview (lpc, TRUE);

  // Init 'beam-render' ...
  if (!BRInit (argFontFileName, argFontSize)) exit (3);
  if (!BRWindowOpen ("Phone2l", argSoftwareRenderer, argInterpolation)) exit (3);
  BRInitMediastreamer ();

  // The following calls only work for 3.8.1 (not 3.6.x)...
  //printf ("### linphone_core_set_video_display_filter (linphonec, 'BRDisplay')...\n");
  linphone_core_set_video_display_filter (lpc, "BRDisplay");
    // "MSVideoOut": A SDL-based video display
    // "MSX11Video": A video display using X11+Xv
    // "MSGLXVideo": A video display using GL (glx)
  //printf ("### linphone_core_get_video_display_filter (): %s\n", linphone_core_get_video_display_filter (lpc));
  //printf ("### video_stream_get_default_video_renderer (): %s\n", video_stream_get_default_video_renderer ());

  // Testing ...
  //BRDisplayMessage ("Hello World!");

  // Initiate call if set...
  if (argCallee) {
    printf ("I: Calling '%s'...\n", argCallee);
    if (!linphone_core_invite (lpc, argCallee)) {
      printf ("E: Call initiation failed!\n");
      error = TRUE;
    }
  }

  // Main loop ...
  while (running && !error) {
    linphone_core_iterate (lpc);
    BRIterate ();
    usleep (20000);   // 20 ms / 50 Hz
  }

  // Finish ...
  printf ("I: Terminating all calls...\n");
  linphone_core_terminate_all_calls (lpc);
  printf ("I: Exiting...\n");
  linphone_core_destroy (lpc);
  BRDone ();

  exit (error ? 1 : 0);
}
