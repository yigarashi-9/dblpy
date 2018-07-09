from setuptools import find_packages, setup

setup(name="dblpy",
      version="1.0.0",
      description="CLI tool to search dblp",
      author="Yuu Igarashi",
      author_email="yuu.igarashi.9@gmail.com",
      license="MIT",
      classifiers = [
          "Development Status :: 4 - Beta",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 3.6"
      ],
      keywords="dblp",
      packages=find_packages(),
      install_requires=[
          "lxml>=4.0.0",
          "PyPDF2>=1.26.0",
          "pyperclip>=1.6.2",
          "requests>=2.18.4"
      ],
      python_requires=">=3.6",
      entry_points={
        'console_scripts': [
            'dblpy = dblpy.__main__:main',
        ],
    },
)
