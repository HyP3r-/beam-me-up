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


#include "beam-render.h"

#include <SDL2/SDL.h>
#include <SDL2/SDL_ttf.h>

#include <mediastreamer2/msfilter.h>
#include <mediastreamer2/msvideo.h>



static SDL_Window *sdlWindow = NULL;
static SDL_Renderer *sdlRenderer = NULL;
static TTF_Font *sdlFont = NULL;
static SDL_Texture *texVideoRemote = NULL, *texVideoLocal = NULL, *texMessage = NULL;
static volatile BOOL sdlRenderUpdate = FALSE;

MSPicture picLocal, picRemote;
static volatile BOOL picLocalUpdated, picRemoteUpdated;
static SDL_mutex *picMutex;   // Mutex for 'picLocal', 'picRemote' + flags


// Important note on the design (2015-05-22)
//
// It seems that SDL2 calls from different treads are not allowed if GPU acceleration
// is to be used, even if SDL2 calls are properly sunchronized with a mutex.
// Unfortunately, the video images are delivered by a background thread from
// mediastreamer2 ('MSFilterDesc::process'). Hence, this module is designed as follows:
//
// 1. Only the main thread is allowed to call SDL2 functions.
//
// 2. Images are passed from the background to the main thread by copying them
//    to 'picLocal'/'picRemote', the structures are protected by the 'picMutex'.
//
// Unfortunately, this involves one additional copy operation for each frame.





// ***************** MSPicture helpers *********************


static void MSPictureInit (MSPicture *pic) {
  int n;

  pic->w = pic->h = 0;
  for (n = 0; n < 4; n++) pic->strides[n] = 0;
  for (n = 0; n < 4; n++) pic->planes[n] = NULL;
}


static void MSPictureCopyFrom (MSPicture *pic, MSPicture *src) {
  // This function must only be called for 'pic' elements created by 'MSPictureInit'!
  int n, bytes[4];

  if (!src) {
    // Clear the picture ...
    if (pic->planes[0]) free (pic->planes[0]);
    MSPictureInit (pic);
  }
  else {
    if ((pic->w != src->w) || (pic->h != src->h)
        || (pic->strides[0] != src->strides[0]) || (pic->strides[1] != src->strides[1])
        || (pic->strides[2] != src->strides[2]) || (pic->strides[3] != src->strides[3])) {
      // Prepare for new format...
      MSPictureCopyFrom (pic, NULL);    // Clear picture
      pic->w = src->w;                  // Set parameters...
      pic->h = src->h;
      for (n = 0; n < 4; n++) pic->strides[n] = src->strides[n];
    }

    for (n = 0; n < 4; n++) bytes[n] = pic->h * pic->strides[n];

    if (pic->planes[0] == NULL) {
      // Allocate memory...
      pic->planes[0] = malloc (bytes[0] + bytes[1] + bytes[2] + bytes[3]);
      for (n = 1; n < 4; n++) pic->planes[n] = pic->planes[n-1] + bytes[n-1];
      //printf ("### (Re)allocating: %08x\n", (uint32_t) pic->planes[0]);
    }

    //printf ("### Copying: %08x\n", (uint32_t) pic->planes[0]);
    if (pic->h) for (n = 0; n < 4; n++) if (src->strides[n])
      memcpy (pic->planes[n], src->planes[n], pic->h / (pic->strides[0] / pic->strides[n]) * pic->strides[n]);
  }
}


void MSPictureDone (MSPicture *pic) {
  MSPictureCopyFrom (pic, NULL);
}





// ***************** SDL-related objects and functions *****


static void RenderUpdate () {
  SDL_Rect r;
  int winW, winH, texW, texH, dist;

  if (!sdlWindow || !sdlRenderer) return;

  SDL_GetRendererOutputSize (sdlRenderer, &winW, &winH);

  SDL_SetRenderDrawColor (sdlRenderer, 0, 0, 0, 255);
  SDL_RenderClear (sdlRenderer);

  if (texVideoRemote) {
    SDL_QueryTexture (texVideoRemote, NULL, NULL, &texW, &texH);
    if (winW * texH < texW * winH) {
      // Texture is wider than window => fit to width...
      r.w = winW;
      r.h = texH * winW / texW;
      r.x = 0;
      r.y = (winH - r.h) / 2;
    }
    else {
      // Window is wider than texture => fit to height...
      r.w = texW * winH / texH;
      r.h = winH;
      r.x = (winW - r.w) / 2;
      r.y = 0;
    }
    SDL_RenderCopy (sdlRenderer, texVideoRemote, NULL, &r);
  }
  if (texVideoLocal) {
    SDL_QueryTexture (texVideoLocal, NULL, NULL, &texW, &texH);
    // Select 1/4 of the total height and keep aspect ratio...
    r.h = winH / 4;
    r.w = r.h * texW / texH;
    r.x = winW - r.w;
    r.y = winH - r.h;
    SDL_RenderCopy (sdlRenderer, texVideoLocal, NULL, &r);
  }
  if (texMessage) {
    SDL_QueryTexture (texMessage, NULL, NULL, &texW, &texH);
    r.w = texW;
    r.h = texH;
    /*
    // Center message text...
    r.x = (winW - texW) / 2;
    r.y = (winH - texH) / 2;
    */
    dist = TTF_FontHeight (sdlFont) / 2;
    r.x = dist;
    r.y = winH - texH - dist;
    SDL_RenderCopy (sdlRenderer, texMessage, NULL, &r);
  }
  SDL_RenderPresent (sdlRenderer);
}


