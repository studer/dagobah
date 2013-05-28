Dagobah
=======

A simple dependency-based job scheduler written in Python.

## Installation

    pip install dagobah
    dagobahd  # start the web interface on localhost:9000

Dagobah does not require a backend, but unless you specify one, your jobs and tasks will be lost when the daemon exists. Each backend requires its own set of drivers. Once you've installed the drivers, you then need to specify any backend-specific options in the config. See "Configuration" below for details. The following backends are available:

#### SQLite

     pip install pysqlite sqlalchemy

#### MongoDB

    pip install pymongo

## Features

## Configuration

## Other Information

#### Known Issues

  * Retrying a failed job after renaming one of its tasks results in an error

#### Planned Features

  * Improved task detail pages
  * Advanced task-level configuration, e.g. timeouts
  * CLI

## Contributors

#### Author

 * [Travis Thieman](https://twitter.com/thieman)
