# Installing Airflow on GCP

## Architecture
<p align="center">

<img src="/common/scripts/airflow-setup/images/Apache_Airflow_architecture_diagram.png" alt="Airflow Architecture"  />
</p>

<p align="center">

<img src="/common/scripts/airflow-setup/images/Apache_Airflow_architecture_diagram2.png" alt="Airflow Architecture" width="500" />
</p>

**OS**: `CentOS 7`

**Sample VM**:

Below is the code to create a VM using `gcloud` with `n1-standard-1` machine type (`1 vCPU, 3.75 GB memory`):
    
```bash
gcloud compute instances create instance-1 \
    --boot-disk-size 10GB \
    --image-family centos-7 --image-project centos-cloud \
    --machine-type n1-standard-1 \
    --zone=europe-west2-a     
```    

## Create Airflow user:

Before you run the steps below you need to create a new linux user `airflow` and add it to the sudo group. Run all the below steps as airflow user.

1. Log in to your server as the `root` user.
2. Use the `adduser` command to add a new user to your system.

    ```bash
    adduser airflow
    ```

    Use the `passwd` command to update the password for the `airflow` user if you want. If not you can just press enter to have no password.

    ```bash
    passwd airflow
    ```

3. Use the `usermod` command to add the user to the `wheel` group.

    ```bash
    usermod -aG wheel airflow
    ``` 

By default, on CentOS, members of the wheel group have sudo privileges.

4. Test sudo access on new user account

* Use the `su` command to switch to the `airflow` account.

    ```bash
    su - airflow
    ```

* For example, you can list the contents of the `/root` directory, which is normally only accessible to the root user.
    
    ```bash
    sudo ls -la /root
    ```

### Steps:

Follow the steps below to install `apache-airflow` on a Google Compute Engine (GCE) VM installed with `CentOS`:

1.  Update `yum` package manager and install the development tools for CentOS:
    
    ```bash
    sudo yum -y update
    sudo yum install -y wget git
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel
    ```
    
2. Install Python `pip` package management system, Python header files (`python-devel`) to build Python extensions & Mysql and upgrade python setup tools.

    ```bash
    sudo yum -y install python-pip python-wheel python-devel 
    sudo yum -y install mysql-devel mysql mysqlclient
    sudo pip install --upgrade pip
    sudo pip install --upgrade setuptools
    ```

3. Now there are 3 options to install apache-airflow:
    
    * Using the in-built Python distribution:

        In this case you just have to directly install `apache-airflow` using `pip`.

    * Using Python Virtual environment:
        
        In this case you will have to create install `virtualenv` and create a new directory and activate the virtual environment. Once you activate the virtual environment you can then install `apache-airflow` using `pip`.
        
        ```bash
        sudo pip install virtualenv
        mkdir -p ~/airflow_python
        virtualenv ~/airflow_python/
        source ~/airflow_python/bin/activate
        ```
        
    * Using a separate distribution of Python (download another Python distribution)
        
        ```bash        
        # Variables
        python27_version=2.7.14
        build_dir=python_build_temp
        
        echo "Create temp directory to build python"
        mkdir $build_dir
        cd $build_dir
        
        echo "Download Python 2.7"
        wget http://python.org/ftp/python/$python27_version\/Python-$python27_version\.tar.xz
        tar xf Python-$python27_version\.tar.xz
        cd Python-$python27_version
        ./configure --prefix=/usr/local --enable-unicode=ucs4 --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
        echo "Build and install Python 2.7"
        make && sudo make altinstall
        
        cd ..
        
        wget https://bootstrap.pypa.io/get-pip.py
        echo "Install pip for Python 2.7"
        sudo /usr/local/bin/python2.7 get-pip.py
        
        echo "Install virtualenv for Python 2.7"
        sudo /usr/local/bin/pip2.7 install virtualenv
        
        echo "Clean up installation files"
        cd ..
        sudo rm -rf $build_dir
        ```
    
    Execute the following code after selecting one of the above python options:
    
    *Note*: We used `apache-airflow` version `1.9.0` as at the time of this project that was the most recent stable release available.
    
    ```bash
    sudo pip install apache-airflow
    sudo pip install apache-airflow[all]
    ```

    To install Airflow 1.9.0 run below commands:
    ```bash
    sudo pip install apache-airflow==1.9.0
    sudo pip install apache-airflow[all]==1.9.0
    ```
    
    Here, `apache-airflow[all]` installs all extensions for `apache-airflow` but if you don't require all extensions you can use below commands to just install specific packages:
    
    ```bash
    sudo pip install apache-airflow[devel]
    sudo pip install apache-airflow[mysql]
    sudo pip install apache-airflow[crypto]
    sudo pip install apache-airflow[gcp_api]
    sudo pip install apache-airflow[hdfs]
    sudo pip install apache-airflow[hive]
    sudo pip install google.cloud pandas-gbq
    sudo pip install configparser
    sudo pip install flask-bcrypt
    sudo pip install crypto cryptography
    sudo pip install pymysql 
    ```  
    
