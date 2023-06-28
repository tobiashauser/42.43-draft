import re
from abc import ABC
from pathlib import Path

from draft.common.Configuration import Configuration
from draft.common.Template import Template


class TexTemplate(Template, ABC):
    """
    An abstract class representing a template that is
    a `.tex` file.

    Subclasses are:
    - Preamble
    - Header

    This class ssets default prefixes and suffixes
    for a tex document.

    This class provides methods to remove the
    document environment and the including of
    the preamble.
    """

    def __init__(self, path: Path, configuration: Configuration):
        super().__init__(
            configuration=configuration,
            path=path,
            placeholder_prefix=r"<<",
            placeholder_suffix=r">>",
            block_comment_prefix=r"\\iffalse",
            block_comment_suffix=r"\\fi",
            single_line_comment_prefix=r"%",
        )

    def load(self):
        """
        Customize the loading function to strip the template
        of the neccessary parts.
        """
        raise NotImplementedError

    @staticmethod
    def remove_document_body(contents: str) -> str:
        # Remove the document environment
        pattern = re.compile(
            # "(?s)(\n)?%s(.*?)%s(?:\n)?" % (r"\\begin{document}", r"\\end{document}")
            "(?s)\v*%s(.*?)%s\v*"
            % (r"\\begin{document}", r"\\end{document}")
        )
        return re.sub(pattern, "", contents)

    @staticmethod
    def remove_include_preamble(contents: str) -> str:
        # pattern = re.compile(r"(?:^\n)?\\input{(?:.*?)preamble(?:\.tex)?}\n?(?:^\n)?")
        # pattern = re.compile(r"(?:^\n)*\\input{(?:.*?)preamble(?:\.tex)?}\n?(?:^\n)*")
        pattern = re.compile(r"\v*\\input{(?:.*?)preamble(?:\.tex)?}\v*")
        return re.sub(pattern, "", contents)