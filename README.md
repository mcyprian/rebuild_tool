===================
sclbuilder
===================
Tool to rebuild list of packages and Software collections.

Finds dependancies of the packages, creates directed graph of realations and analyse it.
Tool gets rebuild metadata: list of packages, source of packages (srpms), build system... 
from Rebuild file and builds them in the right order.

In case list of packages (scl) includes circular dependecies rebuild tool needs special files
called "recipes" to resolve them.

Usage: mybin.py [OPTIONS] REBUILD_FILE

    Options:
      --visual / --no-visual  Enable / disable visualization of relations between
                              pacakges
      --analyse               Analyse relations between packages and print
                              circular dependencies, disable execution of builds
      -h, --help              Show this message and exit.
    
## Rebuild file

All data about rebuild are specified in this file:
    
    **item**       |**Description**                       |**Available plugins** | **Required**
    ---------------|--------------------------------------|----------------------|--------------
    build_system   | system to execute builds             |  copr                |   YES
    packages_source| source of srpms                      |  dnf, koji           |   YES
    repo           | repository that will be used to get dependecies |           |   YES
    packages       | list of packages                     |                      |   YES
    recipes        | list of recipe files to resolve circular dependecies
     |NO
    metapackage    | metapackage of scl                   |                  |SCL_ONLY
    prefix         | prefix of scl                        |                  |SCL_ONLY


Example of Rebuild file:
```
build_system: copr
copr_project: python35-rebuild2
chroots: [fedora-rawhide-x86_64]

packages_source: koji

repo: rawhide-source
recipes: [/home/mcyprian/Codes/devel/sclbuilder/input_data/recipe1_py35.yml,
          /home/mcyprian/Codes/devel/sclbuilder/input_data/recipe2_py35.yml]

packages: [gdb,
           python3,
           python-setuptools,
           pyparsing,
           python-pip,
           python-wheel,
           python-docutils,
           python-coverage,
           python-six,
           python-markupsafe,
           python-jinja2,
           python-nose,
           python-pygments,
           python-sphinx,
           python-virtualenv,
           python-sqlalchemy]
```

## Builder plugins
### Copr

Before rebuild using Copr as build system install and configure copr-cli:
    
    http://miroslav.suchy.cz/blog/archives/2013/12/29/how_to_build_in_copr/

Rebuild file items specific for Copr build system:

    **item**       |**Description**                       |**Required**
    ---------------|--------------------------------------|-------------------
    copr_project   | copr project will be created if it doesn't exist  | YES
    chroots        | list of chroots                      | YES
    chroot_pkgs    | add packages to the minimal buildroot| NO

