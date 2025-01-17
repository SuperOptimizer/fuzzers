#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <stdint.h>
#include <png.h>
#include <stdint.h>

struct memory_buffer {
    const unsigned char* buffer;
    size_t size;
    size_t position;
};

void read_from_memory(png_structp png_ptr, png_bytep outBytes, png_size_t byteCountToRead) {
    struct memory_buffer* mem = (struct memory_buffer*)png_get_io_ptr(png_ptr);
    if (mem->position + byteCountToRead > mem->size) {
        png_error(png_ptr, "Read Error");
        return;
    }
    memcpy(outBytes, mem->buffer + mem->position, byteCountToRead);
    mem->position += byteCountToRead;
}

void write_to_memory(png_structp png_ptr, png_bytep data, png_size_t length) {
    // We don't actually store the output, just pretend to write
    (void)png_ptr;
    (void)data;
    (void)length;
}

void flush_memory(png_structp png_ptr) {
    // No-op for memory writing
    (void)png_ptr;
}

void test_png_transforms(const unsigned char* buffer, size_t length) {
    if (!buffer || length < 33) return;

    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png) return;

    png_infop info = png_create_info_struct(png);
    if (!info) {
        png_destroy_read_struct(&png, NULL, NULL);
        return;
    }

    if (setjmp(png_jmpbuf(png))) {
        png_destroy_read_struct(&png, &info, NULL);
        return;
    }

    struct memory_buffer mem = {
        .buffer = buffer,
        .size = length,
        .position = 0
    };

    png_set_read_fn(png, &mem, read_from_memory);

    // Read header
    png_read_info(png, info);

    // Get image info
    int width = png_get_image_width(png, info);
    int height = png_get_image_height(png, info);
    png_byte color_type = png_get_color_type(png, info);
    png_byte bit_depth = png_get_bit_depth(png, info);

    // Test various transformations
    if (color_type & PNG_COLOR_MASK_ALPHA) {
        png_set_strip_alpha(png);
    }

    if (bit_depth == 16) {
        png_set_strip_16(png);
    }

    if (color_type == PNG_COLOR_TYPE_GRAY && bit_depth < 8) {
        png_set_expand_gray_1_2_4_to_8(png);
    }

    if (color_type == PNG_COLOR_TYPE_GRAY ||
        color_type == PNG_COLOR_TYPE_GRAY_ALPHA) {
        png_set_gray_to_rgb(png);
    }

    // Test gamma correction
    png_set_gamma(png, 2.2, 0.45455);

    // Test background color
    png_color_16 background = {0, 65535, 65535, 65535, 65535};
    png_set_background(png, &background, PNG_BACKGROUND_GAMMA_SCREEN, 0, 1.0);

    // Update info after transforms
    png_read_update_info(png, info);

    // Read image data if dimensions are reasonable
    if (width > 0 && width <= 256 && height > 0 && height <= 256) {
        size_t row_bytes = png_get_rowbytes(png, info);
        if (row_bytes > 0 && row_bytes * height < 1024*1024) {
            png_bytep* row_pointers = (png_bytep*)malloc(height * sizeof(png_bytep));
            if (row_pointers) {
                int valid_alloc = 1;
                // Allocate rows
                for (int y = 0; y < height; y++) {
                    row_pointers[y] = (png_byte*)malloc(row_bytes);
                    if (!row_pointers[y]) {
                        valid_alloc = 0;
                        break;
                    }
                }

                if (valid_alloc) {
                    if (setjmp(png_jmpbuf(png)) == 0) {
                        png_read_image(png, row_pointers);
                    }
                }

                // Cleanup
                for (int y = 0; y < height; y++) {
                    free(row_pointers[y]);
                }
                free(row_pointers);
            }
        }
    }

    // Test chunk processing
    png_textp text_ptr;
    int num_text;
    if (png_get_text(png, info, &text_ptr, &num_text) > 0) {
        // Process text chunks
        png_text new_text;
        new_text.compression = PNG_TEXT_COMPRESSION_NONE;
        new_text.key = (png_charp)"Comment";
        new_text.text = (png_charp)"Fuzz test";
        new_text.text_length = 9;
        png_set_text(png, info, &new_text, 1);
    }

    // Test tRNS chunk
    png_bytep trans_alpha;
    int num_trans;
    png_color_16p trans_color;
    if (png_get_tRNS(png, info, &trans_alpha, &num_trans, &trans_color)) {
        // Process transparency
        if (trans_color) {
            png_color_16 new_trans = *trans_color;
            png_set_tRNS(png, info, trans_alpha, num_trans, &new_trans);
        }
    }

    png_destroy_read_struct(&png, &info, NULL);
}

