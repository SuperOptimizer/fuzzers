#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include <unistd.h>

__AFL_FUZZ_INIT();

// Structure to hold memory buffer info
struct memory_buffer {
    const unsigned char *buffer;
    size_t size;
    size_t position;
};

// Callback function for reading from memory
void read_from_memory(png_structp png_ptr, png_bytep outBytes, png_size_t byteCountToRead) {
    struct memory_buffer *mem = (struct memory_buffer*)png_get_io_ptr(png_ptr);
    if (mem->position + byteCountToRead > mem->size) {
        png_error(png_ptr, "Read Error");
        return;
    }
    memcpy(outBytes, mem->buffer + mem->position, byteCountToRead);
    mem->position += byteCountToRead;
}

// Function to read PNG data from a memory buffer
void read_png_from_memory(const unsigned char *buffer, size_t length) {
    if (!buffer || length < 8) return;

    // Verify PNG signature
    if (png_sig_cmp(buffer, 0, 8)) {
        return;
    }

    // Initialize png read struct
    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png) {
        return;
    }

    // Initialize info struct
    png_infop info = png_create_info_struct(png);
    if (!info) {
        png_destroy_read_struct(&png, NULL, NULL);
        return;
    }

    // Setup error handling
    if (setjmp(png_jmpbuf(png))) {
        png_destroy_read_struct(&png, &info, NULL);
        return;
    }

    // Setup memory buffer
    struct memory_buffer mem = {
        .buffer = buffer,
        .size = length,
        .position = 0
    };

    // Set custom read function
    png_set_read_fn(png, &mem, read_from_memory);

    // Read PNG info
    png_read_info(png, info);

    // Get image info
    int width = png_get_image_width(png, info);
    int height = png_get_image_height(png, info);
    png_byte color_type = png_get_color_type(png, info);
    png_byte bit_depth = png_get_bit_depth(png, info);

    // Clean up
    png_destroy_read_struct(&png, &info, NULL);
}

int main() {
    #ifdef __AFL_HAVE_MANUAL_CONTROL
    __AFL_INIT();
    #endif

    unsigned char *buf = __AFL_FUZZ_TESTCASE_BUF;

    while (__AFL_LOOP(10000)) {
        int len = __AFL_FUZZ_TESTCASE_LEN;

        // Skip very small inputs
        if (len < 8) continue;

        // Process the input buffer as PNG data
        read_png_from_memory(buf, len);
    }

    return 0;
}