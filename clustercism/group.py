import os
import lzma
import bz2
import zlib
import json
import shutil
from functools import partial

BZ2 = partial(bz2.BZ2Compressor)
LZMA = partial(
    lzma.LZMACompressor,
    format=lzma.FORMAT_RAW,
    check=lzma.CHECK_NONE,
    preset=None,
    filters=(
        {"id": lzma.FILTER_DELTA, "dist": 5},
        {"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME},
    ),
)
ZLIB = partial(zlib.compressobj)


def compressed_len(stream, compressor=LZMA):
    compressor = compressor()
    compressed = compressor.compress(stream)
    compressed += compressor.flush()
    return len(compressed)


def information_distance(filename_a, filename_b):
    with open(filename_a, "rb") as fd_a:
        contents_a = fd_a.read()
    with open(filename_b, "rb") as fd_b:
        contents_b = fd_b.read()
    comp_len_a = compressed_len(contents_a)
    comp_len_b = compressed_len(contents_b)

    min_comp_len = min(comp_len_a, comp_len_b)
    max_comp_len = max(comp_len_a, comp_len_b)
    comb_comp_len = compressed_len(contents_a + contents_b)

    return (comb_comp_len - min_comp_len) / max_comp_len


def main(dir_):
    files = set(os.listdir(dir_))
    try:
        with open("info.json", "r") as fd:
            total = json.load(fd)
            already_processed = set(total.keys())
            files -= already_processed
    except FileNotFoundError:
        total = {}

    print(f"{len(files)} left to process")

    for idx, file_i in enumerate(files):
        file_distances = {}
        for file_j in os.listdir(dir_):
            dist = information_distance(
                os.path.join(dir_, file_i), os.path.join(dir_, file_j)
            )
            file_distances[file_j] = dist
        total[file_i] = file_distances
        print(f"{idx}/{len(files)}")
        with open("info.json-new", "w") as fp:
            json.dump(total, fp)
        shutil.move("info.json-new", "info.json")


main("anagram2")
