import configparser
import os
import subprocess
import zipfile
import sys


def load_config(config_file):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)
    return config["DEFAULT"]


def extract_zip(zip_file, extract_to):
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    extracted_files = os.listdir(extract_to)
    if not extracted_files:
        raise FileNotFoundError(f"No files found in the extracted zip at {extract_to}")
    return os.path.join(extract_to, extracted_files[0])


def run_mysql_command(host, port, username, password, command):
    full_command = (
        f'mysql -h {host} -P {port} -u {username} -p{password} -e "{command}"'
    )
    print(f"Running MySQL command: {full_command}")
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running MySQL command: {result.stderr}")
        return False
    return True


def replace_schema(config_file, zip_file):
    config = load_config(config_file)

    docker_host = config["DOCKER_HOST"]
    docker_port = config["DOCKER_PORT"]
    db_name = config["DB_NAME"]
    db_username = config["DB_USERNAME"]
    db_password = config["DB_PASSWORD"]

    # Create a temporary directory to extract the zip file
    temp_dir = "temp_schema"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Extract the zip file
        dump_file = extract_zip(zip_file, temp_dir)
        print(f"Extracted dump file to {dump_file}")

        # Check if the database exists and drop it if it does
        check_db_command = f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'"
        drop_db_command = f"DROP DATABASE IF EXISTS {db_name}"
        create_db_command = f"CREATE DATABASE {db_name}"

        print(f"Checking if database '{db_name}' exists...")
        db_exists = run_mysql_command(
            docker_host, docker_port, db_username, db_password, check_db_command
        )

        if db_exists:
            print(f"Database '{db_name}' exists. Dropping it...")
            if not run_mysql_command(
                docker_host, docker_port, db_username, db_password, drop_db_command
            ):
                print(f"Failed to drop database '{db_name}'.")
                return 1

        # Create the database
        print(f"Creating database '{db_name}'...")
        if not run_mysql_command(
            docker_host, docker_port, db_username, db_password, create_db_command
        ):
            print(f"Failed to create database '{db_name}'.")
            return 1

        # Replace the schema
        print(
            f"Replacing schema in database '{db_name}' on {docker_host}:{docker_port}..."
        )
        import_command = f"cat {dump_file} | mysql -h {docker_host} -P {docker_port} -u {db_username} -p{db_password} {db_name}"
        result = subprocess.run(
            import_command, shell=True, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error importing schema: {result.stderr}")
            return 1

        print("Schema replacement completed successfully.")

    finally:
        # Clean up temporary directory
        print("Cleaning up temporary directory...")
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(temp_dir)
        print("Cleanup completed.")

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python replace_schema.py <config_file> <zip_file>")
        sys.exit(1)

    config_file = sys.argv[1]
    zip_file = sys.argv[2]
    exit_code = replace_schema(config_file, zip_file)
    sys.exit(exit_code)
