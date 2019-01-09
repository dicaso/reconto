from setuptools import setup, find_packages

package = "reconto"
version = "0.0.1"

setup(name = package,
      version = version,
      description="REsearch COmpendium memeNTO",
      url='https://github.com/dicaso/reconto',
      author = 'Christophe Van Neste',
      author_email = 'christophe.vanneste@ugent.be',
      license = 'GNU GENERAL PUBLIC LICENSE',
      packages = find_packages(),
      install_requires = [
          'pyyaml',
          'plumbum',
          'docker'
      ],
      extras_require = {
          'dev':  ["ipython"],
      },
      package_data = {
          'reconto': [
              'templates/reconto.yml',
              'examples/hello.yml'
          ]
      },
      include_package_data = True,
      zip_safe = False,
      entry_points = {
          'console_scripts': [
              'reconto=reconto.__main__:main',
          ],
      },
      test_suite = 'nose.collector',
      tests_require = ['nose']
)

#To install with symlink, so that changes are immediately available:
#pip install -e .
