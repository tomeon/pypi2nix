import os
import os.path

import pytest

from pypi2nix.archive import Archive
from pypi2nix.logger import Logger
from pypi2nix.requirement_parser import requirement_parser
from pypi2nix.requirement_set import RequirementSet
from pypi2nix.source_distribution import DistributionNotDetected
from pypi2nix.source_distribution import SourceDistribution

from .logger import get_logger_output
from .switches import nix


@pytest.fixture
def source_distribution(six_source_distribution_archive, logger):
    return SourceDistribution.from_archive(six_source_distribution_archive, logger)


@pytest.fixture
def flit_requirements(current_platform):
    requirements = RequirementSet(current_platform)
    requirements.add(requirement_parser.parse("flit == 1.3"))
    return requirements


@pytest.fixture
def flit_distribution(pip, project_dir, download_dir, flit_requirements, logger):
    pip.download_sources(flit_requirements, download_dir)
    archives = [
        Archive(path=os.path.join(download_dir, filename))
        for filename in os.listdir(download_dir)
    ]
    distributions = list(
        map(lambda archive: SourceDistribution.from_archive(archive, logger), archives)
    )
    for distribution in distributions:
        if distribution.name == "flit":
            return distribution
    raise Exception("Could not download source distribution for `flit`")


@nix
def test_from_archive_picks_up_on_name(source_distribution):
    assert source_distribution.name == "six"


@nix
def test_that_a_source_distributions_name_is_canonicalized(logger):
    distribution = SourceDistribution(name="NaMe_teSt", logger=logger)
    assert distribution.name == "name-test"


@nix
def test_six_package_has_no_pyproject_toml(source_distribution):
    assert source_distribution.pyproject_toml is None


@nix
def test_that_flit_pyproject_toml_is_recognized(flit_distribution):
    assert flit_distribution.pyproject_toml is not None


@nix
def test_that_flit_build_dependencies_contains_requests(
    flit_distribution, current_platform
):
    assert "requests" in flit_distribution.build_dependencies(current_platform)


@nix
def test_that_we_can_generate_objects_from_source_archives(
    source_distribution_archive, logger
):
    SourceDistribution.from_archive(source_distribution_archive, logger)


@nix
def test_that_we_can_detect_setup_requirements_for_setup_cfg_projects(
    distribution_archive_for_jsonschema, current_platform, logger
):
    distribution = SourceDistribution.from_archive(
        distribution_archive_for_jsonschema, logger
    )
    assert "setuptools-scm" in distribution.build_dependencies(current_platform)


def test_that_trying_to_create_source_distribution_from_random_zip_throws(
    test_zip_path, logger
):
    archive = Archive(path=test_zip_path)
    with pytest.raises(DistributionNotDetected):
        SourceDistribution.from_archive(archive, logger)


def test_build_dependencies_for_invalid_deps_logs_warning(
    data_directory, current_platform, logger: Logger
):
    spacy_distribution_path = os.path.join(data_directory, "spacy-2.1.0.tar.gz")
    archive = Archive(spacy_distribution_path)

    dist = SourceDistribution.from_archive(archive, logger)

    assert "WARNING:" not in get_logger_output(logger)
    dist.build_dependencies(current_platform)
    assert "WARNING:" in get_logger_output(logger)


def test_invalid_build_dependencies_for_setupcfg_package_logs_warning(
    data_directory, current_platform, logger
):
    distribution_path = os.path.join(
        data_directory, "setupcfg-package", "setupcfg-package.tar.gz"
    )
    archive = Archive(distribution_path)

    dist = SourceDistribution.from_archive(archive, logger)

    assert "WARNING:" not in get_logger_output(logger)
    dist.build_dependencies(current_platform)
    assert "WARNING:" in get_logger_output(logger)