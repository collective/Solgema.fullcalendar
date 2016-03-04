# -*- coding:utf-8 -*-

from setuptools import find_packages
from setuptools import setup

version = '2.3.5'
long_description = (
    open('README.rst').read() + '\n' +
    open('CHANGES.rst').read()
)

setup(name='Solgema.fullcalendar',
      version=version,
      description='A complete implementation of Adam Shaw FullCalendar into Plone.',
      long_description=long_description,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'Framework :: Plone',
          'Framework :: Plone :: 4.0',
          'Framework :: Plone :: 4.1',
          'Framework :: Plone :: 4.2',
          'Framework :: Plone :: 4.3',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: OS Independent',
          'Programming Language :: JavaScript',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='Solgema, fullcalendar, diary, agenda, Plone',
      author='Martronic SA',
      author_email='martronic@martronic.ch',
      url='http://pypi.python.org/pypi/Solgema.fullcalendar',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Solgema'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'AccessControl',
          'collective.js.colorpicker',
          'collective.js.fullcalendar >=1.5.2.1',
          'collective.js.jqueryui',
          'plone.app.z3cform',
          'plone.formwidget.contenttree',
          'plone.indexer',
          'plone.z3cform',
          'Products.ATContentTypes',
          'Products.CMFCore',
          'Products.CMFPlone',
          'Products.GenericSetup',
          'setuptools',
          'Solgema.ContextualContentMenu',
          'z3c.form',
          'zope.component',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.schema',
      ],
      extras_require={
          'test': [
              'plone.app.robotframework',
              'plone.app.testing',
              'plone.browserlayer',
              'plone.testing',
              'robotsuite',
              'unittest2',
          ],
      },
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
