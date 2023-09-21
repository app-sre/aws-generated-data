# AWS Generated data

This repository holds data generated from AWS static HTML resources.

The output of these functions are structured files, easily consumable by automations.

## Usage

```bash
$ export AGD_RDS_EOL_ENGINES="postgres:https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-release-calendar.html mysql:https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.Concepts.VersionMgmt.html"
$ make ci-run
```

## Plugins

### AWS RDS

Parses the AWS RDS release calendar and outputs a YAML file with the following structure ([rds_eol.yaml](/output/rds_eol.yaml))

```yaml
---
- engine: <RDS-engine-name>
  eol: <EOL-YEAR-MONTH-DAY>
  version: <RDS-engine-version>
...
```
Feel free to add items to the list manually, if you know of any EOL dates. Entries older than 1 year are automatically removed.

## License

This project is licensed under the terms of the MIT license.
