from setuptools import setup, find_packages

version = '2.1.0'

setup(name='Solgema.fullcalendar',
      version=version,
      description="Solgema",
      long_description=open("README.rst").read() + "\n" +
                       open("CHANGES.txt").read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='Solgema, fullcalendar, diary',
      author='Martronic SA',
      author_email='martronic@martronic.ch',
      url='http://www.martronic.ch/Solgema/plone_products/solgema_fullcalendar',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Solgema'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'Solgema.ContextualContentMenu',
          'plone.app.z3cform',
          'plone.z3cform',
          'z3c.form',
          'collective.js.fullcalendar>=1.5.2.1',
          ],
      extra_requires={
          'Plone3':[
              'collective.js.jqueryui<1.8',
              ],
          'Plone4':[
              'collective.js.colorpicker',
              'collective.js.jqueryui>=1.8.16.4',
              ]
          },
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
