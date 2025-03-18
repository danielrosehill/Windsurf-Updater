#!/bin/bash
# Script to compress GIF files for GitHub
# Usage: ./compress-gif.sh input.gif [output.gif]

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 input.gif [output.gif]"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${2:-compressed_$(basename "$INPUT_FILE")}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found"
    exit 1
fi

echo "Original file size:"
ls -lh "$INPUT_FILE"

echo "Compressing GIF..."
ffmpeg -i "$INPUT_FILE" -vf "scale=640:-1:flags=lanczos,fps=10" -c:v gif -f gif "$OUTPUT_FILE"

echo "Compressed file size:"
ls -lh "$OUTPUT_FILE"

echo "Compression complete! New file: $OUTPUT_FILE"
