===================
sclbuilder
===================
Tool to plan order of packages building in Software Collections

Finds all dependancies of the  packages, prints order of building and makes visualization of the relations between them.

## Usage

    Usage: mybin.py [OPTIONS] [PACKAGES]...

    Options:
      -r REPO                 Repo to search dependancies of the Packages
                              (default: "rawhide-source")
      --visual / --no-visual  Enable / disable visualization of relations
                              between pacakges
      -h, --help              Show this message and exit.

