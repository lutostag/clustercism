import os
import lzma
import bz2
import zlib
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


list_ = []
for filename in os.listdir("rust/anagram"):
    dist = information_distance(
        "rust/anagram/e6044fb7ce864beb9df2641ee43bbf05.tar", "rust/anagram/" + filename
    )
    list_.append((dist, filename))

list_.sort()
print("\n".join([str(i) for i in list_]))
