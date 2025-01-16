#include <stdio.h>
#include <stdlib.h>
#include <turbojpeg.h>
#include <stdint.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) {
        return 0;  // Reject empty inputs
    }

    int width, height, subsamp, colorspace;
    tjhandle tj_handle;

    // Initialize TurboJPEG decompressor
    tj_handle = tjInitDecompress();
    if (tj_handle == NULL) {
        return 0;  // Initialization failed, but don't crash
    }

    // Try to read JPEG header
    int header_result = tjDecompressHeader3(
        tj_handle,
        data,  // Use the fuzz input directly
        size,
        &width,
        &height,
        &subsamp,
        &colorspace
    );

    if (header_result == 0) {
        // Header was successfully parsed, try to decompress
        unsigned char *output_buffer = NULL;
        int pixel_format = TJPF_RGB;  // Choose desired pixel format
        int pitch = width * tjPixelSize[pixel_format];

        // Allocate output buffer
        output_buffer = (unsigned char*)malloc(pitch * height);
        if (output_buffer) {
            // Actually try to decompress the image
            tjDecompress2(
                tj_handle,
                data,
                size,
                output_buffer,
                width,
                pitch,
                height,
                pixel_format,
                0  // Flags
            );

            free(output_buffer);
        }
    }

    // Clean up
    tjDestroy(tj_handle);
    return 0;  // Non-zero return values are reserved for future use
}

#ifndef FUZZING
int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <jpeg_file>\n", argv[0]);
        return 1;
    }

    // Open and read the file
    FILE *fp = fopen(argv[1], "rb");
    if (!fp) {
        fprintf(stderr, "Cannot open file: %s\n", argv[1]);
        return 1;
    }

    // Get file size
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    rewind(fp);

    // Allocate buffer
    uint8_t *buffer = (uint8_t*)malloc(file_size);
    if (!buffer) {
        fprintf(stderr, "Memory allocation failed\n");
        fclose(fp);
        return 1;
    }

    // Read file content
    size_t read_size = fread(buffer, 1, file_size, fp);
    fclose(fp);

    if (read_size != (size_t)file_size) {
        fprintf(stderr, "Failed to read entire file\n");
        free(buffer);
        return 1;
    }

    // Run the fuzzer entry point with our file data
    int result = LLVMFuzzerTestOneInput(buffer, file_size);

    free(buffer);
    return result;
}
#endif