import os
from io import open
from setuptools import setup, find_packages

HERE = os.path.dirname(__file__)

extras_require = {}
_extras_groups = [
    ("requirements", "requirements.txt"),
]
for group, filepath in _extras_groups:
    with open(os.path.join(HERE, filepath), 'r') as f:
        extras_require[group] = f.readlines()

# Get the long description from the relevant file
with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ckanext-googleanalytics",
    
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version="1.0.0",
    
    description="Add GA tracking and reporting to CKAN instance",
    long_description=long_description,
    long_description_content_type="text/markdown",

    # The project's main homepage.
    url='https://github.com/fjelltopp/ckanext-googleanalytics4',

    # Author details
    author="Seb Bacon, Ntwali Bashige",
    author_email="seb.bacon@gmail.com, ntwali.bashige@gmail.com",
    
    # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        # 3 - Alpha
        # 4 - Beta
        # 5 - Production/Stable
        "Development Status :: 4 - Beta",

        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3.7",
    ],
    
    # What does your project relate to?
    keywords="CKAN, Google Analytics 4",

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    namespace_packages=["ckanext", "ckanext.googleanalytics"],

    install_requires=[
      # CKAN extensions should not list dependencies here, but in a separate
      # ``requirements.txt`` file.
      #
      # http://docs.ckan.org/en/latest/extensions/best-practices.html
      # add-third-party-libraries-to-requirements-txt
    ],
    extras_require=extras_require,
    include_package_data=True,
    zip_safe=False,
    
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages.
    # see http://docs.python.org/3.4/distutils/setupscript.html
    # installing-additional-files
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points="""
        [ckan.plugins]
        googleanalytics=ckanext.googleanalytics.plugin:GoogleAnalyticsPlugin
    """,
)