4. Export the airflow home variable to bash profile:
    
    ```bash
    export AIRFLOW_HOME=/home/airflow
    echo 'export AIRFLOW_HOME=/home/airflow' >> ~/.bash_profile
    sudo mkdir $AIRFLOW_HOME/dags
    sudo chmod 777 $AIRFLOW_HOME/dags 
    ```

5. You can then either use SQLite on local VM or a Cloud SQL (MySQL) as database backend. If you want to use SQLite then you can now initialise the database by running the following code in the shell. Once that is done you can then start the webserver. The webUI is now available at the port `8080`.
    
    ```bash
    # Run Airflow a first time to create the airflow.cfg configuration file and edit it.
    cd $AIRFLOW_HOME    
    airflow version    
    ``` 
    
    **Note**: You need to use static IP address for your VM as we would need to whitelist that IP address in MySQL (cloud SQL).
    
    Airflow uses a database to store the DAGs execution status and history. With the default configuration, a SQLite database is created on the file system of the GCE instance where Airflow is running. As we are on the GCP, we are going to use CloudSQL which will allow us to persist the database outside of the GCE instance running Airflow. Follow the below steps to create a cloud SQL instance and use it as a backend:
    
    * To setup the database, go to the CloudSQL console and create a new MySQL instance named airflow-db.
        
        ![Create MySQL instance](/common/scripts/airflow-setup/images/Apache_Airflow_1.png)
        
    * Once created (it takes a few minutes), go to the instance configuration and create a new database named airflow.
    
        ![Create new MySQL database](/common/scripts/airflow-setup/images/Apache_Airflow_2.png)
        
    * Finally, create a user account named airflow-user that will be used by Airflow.

        ![Create airflow user](/common/scripts/airflow-setup/images/Apache_Airflow_3.png)
        
    * Create a static external IP address for the VM running airflow if it is ephemeral [Follow instructions [here](https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address#promote_ephemeral_ip)]. Now whitelist this static ip address in cloud SQL instance [Follow instructions [here](https://cloud.google.com/sql/docs/mysql/configure-ip#add)].
    
    * Edit `airflow.cfg` file using `vim` on the VM to add the connection to Cloud SQL:
    
    **Terminal**:
    ```bash
    vim $AIRFLOW_HOME/airflow.cfg
    ```
    
    **Vim Editor**:
    ```bash
    # Update the following properties:
    executor = LocalExecutor
    sql_alchemy_conn = mysql://airflow-user:AIRFLOW_PASSWORD@CLOUD_SQL_IP:3306/airflow
    load_examples = False
    ```
    
    * Now initialise the metadata database:
    ```bash
    # Run Airflow again to initialize the metadata database.
    airflow initdb
 
    # start the web server, default port is 8080
    airflow webserver -p 8080
    ```
    
    Update `AIRFLOW_PASSWORD` with password for the airflow user defined in Cloud sql and replace `CLOUD_SQL_IP` with the IP address of the Cloud SQL instance. If you do not want to load sample airflow DAG's then set `load_examples` to `False`.
    
6. Password protect the web UI by setting up users as described [here](http://airflow.readthedocs.io/en/latest/security.html#password).
    
    * You should have installed `crypto` package so that the password are not stored as plain text and are instead hashed.
    
    * Edit the `airflow.cfg` file in your `$AIRFLOW_HOME` directory and add/modify the `webserver` section.
        
        ```bash
        [webserver]
        authenticate = True
        auth_backend = airflow.contrib.auth.backends.password_auth
        ```
    * When password auth is enabled, an initial user credential will need to be created before anyone can login. An initial user was not created in the migrations for this authenication backend to prevent default Airflow installations from attack. Creating a new user has to be done via a Python REPL on the same machine Airflow is installed.
        
        **Terminal**:
        ```bash
        # navigate to the airflow installation directory
        cd ~/airflow
        python
        ```
        
        **Python**:
        ```python
        import airflow
        from airflow import models, settings
        from airflow.contrib.auth.backends.password_auth import PasswordUser
        user = PasswordUser(models.User())
        user.username = 'new_user_name'
        user.email = 'new_user_email@example.com'
        user.password = 'set_the_password'
        session = settings.Session()
        session.add(user)
        session.commit()
        session.close()
        exit()
        ```
        
### Integration with `systemd`

Integrating Airflow with `systemd` files makes watching your daemons easy as `systemd` can take care of restarting a daemon on failure. This also enables to automatically start airflow webserver and scheduler on system start.

1. Edit the `airflow` file from `systemd` folder as per the current configuration to set the environment variables for `AIRFLOW_CONFIG`, `AIRFLOW_HOME` & `SCHEDULER`. Alternatively you can download the files from [here](https://github.com/apache/incubator-airflow/tree/master/scripts/systemd). Copy the `airflow` file to `/etc/sysconfig/airflow`.

2. Copy the services files (the files with `.service` extension) to `/usr/lib/systemd/system` in the VM.

3. Copy the `airflow.conf` file to `/etc/tmpfiles.d/` or `/usr/lib/tmpfiles.d/`. Copying `airflow.conf` ensures `/run/airflow` is created with the right owner and permissions (0755 airflow airflow).

4. Enable this services by issuing `systemctl enable <service>` on command line as shown below.

    ```bash
    sudo systemctl enable airflow-webserver
    sudo systemctl enable airflow-scheduler
 
    # Enable the below services if running on an airflow cluster using Celert Executor
    #sudo systemctl enable airflow-worker
    #sudo systemctl enable airflow-flower
    #sudo systemctl enable airflow-kerberos
    ```

5. Now you can use `sudo systemctl start airflow <service>` to start the respective service.
    
    **Start**:
    ```bash
    sudo systemctl start airflow-webserver
    sudo systemctl start airflow-scheduler
    ```  
    
     **Stop**:
    ```bash
    sudo systemctl stop airflow-webserver
    sudo systemctl stop airflow-scheduler
    ``` 
    
     **Restart**:
    ```bash
    sudo systemctl restart airflow-webserver
    sudo systemctl restart airflow-scheduler
    ``` 

**Note**: Run all airflow DAGs by switching first to `airflow` user using `sudo su airflow`.

### Setting up SMTP Server for Airflow Email alerts using Gmail

Create an email id from which you want to send alerts about DAG failure or if you want to use EmailOperator. Edit `airflow.cfg` file to edit the smtp details for the mail server. 

For demo you can use any gmail account. 
*   Create a google `App Password` for your gmail account. [Instruction [here](https://support.google.com/accounts/answer/185833?hl=en)] This is done so that you don't use your original password or 2 Factor authentication.
    1.  Visit your [App passwords](https://security.google.com/settings/security/apppasswords) page. You may be asked to sign in to your Google Account.
    2.  At the bottom, click **Select app** and choose the app you’re using.
    3.  Click **Select device** and choose the device you’re using.
    4.  Select **Generate**.
    5.  Follow the instructions to enter the App password (the 16 character code in the yellow bar) on your device.
    6.  Select **Done**.
    
    Once you are finished, you won’t see that App password code again. However, you will see a list of apps and devices you’ve created App passwords for.

*   Edit `airflow.cfg` and edit the `[smtp]` section as shown below:
    
    ```bash
    [smtp]
    smtp_host = smtp.gmail.com
    smtp_starttls = True
    smtp_ssl = False
    smtp_user = YOUR_EMAIL_ADDRESS
    smtp_password = 16_DIGIT_APP_PASSWORD
    smtp_port = 587
    smtp_mail_from = YOUR_EMAIL_ADDRESS
    ```
    
    Edit the below parameters to the corresponding values:
    
    `YOUR_EMAIL_ADDRESS` = Your Gmail address   
    `16_DIGIT_APP_PASSWORD` = The App password generated above
    
    
### Setting up stackdriver logging on a VM
Setting up stackdriver logging is straightforward.
One has to install the agent (the process that will send the logs to the Cloud):
```bash
curl -O "https://repo.stackdriver.com/stack-install.sh"
sudo bash stack-install.sh --write-gcm
```
As the process might change, I add here the official page as reference: (https://cloud.google.com/monitoring/agent/install-agent).
After that you can easily verify that it works typing:
```bash
logging "EXAMPLE" 
```
and then checking on the stackdriver tab that the log has been written.

Logging can also be configured to work with the main languages such as Python/Java/JS. 

Here a simple example in Python:

```bash
pip install --upgrade google-cloud-logging
```

After that:

```python
# Imports the Google Cloud client library
from google.cloud import logging

# Instantiates a client
logging_client = logging.Client()

# The name of the log to write to
log_name = 'my-log'
# Selects the log to write to
logger = logging_client.logger(log_name)

# The data to log
text = 'Hello, world!'

# Writes the log entry
logger.log_text(text)

```

### Mounting Cloud Storage with `gcsfuse`
Now, we need to mount the `Cloud Storage` to the airflow VM. This is to keep DAGs and the **Master File** (containing the information of tables and partitions) in cloud storage.

#### Installing `gcsfuse`

The following instructions set up `yum` to see updates to gcsfuse, and work
for CentOS 7 and RHEL 7. 

1.  Configure the gcsfuse repo:
        
        sudo tee /etc/yum.repos.d/gcsfuse.repo > /dev/null <<EOF
        [gcsfuse]
        name=gcsfuse (packages.cloud.google.com)
        baseurl=https://packages.cloud.google.com/yum/repos/gcsfuse-el7-x86_64
        enabled=1
        gpgcheck=1
        repo_gpgcheck=1
        gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg
               https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
        EOF
        
2.  Make the system aware of the new repo:
    
        sudo yum update

    Be sure to answer "yes" to any questions about adding the GPG signing key.

3.  Install gcsfuse:

        sudo yum install gcsfuse

    Be sure to answer "yes" to any questions about adding the GPG signing key.

Future updates to gcsfuse will automatically show up when updating with `yum`.

#### Integrating it with `systemd`

To automatically mount a Cloud Storage bucket to a local directory follow the steps below:

1. Create a file named `gcs-fuse.service` in `/usr/lib/systemd/system` directory.
2. Copy the contents from [gcs.service](https://gist.github.com/craigafinch/292f98618f8eadc33e9633e6e3b54c05) and modify the `User` under service and the values in `ExecStart` parameter and paste in `/usr/lib/systemd/system/gcs-fuse.service`.
3. Enable the service using the below command:
    
    ```bash
    sudo systemctl enable gcs-fuse
    sudo systemctl start gcs-fuse  # This will mount the bucket
    ```

Alternatively, run the following command on terminal to avoid the 3 steps above:
    
```
sudo tee /usr/lib/systemd/system/gcs-fuse.service > /dev/null <<EOF
[Unit]
Description=Google Cloud Storage FUSE mounter
After=local-fs.target network-online.target google.service sys-fs-fuse-connections.mount
Before=shutdown.target

[Service]
Type=forking
User=airflow
ExecStart=/bin/gcsfuse --key-file /home/airflow/gcp_key/airflow_service_account.json et01-master-eu-0002 /home/airflow/framework_gcs
ExecStop=/bin/fusermount -u /home/airflow/framework_gcs
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

Enable the service using the command below:
```bash
sudo systemctl enable gcs-fuse
```

Mount the bucket:
```bash
sudo systemctl start gcs-fuse  
```

Unmount the bucket:
```bash
sudo systemctl stop gcs-fuse  
```
    
### Useful Links:

* [Airflow Docs: Configuration](http://airflow.readthedocs.io/en/latest/configuration.html)
* [Blog Post: Installing and using Apache Airflow on the Google Cloud Platform](https://lemag.sfeir.com/installing-and-using-apache-airflow-on-the-google-cloud-platform/)
* [Airflow Gitter Channel](https://gitter.im/apache/incubator-airflow)
* [Airflow Docs: Security - Authentication](http://airflow.readthedocs.io/en/latest/security.html#password)
* [Connecting MySQL Client from Compute Engine](https://cloud.google.com/sql/docs/mysql/connect-compute-engine)
* [Running airflow with auto-recovery using systemd](https://stackoverflow.com/questions/39073443/how-do-i-restart-airflow-webserver)
* [Airflow Docs: Integration with systemd](http://airflow.readthedocs.io/en/latest/configuration.html#integration-with-systemd)
* [GCSFuse: Documentation](https://github.com/GoogleCloudPlatform/gcsfuse/)
