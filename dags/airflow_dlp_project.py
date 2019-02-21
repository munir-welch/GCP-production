import datetime
import os
from airflow.models import Variable
from airflow.contrib.operators import gcs_to_bq, bigquery_operator, gcs_download_operator, file_to_gcs, gcs_to_gcs, gcs_list_operator
from airflow.contrib.sensors import gcs_sensor
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.bash_operator import BashOperator
from extra_packages.dlp_branching import inspect_file, master_file_reader, data_clean, get_acl
from airflow import DAG
from google.cloud import storage 
from pathlib import Path




#-------------------------------------------------------------------------------------------------------------------------------------#
#------- Setting variables containing the master bucket and download master config file  
#-------------------------------------------------------------------------------------------------------------------------------------#
storage_client = storage.Client(project=Variable.get('Gcp_project_id'))

gcp_bucket = storage_client.get_bucket(Variable.get('bucket'))

masterConfig_file = gcp_bucket.get_blob('masterConfig.csv')
# Downloading the config file locally to ~/path/to/airflow/master
masterConfig_file.download_to_filename('masterConfig.csv')

path = str(Path().absolute())+'/masterConfig.csv'

project = Variable.get('Gcp_project_id')
# The info types to search for in the content. Required for DLP API
info_types = [{'name': 'FIRST_NAME'}, {'name': 'LAST_NAME'}, {'name': 'LOCATION'}, {'name': 'US_STATE'}]


#--------------------------------------------------------------------------------------------------------------------------------------#
#-------- Creating defult DAG aruguments that will be passed to every task instance 
#--------------------------------------------------------------------------------------------------------------------------------------#

default_dag_args = {
    'start_date': datetime.datetime(2019, 1, 28),
    # To email on failure or retry set 'email' arg to your email and enable
    # emailing here.
    'email_on_failure': False,
    'email_on_retry': False,
    # If a task fails, retry it once after waiting at least 2 mins
    'retries': 1,
    'retry_delay': datetime.timedelta(minutes=2),
    'project_id': Variable.get('Gcp_project_id')
}


#---------------------------------------------------------------------------------------------------------------------------------------#
#-------- Creating DAG object and passing deafult args and build 'static' operators 
#---------------------------------------------------------------------------------------------------------------------------------------# 

dag = DAG('DLP_Airflow_project', default_args = default_dag_args, schedule_interval=None)


start_dag = DummyOperator(task_id='Manual_start', dag = dag)


end_dag = DummyOperator(task_id='Finsh', dag = dag)



# Reading in the master confid file so we can dynamically create operators/tasks for each dag run
master_file = master_file_reader(path)


