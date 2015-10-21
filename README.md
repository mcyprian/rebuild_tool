===================
sclbuilder
===================
Tool to rebuild packages and Software collections.

Finds all dependancies of the  packages, prints order of building and makes visualization of the relations between them.

## Usage

    Usage: mybin.py [OPTIONS] [PACKAGES]...

    Options:
      -r REPO                 Repo to search dependancies of the Packages
                              (default: "rawhide-source")
      --visual / --no-visual  Enable / disable visualization of relations
                              between pacakges
      -h, --help              Show this message and exit.

## Configuration
Before rebuild using Copr as build system install and configure copr-cli:
    
    http://miroslav.suchy.cz/blog/archives/2013/12/29/how_to_build_in_copr/


