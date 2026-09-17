"""
LZO decompression and CSV-to-Parquet conversion utilities for OMOP datasets.
Uses ctypes binding to liblzo2-2.dll to decompress lzop/lzo compressed CSVs.
"""

import os
import struct
import ctypes
import glob
from pathlib import Path
import duckdb

# Locate liblzo2 DLL
_LZO_DLL_PATHS = [
    r"C:\msys64\ucrt64\bin\liblzo2-2.dll",
    r"C:\msys64\usr\bin\msys-lzo2-2.dll",
    "liblzo2-2.dll",
    "lzo2.dll",
]

_lzo_dll = None
_lzo1x_decompress = None

def _get_lzo_decompress_func():
    global _lzo_dll, _lzo1x_decompress
    if _lzo1x_decompress is not None:
        return _lzo1x_decompress
    
    for path in _LZO_DLL_PATHS:
        if os.path.exists(path) or not os.path.isabs(path):
            try:
                _lzo_dll = ctypes.CDLL(path)
                break
            except Exception:
                continue
    
    if _lzo_dll is None:
        raise RuntimeError(f"Could not load liblzo2 DLL from paths: {_LZO_DLL_PATHS}")
    
    func = _lzo_dll.lzo1x_decompress_safe
    func.argtypes = [
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_void_p
    ]
    func.restype = ctypes.c_int
    _lzo1x_decompress = func
    return _lzo1x_decompress


def decompress_lzo_to_csv(lzo_path: str, output_csv_path: str, chunk_callback=None) -> str:
    """
    Decompresses an LZOP file (.lzo) into an uncompressed CSV file streaming block by block.
    """
    decompress_func = _get_lzo_decompress_func()
    os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)
    
    with open(lzo_path, "rb") as fin, open(output_csv_path, "wb") as fout:
        magic = fin.read(9)
        if magic != b"\x89LZO\x00\r\n\x1a\n":
            raise ValueError(f"Invalid LZOP magic in file: {lzo_path}")
        
        version, lib_version, req_version, method, level = struct.unpack(">HHHBB", fin.read(8))
        flags, mode, mtime_low = struct.unpack(">III", fin.read(12))
        if version >= 0x0940:
            mtime_high, = struct.unpack(">I", fin.read(4))
        name_len, = struct.unpack(">B", fin.read(1))
        filename = fin.read(name_len)
        header_checksum = fin.read(4)
        if flags & 0x00000800:  # F_H_EXTRA_FIELD
            extra_len, = struct.unpack(">I", fin.read(4))
            fin.read(extra_len)
            fin.read(4)  # extra checksum
        
        block_idx = 0
        while True:
            raw_dst_len = fin.read(4)
            if not raw_dst_len or len(raw_dst_len) < 4:
                break
            dst_len, = struct.unpack(">I", raw_dst_len)
            if dst_len == 0:
                # EOF block marker in LZOP
                break
            src_len, = struct.unpack(">I", fin.read(4))
            
            # Read uncompressed checksums
            if flags & 0x00000001:  # Adler32
                fin.read(4)
            if flags & 0x00000002:  # CRC32
                fin.read(4)
            
            if src_len < dst_len:
                if flags & 0x00000004:  # Adler32 compressed
                    fin.read(4)
                if flags & 0x00000008:  # CRC32 compressed
                    fin.read(4)
                compressed_data = fin.read(src_len)
                dst_buf = ctypes.create_string_buffer(dst_len)
                out_len = ctypes.c_size_t(dst_len)
                res = decompress_func(compressed_data, src_len, dst_buf, ctypes.byref(out_len), None)
                if res != 0:
                    raise RuntimeError(f"LZO decompression failed with code {res} at block {block_idx}")
                fout.write(dst_buf.raw[:out_len.value])
            else:
                uncompressed_data = fin.read(src_len)
                fout.write(uncompressed_data)
            
            block_idx += 1
            if chunk_callback and block_idx % 1000 == 0:
                chunk_callback(block_idx)
                
    return output_csv_path


def convert_table_to_parquet(
    lzo_path: str,
    parquet_path: str,
    csv_temp_dir: str = "data/temp_csv",
    table_name: str = None
) -> str:
    """
    Decompresses an .lzo file and converts it into an optimized Parquet file using DuckDB.
    """
    if table_name is None:
        table_name = Path(lzo_path).stem.replace(".csv", "")
    
    os.makedirs(os.path.dirname(os.path.abspath(parquet_path)), exist_ok=True)
    temp_csv_path = os.path.join(csv_temp_dir, f"{table_name}.csv")
    
    # If parquet already exists and is newer than lzo, skip
    if os.path.exists(parquet_path) and os.path.getmtime(parquet_path) >= os.path.getmtime(lzo_path):
        return parquet_path
    
    print(f"[{table_name}] Decompressing {lzo_path} -> {temp_csv_path}...")
    decompress_lzo_to_csv(lzo_path, temp_csv_path)
    
    print(f"[{table_name}] Converting {temp_csv_path} -> {parquet_path} using DuckDB...")
    con = duckdb.connect()
    
    # Define explicit schemas or auto-detect with proper date parsing
    con.execute(f"""
        COPY (
            SELECT * FROM read_csv_auto('{temp_csv_path.replace('\\', '/')}', header=True)
        ) TO '{parquet_path.replace('\\', '/')}' (FORMAT PARQUET, COMPRESSION ZSTD);
    """)
    con.close()
    
    # Clean up temp csv file
    if os.path.exists(temp_csv_path):
        os.remove(temp_csv_path)
        
    print(f"[{table_name}] Successfully created {parquet_path} ({os.path.getsize(parquet_path) / 1024 / 1024:.2f} MB)")
    return parquet_path


def ensure_parquet_tables(
    source_dir: str = "synthea100k",
    parquet_dir: str = "data/parquet",
    temp_csv_dir: str = "data/temp_csv"
) -> dict:
    """
    Ensures all available OMOP .csv.lzo tables in source_dir are converted to Parquet.
    Returns mapping of table_name -> parquet_path.
    """
    os.makedirs(parquet_dir, exist_ok=True)
    table_files = glob.glob(os.path.join(source_dir, "*.csv.lzo"))
    result = {}
    
    for lzo_file in table_files:
        table_name = Path(lzo_file).stem.replace(".csv", "")
        parquet_file = os.path.join(parquet_dir, f"{table_name}.parquet")
        convert_table_to_parquet(lzo_file, parquet_file, temp_csv_dir, table_name)
        result[table_name] = parquet_file
        
    return result


if __name__ == "__main__":
    tables = ensure_parquet_tables()
    print("Parquet tables ready:", tables)