for file in master_file:

	# Storing some variables that are specific to each file that will be passed to each operator/task
	filename = file['filename']
	bucket = file['gcs location']
	time = str(datetime.datetime.now())
	filepath = str(Path().absolute())+'/'+filename
	delete_command = 'cd /Users/munirwelch/Desktop/AirflowSpace/ | rm -rf '+filename


	#-----------------------------------------------------------------------------------------------------------------------------------#
	#-------- Data migration and cleaning section and build 'dynamic operators'
	#-----------------------------------------------------------------------------------------------------------------------------------#

	# Waits for the file to land in the bucket i.e. checks for the presence of the file
	file_landing = gcs_sensor.GoogleCloudStorageObjectSensor(task_id = 'sence_'+filename, bucket=bucket,
	 object='landing/'+filename, google_cloud_storage_conn_id = 'airflow_gcp_connection' , dag=dag)

	# Downloads the file locally (not ideal as this wont scale -  need to change to reach files directly from GCS bucket)
	download_file_local = gcs_download_operator.GoogleCloudStorageDownloadOperator(task_id='download_local_'+filename,
		bucket = bucket, object = 'landing/'+filename, filename=filepath, google_cloud_storage_conn_id = 'airflow_gcp_connection', dag=dag)

	# Calls clean file method to clean file using pandas (could replace this Dataflow or Spark for more heavy duty jobs that would scale)
	clean_file = PythonOperator(task_id='clean_file_'+filename, python_callable = data_clean,
	op_kwargs={'file':filename}, dag=dag)

	# Re-uploads the cleaned file to the same bucket with same name so as to override the old file
	upload_file = file_to_gcs.FileToGoogleCloudStorageOperator(task_id='upload_file_'+filename,
	 src=filepath, dst = 'landing/'+filename, bucket=bucket, google_cloud_storage_conn_id = 'airflow_gcp_connection', dag=dag)

	# Moves the file to the stage folder ready to be analysed by DLP
	move_to_stage = gcs_to_gcs.GoogleCloudStorageToGoogleCloudStorageOperator(task_id='move_to_stage_'+filename,
		source_bucket = bucket, source_object='landing/'+filename, destination_bucket=bucket, destination_object='stage/'+filename,
		move_object = True, google_cloud_storage_conn_id = 'airflow_gcp_connection', dag=dag)


	# Setting the task dependencies for first part of the DAG 
	start_dag >> file_landing >> download_file_local >> clean_file >> upload_file >> move_to_stage >> end_dag

	#-----------------------------------------------------------------------------------------------------------------------------------#
	#-------- Sensitive data checking
	#-----------------------------------------------------------------------------------------------------------------------------------#

	# Starting a new path for each file 
	start = DummyOperator(task_id = 'Start_data_screen_'+filename, dag = dag)

	# Ending the path for each file
	complete = DummyOperator(task_id = 'finished_'+filename, trigger_rule='one_success', dag = dag)

	# This operator calls calls inspect_file method which uses the DLP API to inpect the file and returns one of two paths 
	check_sensitive_data = BranchPythonOperator(task_id = 'checking_data_'+filename, python_callable = inspect_file,
		op_kwargs = {'project': project, 'filename': filename, 'info_types': info_types},  dag=dag)

	# Start of path if sensitive data was found
	sensitive_data_found = DummyOperator(task_id = 'sensitive_data_found_'+filename, dag = dag)

	# Start of path if no sensitve data was found
	no_sensitve_data_found = DummyOperator(task_id= 'no_sensitve_data_found_'+filename, dag = dag)

	# Moves sensitve data to a secure /sensitve folder 
	move_to_secure = gcs_to_gcs.GoogleCloudStorageToGoogleCloudStorageOperator(task_id = 'move_to_secure_'+filename,
		source_bucket = bucket, source_object='stage/'+filename, destination_bucket=bucket, destination_object='sensitive/'+filename,
			move_object = True, google_cloud_storage_conn_id = 'airflow_gcp_connection', dag=dag)

	# moves non-sensitive data to a /load folder to be loaded to a database.
	move_to_load = gcs_to_gcs.GoogleCloudStorageToGoogleCloudStorageOperator(task_id = 'move_to_load_'+filename,
		source_bucket = bucket, source_object='stage/'+filename, destination_bucket=bucket, destination_object='load/'+filename,
			move_object = True, google_cloud_storage_conn_id = 'airflow_gcp_connection', dag=dag)

	# This operator simply prints out the ACL of the file containing sensitive data but idea is to change the ACL for each object in /sensitive
	change_acl = PythonOperator(task_id = 'change_acl_'+filename, python_callable = get_acl, op_kwargs={'file':'sensitive/'+filename},
		dag=dag)

	# Deletes the file from ~/path/to/airflow/master
	delete_file_local = BashOperator(task_id='Deleteing_'+filename, bash_command = delete_command, dag=dag)


	# setting task dependencies for the second part of the DAG
	end_dag >> start >> check_sensitive_data
	check_sensitive_data >> sensitive_data_found >> move_to_secure >> change_acl >> complete
	check_sensitive_data >> no_sensitve_data_found >> move_to_load >> complete
	complete >> delete_file_local