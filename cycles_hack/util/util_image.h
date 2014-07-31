/*
 * Copyright 2011, Blender Foundation.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#ifndef __UTIL_IMAGE_H__
#define __UTIL_IMAGE_H__

/* OpenImageIO is used for all image file reading and writing. */

#include <emscripten.h>

// #include <OpenImageIO/imageio.h>

//OIIO_NAMESPACE_USING

using namespace ccl;

struct ImageSpec {
    int width;
    int height;
    int nchannels;
    ImageSpec(int w, int h, int chans /* no floats -- bytes only */) {
        width = w;
        height = h;
        nchannels = chans;
    }

    ImageSpec() {
        width = 1;
        height = 1;
        nchannels = 4;
    }
};

struct ImageInput {
    string filename;

    ImageInput(string filename) {
        this->filename = filename;
    };

    static ImageInput* create(string filename) {
        ImageInput* inp = new ImageInput(filename);
        return inp;
    };

    bool read_reverse_y_image(void* data, int width_bytes, int length) {
        int image_size = (int) EM_ASM_INT({
            var imgName = Module.Pointer_stringify($0);

            var img = Module.loadedImages[imgName];

            if (console.assert) console.assert(img, imgName + "Was not loaded yet!");
            if (console.assert) console.assert(img.pixels.length === $2,
                "Expected image length(1) does not match actual PNG length(2)", $2, img.pixels.length);

            Module.writeArrayToMemory(img.pixels, $1);
        }, this->filename.c_str(), data, length);

        return true;
    }

    bool open(string filename, ImageSpec& spec) {
        EM_ASM_INT({
            var imgName = Module.Pointer_stringify($0);

            Module.loadedImages = Module.loadedImages || {};

            if (Module.loadedImages[imgName] !== undefined) { return; }

            if (console.time) {
                console.time('loading ' + imgName + ' from base64');
            }

            var imgAsB64 = Module.images[imgName];

            var frombase64 =
                new Uint8Array(
                    atob(imgAsB64)
                        .split("")
                        .map(function(s){
                            return s.charCodeAt(0);
                        }));

            var png = new PNG(frombase64);
            var pixels = png.decodePixels();
            Module.loadedImages[imgName] = new Object();
            Module.loadedImages[imgName].pixels = pixels;
            Module.loadedImages[imgName].height = png.height;
            Module.loadedImages[imgName].width = png.width;
            Module.loadedImages[imgName].length = pixels.length;

            if (console.timeEnd) {
                console.timeEnd('loading ' + imgName + ' from base64');
            }
        }, this->filename.c_str());

        spec.width = EM_ASM_INT({
            return Module.loadedImages[Pointer_stringify($0)].width;
        }, this->filename.c_str());
        spec.height = EM_ASM_INT({
            return Module.loadedImages[Pointer_stringify($0)].height;
        }, this->filename.c_str());
        spec.nchannels = 4;

        return true;
    }

    bool close() {
        return true;
    }
};

#endif /* __UTIL_IMAGE_H__ */

