import ast
from pathlib import Path
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


assert sys.version_info >= (3, 6, 0), "typeshed_client requires Python 3.6+"


current_dir = Path(__file__).parent.resolve()


_version_re = re.compile(r'__version__\s+=\s+(?P<version>.*)')


with (current_dir / 'typeshed_client/__init__.py').open() as f:
    version = _version_re.search(f.read()).group('version')
    version = str(ast.literal_eval(version))


setup(
    name='typeshed_client',
    version=version,
    description="A library for accessing stubs in typeshed.",
    keywords='typeshed typing annotations',
    author='Jelle Zijlstra',
    author_email='jelle.zijlstra@gmail.com',
    url='https://github.com/JelleZijlstra/typeshed_client',
    license='MIT',
    packages=['typeshed_client'],
    install_requires=['mypy >= 0.501', 'mypy_extensions >= 0.1.0', 'typed_ast >= 1.0.3'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
    ],
)