static void UpdateTextureFromMSPicture (SDL_Texture **pTex, MSPicture *pic, char *viewName) {
  int texW, texH;

  if (!pic) {
    if (*pTex) SDL_DestroyTexture (*pTex);
    *pTex = NULL;
  }
  else if (!pic->planes[0] || !pic->w || !pic->h) {
    if (*pTex) SDL_DestroyTexture (*pTex);
    *pTex = NULL;
  }
  else {
    // Check if the texture format is outdated...
    if (*pTex) {
      SDL_QueryTexture (*pTex, NULL, NULL, &texW, &texH);
      if (pic->w != texW || pic->h != texH) {
        // Format changed -> need to recreate the texture...
        SDL_DestroyTexture (*pTex);
        *pTex = NULL;
      }
    }
    // Create texture object (again) if necessary...
    if (!(*pTex)) {
      *pTex = SDL_CreateTexture (sdlRenderer, SDL_PIXELFORMAT_YV12,
                                 SDL_TEXTUREACCESS_STATIC, pic->w, pic->h);
        // Texture parameters taken from https://forums.libsdl.org/viewtopic.php?t=9898, "SDL 2.0 and ffmpeg. How to render texture in new version."
      if (!(*pTex)) {
        printf ("E: 'SDL_CreateTexture' failed for video texture: %s\n", SDL_GetError ());
      }
      SDL_SetTextureBlendMode (*pTex, SDL_BLENDMODE_NONE);
      printf ("I: Received resolution of %s view: %i x %i pixels.\n",
              viewName, pic->w, pic->h);
    }
    // Update the texture...
    if (SDL_UpdateYUVTexture (*pTex, NULL, pic->planes[0], pic->strides[0], pic->planes[1], pic->strides[1], pic->planes[2], pic->strides[2]) != 0) {
      printf ("E: 'SDL_UpdateYUVTexture' failed: %s\n", SDL_GetError ());
    }
  }
}





// ***************** Mediastreamer2 filter module **********


// ***** msFilterDesc methods *****


static void MSDisplayProcess (MSFilter *f) {
  MSPicture pic;
  mblk_t *inp;

  // Handle remote image ...
  if (f->inputs[0]) {
    if ( (inp = ms_queue_peek_last (f->inputs[0])) ) {
      if (ms_yuv_buf_init_from_mblk (&pic, inp) == 0) {
        SDL_LockMutex (picMutex);
        MSPictureCopyFrom (&picRemote, &pic);
        picRemoteUpdated = TRUE;
        SDL_UnlockMutex (picMutex);
      }
    }
    ms_queue_flush (f->inputs[0]);
  }
  else {
    SDL_LockMutex (picMutex);
    MSPictureCopyFrom (&picRemote, NULL);
    picRemoteUpdated = TRUE;
    SDL_UnlockMutex (picMutex);
  }

  // Handle local image ...
  if (f->inputs[1]) {
    if ( (inp = ms_queue_peek_last (f->inputs[1])) ) {
      if (ms_yuv_buf_init_from_mblk (&pic, inp) == 0) {
        SDL_LockMutex (picMutex);
        MSPictureCopyFrom (&picLocal, &pic);
        picLocalUpdated = TRUE;
        SDL_UnlockMutex (picMutex);
      }
    }
    ms_queue_flush (f->inputs[1]);
  }
  else {
    SDL_LockMutex (picMutex);
    MSPictureCopyFrom (&picLocal, NULL);
    picLocalUpdated = TRUE;
    SDL_UnlockMutex (picMutex);
  }
}



// *****


static MSFilterDesc msDisplayDesc = {
  .id=MS_FILTER_PLUGIN_ID,
  .name = "BRDisplay",
  .text = "A custom video display for 'beam-render'",
  .category = MS_FILTER_OTHER,
  .ninputs = 2,
  .noutputs = 0,
  .process = MSDisplayProcess,
};





// ***************** Init/Done *****************************


