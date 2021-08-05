from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')
with open('requirements.txt') as f:
    requirements = f.read().splitlines()
with open('dislash/__init__.py', 'r') as f:
    version = [line.split('=')[1].strip(" '\"") for line in f.read().splitlines() if line.startswith('__version__')][0]


setup(
    name='dislash.py',
    version=version,
    description='A python wrapper for message components and slash commands.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/EQUENOS/dislash.py',
    author='EQUENOS',
    author_email='equenos1@gmail.com',
    keywords='python, discord, slash, commands, api, discord-api, discord-py, slash-commands, message-components, buttons, select-menus',
    packages=['dislash', 'dislash.slash_commands', 'dislash.interactions', 'dislash.slash_commands._modifications'],
    python_requires='>=3.8, <4',
    install_requires=requirements,
    project_urls={
        'Documentation': 'https://dislashpy.readthedocs.io/en/latest',
        'Bug Reports': 'https://github.com/EQUENOS/dislash.py/issues',
        'Source': 'https://github.com/EQUENOS/dislash.py',
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)