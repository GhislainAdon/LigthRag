class PageIndexError(Exception):
    """Base exception for all PageIndex SDK errors."""
    pass


class CollectionNotFoundError(PageIndexError):
    """Collection does not exist."""
    pass


class DocumentNotFoundError(PageIndexError):
    """Document ID not found."""
    pass


class IndexingError(PageIndexError):
    """Indexing pipeline failure."""
    pass


class CloudAPIError(PageIndexError):
    """Cloud API returned error."""
    pass


class FileTypeError(PageIndexError):
    """Unsupported file type."""
    pass
