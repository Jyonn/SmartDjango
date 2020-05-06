from setuptools import setup, find_packages

setup(
    name='SmartDjango',
    version='3.6.4',
    keywords=('django',),
    description='更高效率的Django开发[Chinese Version]',
    long_description='提供智能模型用于字段检测，数据检索，错误类等',
    license='MIT Licence',
    url='https://github.com/lqj679ssn/SmartDjango',
    author='Adel Liu',
    author_email='i@6-79.cn',
    platforms='any',
    packages=find_packages(),
    install_requires=[
        'django>=2.2.5',
        'smartify>=0.0.2',
    ],
)
