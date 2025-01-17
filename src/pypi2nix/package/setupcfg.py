from setuptools.config import read_configuration

from pypi2nix.logger import Logger
from pypi2nix.requirement_parser import ParsingFailed
from pypi2nix.requirement_parser import RequirementParser
from pypi2nix.requirement_set import RequirementSet
from pypi2nix.target_platform import TargetPlatform

from .interfaces import HasBuildDependencies


class SetupCfg(HasBuildDependencies):
    def __init__(
        self,
        name: str,
        setup_cfg_path: str,
        logger: Logger,
        requirement_parser: RequirementParser,
    ):
        self.name = name
        self.setup_cfg = read_configuration(setup_cfg_path)
        self.logger = logger
        self.requirement_parser = requirement_parser

    def build_dependencies(self, target_platform: TargetPlatform) -> RequirementSet:
        setup_requires = self.setup_cfg.get("options", {}).get("setup_requires")
        requirements = RequirementSet(target_platform)
        if isinstance(setup_requires, str):
            requirements.add(self.requirement_parser.parse(setup_requires))
        elif isinstance(setup_requires, list):
            for requirement_string in setup_requires:
                try:
                    requirement = self.requirement_parser.parse(requirement_string)
                except ParsingFailed as e:
                    self.logger.warning(
                        "Failed to parse build dependency of `{name}`".format(
                            name=self.name
                        )
                    )
                    self.logger.warning(
                        "Possible reason: `{reason}`".format(reason=e.reason)
                    )
                else:
                    if requirement.applies_to_target(target_platform):
                        requirements.add(requirement)
        return requirements
