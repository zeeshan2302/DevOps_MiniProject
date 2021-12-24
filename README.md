# DevOps_MiniProject
sudo apt-get update
# For Sql-client
sudo apt-get install mysql-client

# For python and related frameworks

sudo apt-get install python3
sudo apt-get install python3-flask
sudo apt-get install python3-pymysql
sudo apt-get install python3-boto3

# for running application
sudo python3 EmpApp.py

# for connecting to MYSQL
mysql --host [RDS endpoint] -u [username] -p 
<enterpassword>

# connect to DB
use [db name];

# Creating table
create table employee(
emp_id varchar(20),
first_name varchar(20),
last_name varchar(20),
pri_skill varchar(20),
email varchar(40));

# Type exit to go out of this terminal.

# common error:(port Already in use) then stop server.
sudo fuser -k [port name]/tcp
