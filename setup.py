from distutils.core import setup

setup(
    name='WalkoffAgain',
    version='',
    packages=['', 'apps', 'apps.HelloWorld', 'core', 'core.flags', 'core.filters', 'core.keywords', 'tests', 'server'],
    url='https://iadgov.github.io/WALKOFF/',
    license='Creative Commons',
    author='National Security Agency ',
    author_email='walkoff@nsa.gov',
    description='An active cyber defense development framework enabling orchestration capabilities to be written once and deployed across WALKOFF-enabled orchestration tools.',

    install_requires = ['blinker >= 1.4',
                        'Flask >= 0.10.0',
                        'Flask_Login >= 0.3.2, < 0.4.0',
                        'Flask_Principal >= 0.4.0',
                        'Flask_SQLAlchemy >= 2.1',
                        'Flask_Security >= 1.7.5',
                        'Flask_WTF >= 0.12',
                        'jinja2 >= 2.8',
                        'sqlalchemy >= 1.0.12',
                        'wtforms >= 2.1',
                        'werkzeug >= 0.11.4',
                        'requests >= 2.9.1',
                        'APscheduler >= 3.0.0',
                        'gevent',
                        'importlib']
)
