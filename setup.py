
from setuptools import setup, find_packages

with open("README.md") as f:
    long_desc = f.read()

setup(
    name="easy_deployer",
    version="1.0.1",
    description="A package to simplify and quickly deploy your project/app/folders to the supported platforms.",
    long_description=long_desc,
    long_description_content_type='text/markdown',
    author="Mohamed-Amine Benali",
    author_email="benali.medamine2002@gmail.com",
    url="https://github.com/medamine980/easy-deployer",
    packages=find_packages(exclude=["easy_deployer.dist", "easy_deployer.ignore"]),
    license="MIT",
    keywords=["python", "github", "github-deployer", "heroku", 
    "heroku-deployer", "deploy", "easy", "easy-deployer", "simple", "simple-deployer"],
    install_requires=[
        'keyboard',
        'pipreqs',
        'Click',
        'InquirerPy'
    ],
    # install_required=["pipreqs"],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.11'
    ],
    entry_points = {
        'console_scripts': [
            'easy-deployer = easy_deployer.cli:cli',
        ]
    }
    # console_scripts={
    #     "easy-deployer-github": "easy_deployer.github:main",
    #     "easy-deployer-heroku": "easy_deployer.heroku:main",
    #     "easy-deployer": "easy_deployer.main:main"
    # }
)