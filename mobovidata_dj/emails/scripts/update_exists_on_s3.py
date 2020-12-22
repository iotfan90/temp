from mobovidata_dj.emails.models import CSVImport
def run():
    CSVImport.update_exists_on_s3()
