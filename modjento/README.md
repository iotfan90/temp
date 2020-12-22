Loading the magento database locally
======
Prerequisites:
---------
  1. You’re on Mac OS X
  2. Homebrew:
  
        ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"  
  3. MariaDB:
    
        brew install mariadb

  4. Note and verify your root username/password for your local mariadb:
    
        mysql -u root -p
        Enter password:<enter blank password if you don’t know it>
        MariaDB [None]> select user();
        +----------------+
        | user()         |
        +----------------+
        | root@localhost |
        +----------------+
        1 row in set (0.01 sec)
        
Grab a dump file from mmg-slave
-------------------------------

   1. The dump files are located in /load_files:
        
        [mobovidata@mmg-slave load_files]$ ls -la
        total 2197336
        drwxrwxrwx. 2 mobovidata web-data       4096 Aug 10 21:08 .
        drwxr-x---. 5 mobovidata web-data       4096 Aug 10 22:04 ..
        -rw-r--r--. 1 mobovidata web-data 2250059207 Aug 10 22:11 20160710.mmg.sql.gz
   2. You will need to ssh to mmg-slave and see what load files are available as the dumps are deleted and refreshed regularly.  You will want to grab the latest ganglia dump file available. 
   3. You can download the database dump to your local machine using scp:   
        
        scp -i <path/to/private/key> <username>@mmg-slave:~/load_files/20160710.mmg.sql.gz ~/Documents/
   4. Create the database instances we will need for mobovida:
    
        mysql -u root -p
        MariaDB [None]> create database mmg ;
        MariaDB [None]> quit
   5. Now we will need to load the database into our local mariadb server.
        
        gunzip -c ~/Documents/20160710.mmg.sql.gz | mysql -u root -p mmg

        
         

    
    

