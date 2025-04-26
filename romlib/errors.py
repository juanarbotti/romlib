class UnsupportedROMError(Exception):
    """Raised when ROM is not supported."""
    pass

class FileFormatNotSupported(Exception):
    """Raised when format is not supported"""
    pass
class FileCompressionFormatNotSupported(Exception):
    """Raised when  a compression format is not supported"""
    pass
class DecompressionFailure(Exception):
    """Raised when a decompression was not succesfull."""
    pass
class DirectoryNotFound(Exception):
    """Raised when a directory is not found"""
    pass

class InvalidROMFile(Exception):
    """Raised when a ROM is not valid for a class"""
    pass

class NoROMLoaded(Exception):
    """Raised when a ROM is not loaded in a class"""
    pass

class FilesizeSmallerThanLenghts(Exception):
    """Raised when filesize is smaller than the bytes required for analyze."""
    pass

class ElementNotFound(Exception):
    """Raised when something is not found in the database."""
    pass