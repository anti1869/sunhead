from setuptools import setup, find_packages
import sys


if sys.version_info < (3, 5):
    raise Exception('This package requires Python 3.5 or higher.')


VERSION = "5.0.1"
PACKAGE_NAME = "sunhead"
SOURCE_DIR_NAME = "src"


def readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description="Framework for building asynchronous websites and micro-services on top of ``aiohttp``",
    author="Dmitry Litvinenko",
    author_email="anti1869@gmail.com",
    long_description=readme(),
    url="https://github.com/anti1869/sunhead",
    package_dir={'': SOURCE_DIR_NAME},
    packages=find_packages(SOURCE_DIR_NAME, exclude=('*.tests',)),
    include_package_data=True,
    zip_safe=False,
    package_data={},
    license='Apache 2',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Development Status :: 2 - Pre-Alpha',
    ],
    install_requires=[
        "aioamqp",
        "aiocron",
        "aiohttp >= 1.0.5, < 2.0",
        "aiohttp_autoreload",
        "colorlog",
        "simplejson",
        "prometheus_client",
        "psutil",
        "python-dateutil",
        "PyYAML",
    ],
    entry_points={
        'console_scripts': [
            'sun = sunhead.__main__:main',
        ],
    }
)
