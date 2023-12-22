from setuptools import setup, find_packages


setup(
    name='tech_sage',
    version='1.0.0',
    description='Address Book, Notebook, Sorter',
    url='https://github.com/Grigory-Yunusov/Tech_Sage',
    author=['Andrey Samoylenko','Grigory Yunusov','Gulyaeva Kristina','Ievgen Sharnin','Kostiantyn Kosorotov'],
    author_email='',
    license='as authors',
    install_requires=[
        'prompt_toolkit',
        'rich',
        ],
    classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
],
    packages=find_packages(),
    entry_points={'console_scripts': ['tech_sage=tech_sage.main:main']} 
)
