import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
import uuid
from fastapi import UploadFile

class UploadError(Exception):
    pass

#await upload_to_spaces(file_name, file_path, file_ext)
async def upload_to_spaces(new_file_name: str,  file_path: str , file_extension: str, upload_file: UploadFile):
    # Retrieve AWS credentials from environment variables
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    # Check if the credentials are available
    if not aws_access_key_id or not aws_secret_access_key:
        raise UploadError("AWS credentials not available in environment variables.")

    # Configure your DigitalOcean Spaces credentials and bucket
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name='nyc3',
                            endpoint_url='https://nyc3.digitaloceanspaces.com',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)

    try:
        # Generate a unique file name
        unique_file_name = f"{new_file_name}_{str(uuid.uuid4())}.{file_extension}"

        # Save the uploaded file to a temporary file
        with open(unique_file_name, "wb") as temp_file:
            temp_file.write(await upload_file.read())

        # Upload the file to DigitalOcean Spaces
        client.upload_file(unique_file_name, f"farabix-resources", f"{file_path}{new_file_name}.{file_extension}")

        # Remove the temporary file after uploading
        os.remove(unique_file_name)

        return f"https://farabix-resources.nyc3.digitaloceanspaces.com{file_path}{new_file_name}.{file_extension}"
    except (NoCredentialsError, ClientError) as e:
        raise UploadError(f"Error in uploading file to DigitalOcean Spaces: {e}")
