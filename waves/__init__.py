from importlib.metadata import version, PackageNotFoundError
import pathlib

from waves import builders
from waves import parameter_study

try:
    __version__ = version("waves")
except PackageNotFoundError:
    try:
        from waves import _version
        __version__ = _version.version
    except ImportError:
        import setuptools_scm
        __version__ = setuptools_scm.get_version(root=pathlib.Path(__file__).parent.parent)
