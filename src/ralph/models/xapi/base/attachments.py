"""Base xAPI `Attachments` definitions."""

from typing import Optional

from pydantic import AnyUrl

from ..config import BaseModelWithConfig
from .common import IRI, LanguageMap


class BaseXapiAttachment(BaseModelWithConfig):
    """Pydantic model for `attachment` property.

    Attributes:
        usageType (IRI): Identifies the usage of this Attachment.
        display (LanguageMap): Consists of the Attachment's title.
        description (LanguageMap): Consists of the Attachment's description.
        contentType (str): Consists of the Attachment's content type.
        length (int): Consists of the length of the Attachment's data in octets.
        sha2 (str): Consists of the SHA-2 hash of the Attachment data.
        fileUrl (URL): Consists of the URL from which the Attachment can be retrieved.
    """

    usageType: IRI
    display: LanguageMap
    description: Optional[LanguageMap] = None
    contentType: str
    length: int
    sha2: str
    fileUrl: Optional[AnyUrl] = None
