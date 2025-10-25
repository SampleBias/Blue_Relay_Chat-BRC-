"""
Compression utilities for Blue Relay Chat RPi 4 client.

This module provides compression and decompression functions for
optimizing message size and storage efficiency.
"""

try:
    import lz4.frame
    import lz4.block
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False
    # Create fallback compression functions
    def compress(data):
        return data
    def decompress(data):
        return data

from typing import Optional, Union

from ..exceptions import ValidationError
from ..constants import COMPRESSION_ALGORITHM, COMPRESSION_THRESHOLD


def compress(data: bytes, algorithm: str = COMPRESSION_ALGORITHM) -> bytes:
    """
    Compress data using the specified algorithm.
    
    Args:
        data: Data to compress
        algorithm: Compression algorithm to use
        
    Returns:
        Compressed data
    """
    if not data:
        return data
    
    try:
        if algorithm == "lz4" and LZ4_AVAILABLE:
            # Use LZ4 frame compression
            return lz4.frame.compress(data)
        else:
            # Use fallback (no compression)
            return data
    except Exception as e:
        raise ValidationError(f"Compression failed: {e}")


def decompress(compressed_data: bytes, algorithm: str = COMPRESSION_ALGORITHM) -> bytes:
    """
    Decompress data using the specified algorithm.
    
    Args:
        compressed_data: Compressed data
        algorithm: Compression algorithm that was used
        
    Returns:
        Decompressed data
    """
    if not compressed_data:
        return compressed_data
    
    try:
        if algorithm == "lz4" and LZ4_AVAILABLE:
            # Use LZ4 frame decompression
            return lz4.frame.decompress(compressed_data)
        else:
            # Use fallback (no decompression)
            return compressed_data
    except Exception as e:
        raise ValidationError(f"Decompression failed: {e}")


def compress_string(text: str, algorithm: str = COMPRESSION_ALGORITHM) -> bytes:
    """
    Compress a string.
    
    Args:
        text: String to compress
        algorithm: Compression algorithm to use
        
    Returns:
        Compressed data
    """
    if not text:
        return b""
    
    data = text.encode('utf-8')
    return compress(data, algorithm)


def decompress_to_string(compressed_data: bytes, algorithm: str = COMPRESSION_ALGORITHM) -> str:
    """
    Decompress data to a string.
    
    Args:
        compressed_data: Compressed data
        algorithm: Compression algorithm that was used
        
    Returns:
        Decompressed string
    """
    if not compressed_data:
        return ""
    
    data = decompress(compressed_data, algorithm)
    return data.decode('utf-8')


def should_compress(data: Union[bytes, str], threshold: int = COMPRESSION_THRESHOLD) -> bool:
    """
    Check if data should be compressed based on size.
    
    Args:
        data: Data to check
        threshold: Size threshold in bytes
        
    Returns:
        True if data should be compressed, False otherwise
    """
    if isinstance(data, str):
        size = len(data.encode('utf-8'))
    else:
        size = len(data)
    
    return size >= threshold


def compress_if_needed(data: Union[bytes, str], algorithm: str = COMPRESSION_ALGORITHM, 
                      threshold: int = COMPRESSION_THRESHOLD) -> tuple:
    """
    Compress data if it's larger than the threshold.
    
    Args:
        data: Data to potentially compress
        algorithm: Compression algorithm to use
        threshold: Size threshold in bytes
        
    Returns:
        Tuple of (compressed_data, was_compressed)
    """
    if not should_compress(data, threshold):
        if isinstance(data, str):
            return data.encode('utf-8'), False
        else:
            return data, False
    
    if isinstance(data, str):
        compressed = compress_string(data, algorithm)
    else:
        compressed = compress(data, algorithm)
    
    return compressed, True


def decompress_if_needed(data: bytes, was_compressed: bool, 
                         algorithm: str = COMPRESSION_ALGORITHM) -> Union[bytes, str]:
    """
    Decompress data if it was compressed.
    
    Args:
        data: Data to potentially decompress
        was_compressed: Whether the data was compressed
        algorithm: Compression algorithm that was used
        
    Returns:
        Decompressed data
    """
    if not was_compressed:
        return data
    
    return decompress(data, algorithm)


def get_compression_info(data: Union[bytes, str], algorithm: str = COMPRESSION_ALGORITHM) -> dict:
    """
    Get information about compression for the given data.
    
    Args:
        data: Data to analyze
        algorithm: Compression algorithm to use
        
    Returns:
        Dictionary containing compression information
    """
    if isinstance(data, str):
        original_size = len(data.encode('utf-8'))
    else:
        original_size = len(data)
    
    info = {
        "original_size": original_size,
        "compressed_size": original_size,
        "compression_ratio": 1.0,
        "space_saved": 0,
        "should_compress": should_compress(data),
    }
    
    if info["should_compress"]:
        try:
            compressed = compress(data, algorithm)
            compressed_size = len(compressed)
            compression_ratio = compressed_size / original_size
            space_saved = original_size - compressed_size
            
            info.update({
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "space_saved": space_saved,
            })
        except Exception:
            # If compression fails, keep default values
            pass
    
    return info