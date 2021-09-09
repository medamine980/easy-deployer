from setuptools import setup, find_packages

with open("README.md") as f:
    long_desc = f.read()

setup(
    name="simple_deployer",
    version="0.1.0",
    long_description=long_desc,
    long_description_content_type='text/markdown',
    author="Mohamed-Amine Benali",
    author_email="namelowy_64@hotmail.com",
    url="https://github.com/medamine980/simple-deployer",
    packages=find_packages("simple_deployer", exclude=["simple_deployer.dist"]),
    license="MIT",
    keywords=["python", "github", "github-deployer", "heroku", "heroku-deployer", "deploy"],
    install_required=["pipreqs"],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6'
    ],
    console_scripts={
        "github-deployer": "simple_deployer.github:main",
        "heroku-deployer": "simple_deployer.heroku:main"
    }
)