BOOL BRInit (const char *fontFileName, int fontSize) {

  // Init SDL and SDL_TTF...
  if (SDL_Init (SDL_INIT_VIDEO) != 0) {
    printf ("E: 'SDL_Init' failed: %s\n", SDL_GetError ());
    return FALSE;
  }
  if (TTF_Init() != 0) {
    printf ("E: 'TTF_Init' failed: %s\n", SDL_GetError ());
    SDL_Quit ();
    return FALSE;
  }

  // Create pic* structures...
  MSPictureInit (&picLocal);
  MSPictureInit (&picRemote);
  picLocalUpdated = picRemoteUpdated = FALSE;
  picMutex = SDL_CreateMutex ();

  // Load font...
  sdlFont = TTF_OpenFont (fontFileName, fontSize);
  if (!sdlFont) {
    printf ("E: Unable to load font '%s'\n", fontFileName);
    SDL_Quit ();
    return FALSE;
  }

  // Return with success...
  return TRUE;
}


void BRInitMediastreamer () {
  ms_filter_register (&msDisplayDesc);
}


void BRDone () {
  BRWindowClose ();

  if (sdlFont) {
    TTF_CloseFont (sdlFont);
    sdlFont = NULL;
  }

  MSPictureDone (&picLocal);
  MSPictureDone (&picRemote);
  SDL_DestroyMutex (picMutex);
  picMutex = NULL;

  SDL_Quit ();
}





// ***************** Window management *********************


BOOL BRWindowOpen (char *titel, BOOL forceSoftwareRenderer, int interpolationMethod) {
  SDL_RendererInfo renInfo;
  BOOL accelerated;

  // Init window...
  sdlWindow = SDL_CreateWindow (
    titel,
    SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
    704, 576, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE /* | SDL_WINDOW_FULLSCREEN_DESKTOP */
  );
  if (!sdlWindow) {
    printf ("E: 'SDL_CreateWindow' failed: %s\n", SDL_GetError ());
    return FALSE;
  }

  // Init renderer...
  sdlRenderer = SDL_CreateRenderer (sdlWindow, -1, forceSoftwareRenderer ? SDL_RENDERER_SOFTWARE : 0);
  if (!sdlRenderer) {
    SDL_DestroyWindow (sdlWindow);
    sdlWindow = NULL;
    printf ("E: 'SDL_CreateRenderer' failed: %s\n", SDL_GetError ());
    return FALSE;
  }

  // Determine, set and report renderer type and scaling method...
  SDL_GetRendererInfo (sdlRenderer, &renInfo);
  accelerated = (renInfo.flags & SDL_RENDERER_ACCELERATED) ? TRUE : FALSE;
  if (!interpolationMethod) interpolationMethod = accelerated ? 2 : 1;
  SDL_SetHint (SDL_HINT_RENDER_SCALE_QUALITY, interpolationMethod == 2 ? "1" : "0");
  printf ("I: Using %s renderer '%s' and %s interpolation.\n",
          accelerated ? "accelerated" : "software", renInfo.name,
          interpolationMethod == 2 ? "trying bilinear" : "nearest-neighbor");

  //for (n = 0; n < (int) renInfo.num_texture_formats; n++)
  //  INFOF(("  SDL_Renderer [%i]:         %s", n, SDL_GetPixelFormatName (renInfo.texture_formats[n])));


  // Return with success...
  return TRUE;
}


void BRWindowClose () {
  if (sdlRenderer) SDL_DestroyRenderer (sdlRenderer);
  sdlRenderer = NULL;
  if (sdlWindow) SDL_DestroyWindow (sdlWindow);
  sdlWindow = NULL;
}





// ***************** Iteration *****************************

void BRIterate () {
  SDL_Event ev;

  // Check for UI events...
  while (SDL_PollEvent (&ev)) {
    if (ev.type == SDL_WINDOWEVENT && ev.window.event == SDL_WINDOWEVENT_EXPOSED)
      sdlRenderUpdate = TRUE;
  }

  // Check for updated video images...
  SDL_LockMutex (picMutex);
  if (picLocalUpdated) {
    UpdateTextureFromMSPicture (&texVideoLocal, &picLocal, "secondary");
    picLocalUpdated = FALSE;
    sdlRenderUpdate = TRUE;
  }
  if (picRemoteUpdated) {
    UpdateTextureFromMSPicture (&texVideoRemote, &picRemote, "main");
    picRemoteUpdated = FALSE;
    sdlRenderUpdate = TRUE;
  }
  SDL_UnlockMutex (picMutex);

  // Render update if necessary...
  if (sdlRenderUpdate) {
    RenderUpdate ();
    sdlRenderUpdate = FALSE;
  }
}





// ***************** Font rendering ************************


void BRDisplayMessage (const char *msg) {
  const static SDL_Color textColor = { .r = 0xff, .g = 0xff, .b = 0xff };
  SDL_Surface *surf;

  if (texMessage) {
    SDL_DestroyTexture (texMessage);
    texMessage = NULL;
  }
  surf = TTF_RenderUTF8_Blended (sdlFont, msg, textColor);
  texMessage = SDL_CreateTextureFromSurface (sdlRenderer, surf);
  //SDL_RenderPresent (sdlRenderer);
  RenderUpdate ();
}
