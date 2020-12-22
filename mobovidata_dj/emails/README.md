Big Data Email Utils
===================
Author: Lee Bailey, l@lwb.co 8/8/2016

Explanation
-------------

Standard Django models for storing tons of send/open email data in the mobovidata project.

> **Note:**

> - In the interest of compatibility and ease-of-use, this has all been implemented as simple Django model with nothing special
> - We use an external data warehousing solution from http://crate.io and the django-crate adapter from http://github.com/linked/django-crate
> - Crate is mostly* fully django- and sql-compatible, but we have to be careful using JOINS -- LEFT OUTER is not supported, and therefore various aggregations (including django's model.manager.count() method) are sensitive to the orders that joins were performed.
> - It is therefore suggested that for models using the django-crate driver, ForeignKey fields are avoided in favor of CharFields to store model ID data.

#### <i class="icon-file"></i> Class Structure

- EmailBase -> 13 basic fields included on all Responsys Send Data types
| - EmailBrowserBase -> 4 additional fields (UserAgent, OS, Browser, BrowserType)
 - | - EmailOfferBase -> 4 additional fields (Offer name, number, category, url)
 -  All other models subclass these 3 base models

Email Administration
-------------------
Two relevant tasks govern the creation and import of send data; both have been defined as celery tasks and also as django manage.py commands

 - discover_send_data should be run once every time new data is received (6 hours?) to find the new CSV files
 - process_send_data should be run one-or-more-times whenever new data is discovered; this process is fairly thread safe and can be run multiple times concurrently for speed. A single thread on a Dell XPS 8900 dev machine can process 1 million records in about 20 minutes.

Crate Administration
-------------------

Django's built-in Migrate command will only migrate one database at a time. django-crate supports basic CREATE TABLE and DROP TABLE, but not ADD COLUMN, DROP COLUMN, ALTER TABLE. 
> **Note:**

> - To start/stop/run the crate server, you can use the included docker-compose.yml
> - cd provision/crate_setup; docker-compose -up -d
> - Navigate to http://localhost:4200/_plugin/crate-admin/#/ to verify that it works
> - To run the CREATE TABLE command, use "python manage.py migrate emails --database=crate"
> - You should see the tables at http://localhost:4200/_plugin/crate-admin/#/tables
> - It is suggested that you don't use django migrations, and instead delete the migrations folder and recreate it every time there are major changes.
> - The django-crate adapter will also fail to create any fields typed as ForeignKey; you must manually connect to crate and issue a query like "add column my_table (user_id string)".
> - For incremental backups, first setup a repository by running
> "CREATE REPOSITORY backup TYPE fs WITH (location='backup_path', compress=true);"
> - Then run backups using the following command
> CREATE SNAPSHOT backup.snapshot1 ALL WITH (wait_for_completion=true, ignore_unavailable=true);
> - See https://crate.io/docs/reference/sql/snapshot_restore.html
> - Crate has an admin interface that is very useful for exploring data at http://your_crate_ip:4200/admin/
> - At the end of the day, it is important to remember that crate is essentially ElasticSearch, and so some ES admin plugins will be compatible, ES partitioning and sharding advice is relevant, and scaling is simple (just add a new node) just like ES.

