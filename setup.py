from setuptools import setup
import re

with open('requirements.txt') as f:
  requirements = f.read().splitlines()

with open('singyeong/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

with open('README.md') as f:
    readme = f.read()

extras_require = {
    "msgpack": [
        "msgpack"
    ],
    "ujson": [
        "ujson"
    ]
}

setup(name='singyeong.py',
      author='StartIT',
      url='https://github.com/StartITBot/singyeong.py',
      project_urls={
        "StartIT Bot": "https://startit.fun/",
        "Issue tracker": "https://github.com/StartITBot/singyeong.py/issues",
      },
      version=version,
      packages=['singyeong'],
      platforms=["any"],
      license='MIT',
      description='An asynchronous client for 신경.',
      long_description=readme,
      long_description_content_type="text/markdown",
      include_package_data=True,
      install_requires=requirements,
      extras_require=extras_require,
      python_requires='>=3.6',
      classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet",
        "Topic :: Utilities",
        "Topic :: System :: Networking",
        "Topic :: Software Development :: Libraries",
      ]
)
