from setuptools import setup

setup(
    name="mquery",
    version="0.1.0",
    description="CLI for reading and filtering your mBank history exports.",
    author="Piotr Wasilewski",
    author_email="piotrek@piotrek.io",
    url="https://github.com/piotrekio/mquery",
    license="MIT",
    python_requires=">=3.8",
    install_requires=["click>=7.0"],
    py_modules=["mquery"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Utilities",
    ],
    entry_points={"console_scripts": ["mquery=mquery:main"]},
)
