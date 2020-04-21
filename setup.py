from setuptools import setup, find_packages

setup(name='hashdiff',
      version='0.1.0',
      description='HashDiff toolkit for detecting changes in large directory structures and/or for backup management',
      url='http://github.com/velkoborsky/hashdiff',
      author='Jakub Velkoborsky',
      author_email='jakub@velkoborsky.eu',
      license='GPLv3',
      packages=find_packages(exclude=("tests",)),
      entry_points = {
            'console_scripts': [
                  'hsnap = hashdiff.hsnap.__main__:cli_main',
                  'hcmp = hashdiff.hcmp.__main__:cli_main'
            ]
      },
      zip_safe=False)
