from setuptools import setup, find_packages

setup(
    name='smartdjango',
    version='4.3.4',
    keywords=['django'],
    description='fast Django app development',
    long_description='field validation detector, model advanced search, unified error class',
    license='MIT Licence',
    url='https://github.com/Jyonn/smartdjango',
    author='Jyonn Liu',
    author_email='i@6-79.cn',
    platforms='any',
    packages=find_packages(),
    install_requires=[
        'django',
        'oba',
        'diq',
    ],
)
