import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyezbeq",
    version="0.0.4",
    author="iloveicedgreentea2",
    description="A package to control ezbeq",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iloveicedgreentea/pyezbeq",
    packages=setuptools.find_packages(),
    package_data={"pyezbeq": ["py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
)
