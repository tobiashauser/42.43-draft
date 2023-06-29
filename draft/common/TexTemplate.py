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
    - Exercise

    This class ssets default prefixes and suffixes
    for a tex document.

    This class provides methods to remove the
    document environment and the including of
    the preamble.
    """

    @property
    def body(self) -> str:
        """Return the document body of the template."""
        pattern = re.compile(r"\\begin{document}\n(.*?)\\end{document}", re.DOTALL)
        match = re.search(pattern, self.contents)
        if match:
            return match.group(1)
        else:
            return ""

    @property
    def declarations(self) -> str:
        """
        Return the declarations in the template.

        Those are the contents without the document body.
        """
        cache = self.contents
        self.remove_document_body()
        result = self.contents
        self._contents = cache
        return result

    def __init__(self, path: Path, configuration: Configuration):
        super().__init__(configuration=configuration, path=path)

    def load(self):
        """
        Customize the loading function to strip the template
        of the neccessary parts.
        """
        raise NotImplementedError

    def remove_document_body(self):
        super().remove_blocks(prefix=r"\\begin{document}", suffix=r"\\end{document}")

    def remove_include_preamble(self):
        super().remove_lines(prefix=r"\\input{(?:.*?)preamble(?:\.tex)?}")
