from pageindex.errors import (
    PageIndexError,
    CollectionNotFoundError,
    DocumentNotFoundError,
    IndexingError,
    CloudAPIError,
    FileTypeError,
)


def test_all_errors_inherit_from_base():
    for cls in [CollectionNotFoundError, DocumentNotFoundError, IndexingError, CloudAPIError, FileTypeError]:
        assert issubclass(cls, PageIndexError)
        assert issubclass(cls, Exception)


def test_error_message():
    err = FileTypeError("Unsupported: .docx")
    assert str(err) == "Unsupported: .docx"


def test_catch_base_catches_all():
    for cls in [CollectionNotFoundError, DocumentNotFoundError, IndexingError, CloudAPIError, FileTypeError]:
        try:
            raise cls("test")
        except PageIndexError:
            pass  # expected
