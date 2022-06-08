"""Based on the pypa sample-project

See: https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="dtnclient",
    version="0.1",
    description="Python client for dtn7-go",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CryptoCopter/dtnclient",
    author="Markus Sommer",
    author_email="msommer@informatik.uni-marburg.de",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)  ",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="dtn bundle",
    license="GPLv3+",
    packages=find_packages(),
    install_requires=["requests", "python-rapidjson"],
    zip_safe=True,
    project_urls={
        "Bug Reports": "https://github.com/CryptoCopter/dtnclient/issues",
        "Source": "https://github.com/CryptoCopter/dtnclient",
    },
    scripts=["dtnclient/dtnclient.py"],
)
