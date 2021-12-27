# importing libraries
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

# app start
app = Flask(__name__)

# S3 bucket config
bucket = custombucket
region = customregion

# RDS config
db_conn = connections.Connection(
    host = customhost,
    port =3306,
    user = customuser,
    password = custompass,
    db = customdb
)
output = {}
table = 'employee'

# App routing starts here

# Home Page
@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')

## Add Employee Page
@app.route("/addemp", methods=['POST'])
def AddEmp():
    # the list of fields we want to insert in sql
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    email = request.form['email']
    emp_image_file = request.files['emp_image_file']
    
    # saving details in database
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    # cursor variable is created for creating the database connection
    cursor = db_conn.cursor()
    # if the form is being submitted without uploading the image it will give a prompt to 
    # select a file
    if emp_image_file.filename == "":
        return "Please select a file"

    try: 
        # insertion in sql
        cursor.execute(insert_sql,(emp_id, first_name, last_name, pri_skill, email))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        # a defined name to the image present in S3 is alloted
        emp_image_file_name_in_s3 = "emp-id-"+str(emp_id) + "_image_file.jpg"
        # boto3 SDK is used to push and fetch images to and from S3 through flask
        s3 = boto3.resource('s3')
        
        try:
            # Data insertion in MySQL RDS and image uploading to S3 taking place
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            # for avoiding null pointer exception the location is given
            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

            # Uploading to S3 completed metadta is saved in dynamodb...")

            try:
                dynamodb_client = boto3.client('dynamodb', region_name='ap-south-1')
                dynamodb_client.put_item(
                 TableName='employee_image_table', # table creating in dynamoDB
                    Item={
                     'empid': {
                          'N': emp_id      # primary key as number
                      },
                      'image_url': {
                            'S': object_url     # image URL as String
                        }
                    }
                )

            except Exception as e:
                return str(e)
        
        except Exception as e:
            return str(e)

    finally:
        cursor.close()      #the DB cursor is being closed

    # all the process of data insertion is done
    return render_template('AddEmpOutput.html', name=emp_name)

## Get Employee Page
@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("GetEmp.html")

## Fetch Employee Page
@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    emp_id = request.form['emp_id']

    output = {}
    # fetching the data through the table using the primary key which is employee id
    select_sql = "SELECT emp_id, first_name, last_name, pri_skill, email from employee where emp_id=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql,(emp_id))
        result = cursor.fetchone()

        # the order of displaying the result
        output["emp_id"] = result[0]
        output["first_name"] = result[1]
        output["last_name"] = result[2]
        output["primary_skills"] = result[3]
        output["email"] = result[4]

        # again using boto3 to fetch the data from dynamo db
        dynamodb_client = boto3.client('dynamodb', region_name=customregion)
        try:
            response = dynamodb_client.get_item(
                TableName='employee_image_table',
                Key={
                    'empid': {
                        'N': str(emp_id)
                    }
                }
            )
            image_url = response['Item']['image_url']['S']

        except Exception as e:
            program_msg = "Flask could not update DynamoDB table with S3 object URL"
            return program_msg

    # if fetching the wrong employee id which is not in database this will show
    except Exception as e:
        return "<h1> Employee not Registered </h1>"

    finally:
        cursor.close()

    # display of final output page
    return render_template("GetEmpOutput.html", id=output["emp_id"], fname=output["first_name"],
                           lname=output["last_name"], interest=output["primary_skills"], email=output["email"],
                           image_url=image_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)
