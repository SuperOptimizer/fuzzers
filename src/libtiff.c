#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <tiffio.h>

// Define a memory buffer for TIFF operations
typedef struct {
    const uint8_t* data;
    size_t size;
    size_t pos;
} MemBuffer;

// Custom read functions for in-memory TIFF handling
static tsize_t readCallback(thandle_t handle, tdata_t data, tsize_t size) {
    MemBuffer* buf = (MemBuffer*)handle;
    size_t remaining = buf->size - buf->pos;
    size_t to_read = (remaining < size) ? remaining : size;

    if (to_read > 0) {
        memcpy(data, buf->data + buf->pos, to_read);
        buf->pos += to_read;
    }
    return to_read;
}

static tsize_t writeCallback(thandle_t handle, tdata_t data, tsize_t size) {
    return size; // Pretend we wrote everything
}

static toff_t seekCallback(thandle_t handle, toff_t offset, int whence) {
    MemBuffer* buf = (MemBuffer*)handle;

    switch (whence) {
        case SEEK_SET:
            buf->pos = offset;
            break;
        case SEEK_CUR:
            buf->pos += offset;
            break;
        case SEEK_END:
            buf->pos = buf->size + offset;
            break;
    }

    return buf->pos;
}

static int closeCallback(thandle_t handle) {
    return 0;
}

static toff_t sizeCallback(thandle_t handle) {
    MemBuffer* buf = (MemBuffer*)handle;
    return buf->size;
}

static int mapCallback(thandle_t handle, tdata_t* base, toff_t* size) {
    MemBuffer* buf = (MemBuffer*)handle;
    *base = (void*)buf->data;
    *size = buf->size;
    return 1;
}

static void unmapCallback(thandle_t handle, tdata_t base, toff_t size) {
    // Nothing to do, we don't own the memory
}

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size < 8) { // TIFF files need at least a header
        return 0;
    }

    // Setup memory buffer
    MemBuffer membuf = {
        .data = Data,
        .size = Size,
        .pos = 0
    };

    // Open TIFF from memory buffer
    TIFF* tif = TIFFClientOpen(
        "memory", "rm",
        (thandle_t)&membuf,
        readCallback,
        writeCallback,
        seekCallback,
        closeCallback,
        sizeCallback,
        mapCallback,
        unmapCallback
    );

    if (!tif) {
        return 0; // Not a valid TIFF file
    }

    // Try to read and modify various TIFF attributes
    uint32_t width, height;
    uint16_t compression, photometric;

    TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &width);
    TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &height);
    TIFFGetField(tif, TIFFTAG_COMPRESSION, &compression);
    TIFFGetField(tif, TIFFTAG_PHOTOMETRIC, &photometric);

    // Try to read image data
    if (width > 0 && width < 65535 && height > 0 && height < 65535) {
        uint32_t* raster = (uint32_t*)_TIFFmalloc(width * height * sizeof(uint32_t));
        if (raster) {
            // Attempt to read the image
            if (TIFFReadRGBAImage(tif, width, height, raster, 0)) {
                // Try some modifications
                TIFFSetField(tif, TIFFTAG_COMPRESSION, COMPRESSION_LZW);
                TIFFSetField(tif, TIFFTAG_PREDICTOR, 2);
            }
            _TIFFfree(raster);
        }
    }

    // Try to read all directories
    do {
        // Read directory contents
        uint16_t bps, spp;
        float xres, yres;

        TIFFGetField(tif, TIFFTAG_BITSPERSAMPLE, &bps);
        TIFFGetField(tif, TIFFTAG_SAMPLESPERPIXEL, &spp);
        TIFFGetField(tif, TIFFTAG_XRESOLUTION, &xres);
        TIFFGetField(tif, TIFFTAG_YRESOLUTION, &yres);

    } while (TIFFReadDirectory(tif));

    TIFFClose(tif);
    return 0;
}