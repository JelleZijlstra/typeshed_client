import ast
import os
from pathlib import Path
import re
from setuptools import setup


current_dir = Path(__file__).parent.resolve()
ts_client_dir = current_dir / "typeshed_client"
typeshed_dir = ts_client_dir / "typeshed"


_version_re = re.compile(r"__version__\s+=\s+(?P<version>.*)")


with (ts_client_dir / "__init__.py").open() as f:
    version = _version_re.search(f.read()).group("version")
    version = str(ast.literal_eval(version))


def find_bundled_files():
    for root, _, files in os.walk(typeshed_dir):
        root_path = Path(root)
        for file in files:
            path = root_path / file
            if path.suffix == ".pyi" or path.name == "VERSIONS":
                yield str(path)


setup(
    name="typeshed_client",
    version=version,
    description="A library for accessing stubs in typeshed.",
    long_description=Path("README.rst").read_text(),
    keywords="typeshed typing annotations",
    author="Jelle Zijlstra",
    author_email="jelle.zijlstra@gmail.com",
    url="https://github.com/JelleZijlstra/typeshed_client",
    project_urls={
        "Bug Tracker": "https://github.com/JelleZijlstra/typeshed_client/issues"
    },
    license="MIT",
    packages=["typeshed_client"],
    install_requires=["typed_ast >= 1.0.3", "importlib_resources >= 1.4.0"],
    package_data={"typeshed_client": list(find_bundled_files())},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development",
    ],
    python_requires=">=3.6",
)
