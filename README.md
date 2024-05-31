# db-utils

A simple utility package for backing up and restoring MySQL databases. This package is designed for personal use and includes scripts for creating database backups from a remote server and restoring them locally, making it easy to copy production databases to your local development environment.

## Features

- Backup MySQL database tables with and without data from a remote server
- Compress backups into zip files
- Restore and replace MySQL database schemas from backup zip files locally
- Option to skip data for specific tables and only backup their schema

## Installation

Clone the repository:

```sh
git clone https://github.com/yourusername/db-utils.git
cd db-utils
```

## Usage

### Backup Database
The backup_database.py script creates a backup of a MySQL database on a remote server, compresses it into a zip file, and downloads it to a local directory.

#### Configuration
Create a configuration file with the following format:

```ini
[DEFAULT]
REMOTE_SERVER = your_remote_server
USERNAME = your_username
PRIVATE_KEY_PATH = /path/to/your/private/key
DB_NAME = your_database_name
DB_USERNAME = your_db_username
DB_PASS = your_db_password
LOCAL_BACKUP_DIRECTORY = /path/to/local/backup/directory
REMOTE_BACKUP_DIRECTORY = /path/to/remote/backup/directory
TABLES_TO_SKIP_DATA = table1
                     table2
```

The `TABLES_TO_SKIP_DATA` setting allows you to specify tables for which only the schema information should be backed up, without the data. This is useful for tables like log entries (e.g., telescope_entries in Laravel projects).

#### Run the Script

```sh
python backup_database.py <config_file>
```


### Replace Database Schema

The replace_schema.py script extracts a MySQL database backup from a zip file and replaces the schema in a specified database locally. This is useful for setting up a local development environment with a copy of the production database.

#### Configuration

Create a configuration file with the following format:

```ini
[DEFAULT]
DOCKER_HOST = your_docker_host
DOCKER_PORT = your_docker_port
DB_NAME = your_database_name
DB_USERNAME = your_db_username
DB_PASSWORD = your_db_password
```

#### Run the Script

```sh
python replace_schema.py <config_file> <zip_file>
```

The local database instance can be running within a Docker container. The scripts are intended for use with MySQL databases or compatible databases like MariaDB.