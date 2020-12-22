# Mobovidata

This repository holds the source code of the Mobovidata application made by Mobovida.


### Table of Contents

1. [Overview](#markdown-header-overview)
1. [Local environment setup](#markdown-header-local-environment-setup)
1. [Testing](#markdown-header-testing)
1. [Deploy](#markdown-header-deploy)
1. [Coding practices](#markdown-header-coding-practices)
1. [Contributors](#markdown-header-contributors)
1. [License](#markdown-header-license)


# Overview
**TODO - Kenny**

Quick introduction to project, project parts and functions.


# Local environment setup

1. Check out the code:

        :::bash
            $ git clone git@bitbucket.org:wirelessemporium/mobovidata.git mobovidata
            $ cd mobovidata/
        
    
2. Set up a [virtual environment](https://virtualenv.pypa.io/en/stable/):

        :::bash
            $ virtualenv .env

    **NOTE:** This creates a virtual environment in the .env dir in your project's directory, our default setup for mobovidata.


3. Activate the virtual env:

        :::bash
            $ source .env/bin/activate

    **NOTE:** Be sure to activate virtual environment before continue this tutorial.


4. Install requirements:
        
        :::bash
            $ pip install -r requirements/development.txt


5. Install MySQL/MariaDB, open mysql console, then run:
        
        :::sql
            CREATE DATABASE mobovidata;
            CREATE DATABASE mmg;
    
    **NOTE 1:** MySQL version >= 5.6.5
    
    **NOTE 2:** This will be used for Django's own tables and any models we add outside of Magento.
    (Adjust your connection settings for your local mysql as needed.)


6. Create a MySQL/MariaDB user named `django` and **grant privileges** on `mobovidata` and `mmg` databases:

        :::sql
            CREATE USER 'django'@'localhost' IDENTIFIED BY 'YOUR PASSWORD HERE';
            GRANT ALL PRIVILEGES ON mobovidata.* TO 'django'@'localhost';
            GRANT ALL PRIVILEGES ON mmg.* TO 'django'@'localhost';
            FLUSH PRIVILEGES;


7. Load **Magento** database dump into `mmg`. First ask contributors for a `magento database dump`.

        :::bash
            $ gunzip -c ~/dump_path/dump_name.mmg.sql.gz | mysql -u YOUR_MYSQL_USER_NAME -p mmg

    **NOTE:** For more details check the README in [modjento/README.md](modjento/README.md)

    **WARNING:** It'll take time to load the entire dump.
    
    
8. Create your local settings override, `config/settings/local.py`:
    
    You will find an example of local settings on `config/settings/local_settings_example.py`. 
    You **MUST** create your own `local.py` file using this template and replacing the fields with your own data.
    Additional settings will be added to your `local.py` as needed.

    
9. Check out the `dev` branch:
    
        :::bash
            $ git checkout -t origin/dev
    
    **NOTE:** All future work should be based off and pull requested to the `dev` branch.


10. Make Django migrations:
    
        :::bash
            $ python manage.py makemigrations
            $ python manage.py migrate
    

11. Run server
        
        :::bash
            $ cd mobovidata
            $ python manage.py runserver
        
    The `python manage.py runserver` command runs the server and watch for file changes.
    
    Shut it down manually with `Ctrl-C`.
    

# Testing

Create your local settings override, `config/settings/test_settings_local.py`:
    
You will find an example of local settings on `config/settings/test_settings_local_example.py`. 
You **MUST** create your own `test_settings_local.py` file using this template and replacing the fields with your own data.
Additional settings will be added to your `test_settings_local.py` as needed.

    :::bash
        $ cd mobovidata
        $ python manage.py test

**TODO**


# Deploy
Run:
   
    :::bash
        $ fab deploy:target=TARGET,branch=BRANCH


**TODO**


# Coding practices
Before pushing your code you must ensure it successfully passed these rules:

* No dead code or commented code.
* No unused imports.
* No hard-coding data or magic numbers.
* Complex code must have comments.
* Methods must have Python docstring.
* Imports must be alphabetically sorted in the following order:
    1. Standard library imports
    2. Third party imports
    3. Application specific imports
    
        Example:
        
            :::python
                import a_standard
                import b_standard
                
                import a_third_party
                import b_third_party
                
                from a_soc import bar
                from a_soc import foo
                from a_soc.bar import barfoo
                from b_soc import d

* Using PEP8 python style guide.
* Readme file updated. 
* New Code follows the standard flow for handling exceptions.
* New Code follows the standard flow for logging.
* Write new test cases if applicable.
* Succeed Test run.
* Uses Django Framework facilities (ie: Forms).
* New files follows the standard project scaffolding.
* Readme files updated if applicable.


# Contributors
* Kenny Smithnanic


# License

Copyright (c) 2016, Kenny Smithnanic
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation and/or
  other materials provided with the distribution.

* Neither the name of mobovidata_www nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.