// Test PNG writing
void test_png_writing(const unsigned char* buffer, size_t length) {
    if (!buffer || length < 33) return;

    // First read the PNG
    png_structp read_png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!read_png) return;

    png_infop read_info = png_create_info_struct(read_png);
    if (!read_info) {
        png_destroy_read_struct(&read_png, NULL, NULL);
        return;
    }

    if (setjmp(png_jmpbuf(read_png))) {
        png_destroy_read_struct(&read_png, &read_info, NULL);
        return;
    }

    struct memory_buffer read_mem = {
        .buffer = buffer,
        .size = length,
        .position = 0
    };

    png_set_read_fn(read_png, &read_mem, read_from_memory);
    png_read_info(read_png, read_info);

    // Now try to write it
    png_structp write_png = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!write_png) {
        png_destroy_read_struct(&read_png, &read_info, NULL);
        return;
    }

    png_infop write_info = png_create_info_struct(write_png);
    if (!write_info) {
        png_destroy_write_struct(&write_png, NULL);
        png_destroy_read_struct(&read_png, &read_info, NULL);
        return;
    }

    if (setjmp(png_jmpbuf(write_png))) {
        png_destroy_write_struct(&write_png, &write_info);
        png_destroy_read_struct(&read_png, &read_info, NULL);
        return;
    }

    png_set_write_fn(write_png, NULL, write_to_memory, flush_memory);

    // Copy IHDR
    png_uint_32 width, height;
    int bit_depth, color_type, interlace_type, compression_type, filter_method;
    png_get_IHDR(read_png, read_info, &width, &height, &bit_depth, &color_type,
                 &interlace_type, &compression_type, &filter_method);
    png_set_IHDR(write_png, write_info, width, height, bit_depth, color_type,
                 interlace_type, compression_type, filter_method);

    // Write header
    png_write_info(write_png, write_info);

    // Read and write image data
    if (width > 0 && width <= 256 && height > 0 && height <= 256) {
        png_uint_32 row_bytes = png_get_rowbytes(read_png, read_info);
        if (row_bytes > 0 && row_bytes * height < 1024*1024) {
            png_bytep* row_pointers = (png_bytep*)malloc(height * sizeof(png_bytep));
            if (row_pointers) {
                int valid_alloc = 1;
                // Allocate rows
                for (png_uint_32 y = 0; y < height; y++) {
                    row_pointers[y] = (png_byte*)malloc(row_bytes);
                    if (!row_pointers[y]) {
                        valid_alloc = 0;
                        break;
                    }
                }

                if (valid_alloc) {
                    if (setjmp(png_jmpbuf(read_png)) == 0) {
                        png_read_image(read_png, row_pointers);
                    }
                    if (setjmp(png_jmpbuf(write_png)) == 0) {
                        png_write_image(write_png, row_pointers);
                    }
                }

                // Cleanup
                for (png_uint_32 y = 0; y < height; y++) {
                    free(row_pointers[y]);
                }
                free(row_pointers);
            }
        }
    }

    png_write_end(write_png, write_info);
    png_destroy_write_struct(&write_png, &write_info);
    png_destroy_read_struct(&read_png, &read_info, NULL);
}

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    // Test various PNG reading and transformation operations
    test_png_transforms(Data, Size);

    // Test PNG writing operations
    test_png_writing(Data, Size);

    return 0;
}