from setuptools import setup, find_packages

# python setup.py install
# pip uninstall msc-control-flow-fleshing-project

def parse_requirements(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]

setup(
    name='msc-control-flow-fleshing-project',
    version='0.1',
    author='Max Mitchell',
    author_email='mbm22@doc.ic.ac.uk',
    description='A project testing compilers with control flow fleshing',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mbdmitchell/msc-individual-project',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['config.json'],
    },
    python_requires='>=3.9',
    install_requires=parse_requirements('requirements.txt'),
    test_suite='test',
)