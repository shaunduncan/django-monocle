from setuptools import setup, find_packages
version = '0.0.1'

print find_packages()
setup(name='django-monocle',
      version=version,
      description=("Django app for embedding rich content with scalability in mind"),
      classifiers=['Development Status :: 1 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Django Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: Utilities'],
      keywords='oembed rich content scalability',
      author='Shaun Duncan',
      author_email='shaun.duncan@coxinc.com',
      url='http://www.github.com/coxmediagroup/django-monocle/',
      download_url='https://github.com/coxmediagroup/django-monocle/downloads',
      license='BSD',
      packages=find_packages(),
      install_requires=['celery']
      )
