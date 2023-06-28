import re
from abc import ABC
from pathlib import Path
from typing import Any, Callable, Dict, List, Set

import oyaml as yaml

from draft.common.Configuration import Configuration
from draft.common.File import File
from draft.common.helpers import combine_dictionaries


class Template(File, ABC):
    """
    A abstract class representing a template, that is, a file
    on the disk.

    Conforming types are:
    - TexTemplate (ABC)

    Subclasses should remember to call `super().__init__()`
    if they implement their own initializer.
    """

    @property
    def configuration(self) -> Configuration:
        return self._configuration

    @property
    def placeholder_prefix(self) -> str:
        return self._placeholder_prefix

    @property
    def placeholder_suffix(self) -> str:
        return self._placeholder_suffix

    @property
    def placeholders(self) -> Set[str]:
        return self._placeholders

    @property
    def prompts(self) -> List[Dict[str, Any]]:
        return self._prompts

    @property
    def block_comment_prefix(self) -> str:
        return self._block_comment_prefix

    @property
    def block_comment_suffix(self) -> str:
        return self._block_comment_suffix

    @property
    def yaml(self) -> Dict[str, Any]:
        return self._yaml

    @property
    def single_line_comment_prefix(self) -> str:
        return self._single_line_comment_prefix

    def __init__(
        self,
        configuration: Configuration,
        path: Path,
        placeholder_prefix: str,
        placeholder_suffix: str,
        single_line_comment_prefix: str,
        block_comment_prefix: str,
        block_comment_suffix: str,
    ):
        """
        Take care to pass properly escaped string literals for
        `placeholder_prefix`, `placeholder_suffix`, `yaml_prefix`,
        `yaml_suffix` to the initialiser:

        ```
        yaml_prefix=r"\\iffalse",
        ```

        Always pass a reference to a global configuration
        in the initializer. The prompts rely on having
        the newest version of the configuration.
        """
        super().__init__(path=path)
        self._configuration = configuration

        # Placeholders
        self._placeholder_prefix: str = placeholder_prefix
        self._placeholder_suffix: str = placeholder_suffix
        self.__init_placeholders__()

        # YAML
        self._block_comment_prefix = block_comment_prefix
        self._block_comment_suffix = block_comment_suffix
        self.__init_yaml__()

        # Single Line comments
        self._single_line_comment_prefix = single_line_comment_prefix
        if configuration.get("remove_comments", False):
            self.remove_comments()

        # Prompts
        self.__init_prompts__()

    def __init_placeholders__(self):
        """
        Extract handlebars like `<<semester>>` from the
        contents of the template.
        """
        pattern = re.compile(
            r"%s([^\s.]+?)%s" % (self.placeholder_prefix, self.placeholder_suffix)
        )
        matches = pattern.findall(self.contents)
        self._placeholders = set(matches)

    def __init_yaml__(self):
        """
        Parse and combine YAML-frontmatter from all the
        block comments in the contents.

        YAML-blocks closer to the top of the document take
        priority over those further down.
        List and dictionary values will be combined.
        """

        # Extract all the block comments
        pattern = re.compile(
            "(?s)\n%s(.*?)%s" % (self.block_comment_prefix, self.block_comment_suffix)
        )
        matches = pattern.findall(self.contents)

        dict: Dict[str, Any] = {}

        # Iterate over all the block comments
        for match in matches:
            try:
                dict = combine_dictionaries(dict, yaml.safe_load(match))
            except:
                pass

        self._yaml = dict

    def __init_prompts__(self):
        """
        Create prompts for PyInquirer from the placeholders
        in the file if a value doesn't yet exist in the
        configuration.

        They can be customized in any YAML-block.
        """

        def exists(key: str) -> Callable[..., bool]:
            return lambda: key not in self.configuration

        prompts: List[Dict[str, Any]] = []

        for placeholder in self.placeholders:
            question: Dict[str, Any] = {}

            # ignore `<<draft-exercises>>`
            if placeholder == "draft-exercises":
                continue

            # set the minimum default values
            question["name"] = placeholder
            question["type"] = "input"
            question["message"] = "Please provide the '%s'." % placeholder

            # customize if this placeholder was customized
            if isinstance(self.yaml.get(placeholder, {}), dict):
                for key, value in self.yaml.get(placeholder, {}).items():
                    # the name cannot be customized
                    if key == "name":
                        continue
                    elif key == "validate":
                        if self.configuration.get("allow_eval", False):
                            question[key] = eval(value)
                    elif key == "when":
                        if self.configuration.get("allow_eval", False):
                            question[key] = eval(value) and exists(question["name"])
                    else:
                        question[key] = value

            # Insert when condition
            if "when" not in question:
                question["when"] = exists(question["name"])

            prompts.append(question)

        self._prompts = prompts

    def remove_comments(self):
        """
        Remove single line comments and block
        contents from the string.
        """

        # Remove single line comments
        # pattern = re.compile("(^\n)?%s(.*)(\n)?" % (self.single_line_comment_prefix))
        pattern = re.compile("\v*%s(?:.*)\v*" % (self.single_line_comment_prefix))
        self._contents = re.sub(pattern, "", self.contents)

        # Remove block comments
        pattern = re.compile(
            # "(?s)(\n)?%s(.*?)%s(\n)?"
            "(?s)\v*%s(?:.*?)%s\v*"
            % (self.block_comment_prefix, self.block_comment_suffix)
        )
        self._contents = re.sub(pattern, "", self.contents)