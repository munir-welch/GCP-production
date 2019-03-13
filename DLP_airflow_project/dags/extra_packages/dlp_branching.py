import google.cloud.dlp 
from google.cloud import storage
import mimetypes
import csv
import pandas as pd
from airflow.models import Variable

storage_client = storage.Client(project=Variable.get('Gcp_project_id'))

gcp_bucket = storage_client.get_bucket(Variable.get('bucket'))

#------------------------------------------------------------------------------------------------------------------------#
#-------------DLP service agent------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------#
def inspect_file(project, filename, info_types, min_likelihood=None, 
	custom_dictionaries=None, custom_regexes=None, 
	max_findings=None, include_quote=True, mime_type=None):


	# Instantiate a client.
	dlp = google.cloud.dlp.DlpServiceClient()

	# Convert the project id into a full resource id.
	parent = dlp.project_path(project)

	# The minimum likelihood to constitute a match. Optional.
	min_likelihood = 'LIKELY'

	# The maximum number of findings to report (0 = server maximum). Optional.
	max_findings = 0

	# Construct the configuration dictionary. Keys which are None may
	# optionally be omitted entirely.
	inspect_config = {
	    'info_types': info_types,
	    'min_likelihood': min_likelihood,
	    'include_quote': include_quote,
	    'limits': {'max_findings_per_request': max_findings},
	    }

	if mime_type is None:
		mime_guess = mimetypes.MimeTypes().guess_type(filename)
		mime_type = mime_guess[0]

	    # Select the content type index from the list of supported types.
	supported_content_types = {
	None: 0,  # "Unspecified"
	'image/jpeg': 1,
	'image/bmp': 2,
	'image/png': 3,
	'image/svg': 4,
	'text/plain': 5
	}
	content_type_index = supported_content_types.get(mime_type, 0)

	    # Construct the item, containing the file's byte data.
	with open(filename, mode='rb') as f:
		item = {'byte_item': {'type': content_type_index, 'data': f.read()}}
	#item = {'value': filename}
	# Call the API.
	response = dlp.inspect_content(parent, inspect_config, item)

    # Print out the results.
   
	FIRST_NAMES = []
	LAST_NAMES = []
	LOCATIONS = []
	US_STATES = []
	if response.result.findings:
		print('the total number of findings is: ', len(response.result.findings))
		for finding in response.result.findings:
			if finding.info_type.name == 'FIRST_NAME':
				FIRST_NAMES.append(finding.info_type.name)

			elif finding.info_type.name == 'LAST_NAME':
				LAST_NAMES.append(finding.info_type.name)

			elif finding.info_type.name == 'LOCATION':
				LOCATIONS.append(finding.info_type.name)
				
			elif finding.info_type.name == 'US_STATE':
				US_STATES.append(finding.info_type.name)

		if len(response.result.findings) >= 10:
			return 'sensitive_data_found_'+filename
		else: 
			return 'no_sensitve_data_found_'+filename

		print('TOTAL_FINDINGS = ', len(response.result.findings))
		print('FIRST_NAMES = ', len(FIRST_NAMES))
		print('LAST_NAMES = ', len(LAST_NAMES))
		print('LOCATIONS = ', len(LOCATIONS))
		print('US_STATES = ', len(US_STATES))
	else:
		print('No findings.')
		return 'no_sensitve_data_found_'+filename

#------------------------------------------------------------------------------------------------------------------------#
#-------------Read master config file operator---------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------#
def master_file_reader(object_file_path):

	list_of_records = []

	with open(object_file_path, 'r') as master:
		csv_reader = csv.reader(master)
		next(csv_reader)

		for line in csv_reader:
			full_record = {
			'filename' : line[0],
			'gcs location' : line[1],
			'destination dataset' : line[2],
			'destination_table' : line[3]
			}

			list_of_records.append(full_record)


	return (list_of_records)

#------------------------------------------------------------------------------------------------------------------------#
#-------------Clean data (arbitary)--------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------#
def data_clean(file):
	dirty_file = pd.read_csv(file)
	print('i read a file')
	x = dirty_file.isna().sum()
	if x.any() > 0:
		print('has nans')
		dirty_file.fillna('Null', inplace=True)
	else:
		print('clean file contains', x, 'Nans')

	clean_files = dirty_file.replace(0, 'Null')
	clean_files.to_csv(file, index=False)

#------------------------------------------------------------------------------------------------------------------------#
#-------------Get bucket ACL (to be extended)----------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------#

def get_acl(file):
	blob = gcp_bucket.get_blob(file)

	for entry in blob.acl:
		print('{}: {}'.format(entry['role'], entry['entity']))
