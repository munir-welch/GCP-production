# install 
$ cd /path/to/my/airflow/workspace
$ virtualenv -p `which python3` venv
$ source venv/bin/activate
(venv) $ 

(venv) $ pip install apache-airflow


(venv) $ cd /path/to/my/airflow/workspace
(venv) $ mkdir airflow_home
(venv) $ export AIRFLOW_HOME=`pwd`/airflow_home

(venv) $ airflow initdb

Better to use systemd 
using & runs in background 

(venv) $ airflow webserver & airflow scheduler &

to kill run 

cat airflow_home/airflow-webserver.pid | xargs kill -9

to restart run 

airflow webserver -p 8080 -D True



postgres 

sudo -u myusername psql postgres
for sqllite database use 
sql_alchemy_conn = sqlite:////Users/munirwelch/Desktop/AirflowSpace/airflow_home/airflow.db
for postgresql use 
sql_alchemy_conn = db+postgresql://airflow:airflow@localhost:5432/airflow

sudo pip install pandas-gbq -U


Web server PID 71487  