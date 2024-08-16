import configparser
from datetime import datetime
import os
from fabric import Connection


def load_config(config_file):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)
    return config["DEFAULT"]


def run_command(connection, command):
    result = connection.run(command, hide=True)
    return result.stdout, result.stderr


def main(config_file):
    config = load_config(config_file)

    remote_server = config["REMOTE_SERVER"]
    username = config["USERNAME"]
    private_key_path = config["PRIVATE_KEY_PATH"]
    db_name = config["DB_NAME"]
    db_username = config["DB_USERNAME"]
    db_host = config.get("DB_HOST", "localhost")
    db_port = config.get("DB_PORT", 3306)
    db_pass = config["DB_PASS"]
    local_backup_directory = config["LOCAL_BACKUP_DIRECTORY"]
    remote_backup_directory = config["REMOTE_BACKUP_DIRECTORY"]
    tables_to_skip_data = [
        table.strip() for table in config["TABLES_TO_SKIP_DATA"].strip().split("\n")
    ]

    current_date_time = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{current_date_time}_{db_name}"
    remote_file_path = os.path.join(remote_backup_directory, file_name)

    no_data_tables_args = " ".join(tables_to_skip_data)
    ignore_table_args = " ".join(
        [f"--ignore-table={db_name}.{table}" for table in tables_to_skip_data]
    )

    # Define the commands
    create_dumps_directory_if_not_exists = f"mkdir -p {remote_backup_directory}"
    no_data_command = f"mysqldump  -h {db_host} -P {db_port} -u {db_username} -p{db_pass} --opt --no-tablespaces --no-data --set-gtid-purged=OFF {db_name} {no_data_tables_args} > {remote_file_path}_no_data_tables_structure_only.sql"
    data_command = f"mysqldump  -h {db_host} -P {db_port} -u {db_username} -p{db_pass} --opt --no-tablespaces --set-gtid-purged=OFF {db_name} {ignore_table_args} > {remote_file_path}_data_tables.sql"
    merge_command = f"cat {remote_file_path}_no_data_tables_structure_only.sql {remote_file_path}_data_tables.sql > {remote_file_path}.sql"
    cleanup_command = f"rm {remote_file_path}_no_data_tables_structure_only.sql {remote_file_path}_data_tables.sql"
    zip_command = f"cd {remote_backup_directory} && zip {file_name}.zip {file_name}.sql && rm {file_name}.sql"

    # Establish the connection
    conn = Connection(
        host=remote_server,
        user=username,
        connect_kwargs={"key_filename": private_key_path},
    )

    try:
        print("Creating backup directory on remote server...")
        run_command(conn, create_dumps_directory_if_not_exists)

        print("Running backup for table structures without data on remote server...")
        try:
            run_command(conn, no_data_command)
        except Exception as e:
            print(f"Failed to dump table structures without data: {e}")
            print("Proceeding with data tables dump only...")

        print("Running backup for tables with data on remote server...")
        run_command(conn, data_command)

        print("Merging dump files...")
        run_command(conn, merge_command)

        print("Cleaning up temporary dump files...")
        run_command(conn, cleanup_command)

        print("Creating zip file for the backup...")
        run_command(conn, zip_command)

        print("Downloading backup file...")
        local_backup_path = os.path.join(local_backup_directory, f"{file_name}.zip")
        conn.get(
            os.path.join(remote_backup_directory, f"{file_name}.zip"),
            local=local_backup_path,
        )
        print(f"Backup completed and stored at {local_backup_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python backup_database.py <config_file>")
        sys.exit(1)
    config_file = sys.argv[1]
    main(config_file)
