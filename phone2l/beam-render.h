/*************************************************************************

  This file is part of the 'beam' project.

  (C) 2015 Gundolf Kiefer <gundolf.kiefer@hs-augsburg.de>
      Hochschule Augsburg, University of Applied Sciences

  Description:
    This module contains helper function for SDL2-based output.

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


#ifndef _BEAM_RENDER_
#define _BEAM_RENDER_


#ifndef BOOL
#define BOOL int
#define TRUE 1
#define FALSE 0
#endif



// ***** Init/Done *****

BOOL BRInit (const char *fontFileName, int fontSize);
  // In case of an error, an error message is printed and 'FALSE' is returned
  // (no need to print an error message by caller).

void BRInitMediastreamer ();
  // Registers own filters with 'mediastreamer2',
  // must be called after initialization of 'mediastreamer2'
  // Presently available:
  //   "BRDisplay": Display output with 'beam-render'

void BRDone ();



// ***** Window management *****

BOOL BRWindowOpen (const char *titel, BOOL forceSoftwareRenderer, int interpolationMethod);
  // Opens the window (presently only one window supported)
  // on error, prints a message and returns 'FALSE'
  // 'interpolationMethod' can be one of: 0=auto, 1=nearest, 2=bilinear
void BRWindowClose ();



// ***** Iteration *****

void BRIterate ();



// ***** Font rendering *****

void BRDisplayMessage (const char *msg);
  // Displays message in the centre of the screen; msg == NULL clears the previous message



#endif
