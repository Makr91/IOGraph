import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='IOGraph',  
     version='0.0.30',
     scripts=['./scripts/IOGraph'],
     package_data={
        'IOGraph': [ 'conf.yml.dist' ] 
     },
     author="Mark Gilbert",
     author_email='support@philotic.cloud',
     long_description=long_description,
     description='Generate Plotly Graphs from IOZone Data',
     long_description_content_type="text/markdown",
     url='http://pypi.python.org/Makr91/IOGraph/',
     packages=['IOGraph'],
     install_requires=[
        'setuptools',
        'pandas >= 0.22.0',
        'plotly >= 5.0.0rc2',
        'xlrd >= 2.0.1',
        'PyYAML >= 5.3.1',
        'dash >= 1.2.0 ',
        'Cython >= 0.29.23',
        'dash-core-components >= 1.16.0',
        'dash-html-components >= 1.1.3',
        'dash-renderer >= 1.9.1',
        'dash-table >= 4.11.3',
        'openpyxl >= 3.0.7',
        'argparse >= 1.4.0',
        'appdirs >= 1.4.4',
        'distro >= 1.5.0',
        'xlutils >= 2.0.0',
        'xlwt >= 1.3.0',
        'numpy >= 1.16.0',
        'psutil >= 5.6.3'
     ],
     python_requires='>=3.5',
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: Apache Software License",
         "Operating System :: OS Independent",
     ],
 )

