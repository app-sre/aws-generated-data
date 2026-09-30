# AWS Generated data

This repository holds data generated from AWS static HTML resources.

The output of these functions are structured files, easily consumable by automations.

## Pre-requisite 

- Install Python 
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Usage

```bash
$ export AGD_RDS_EOL_ENGINES='postgres:https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-release-calendar.html mysql:https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.Concepts.VersionMgmt.html aurora-postgresql:https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/aurorapostgresql-release-calendar.html' AGD_RDS_EOL_OUTPUT='rds_eol.yaml' AGD_MSK_RELEASE_CALENDAR_URL='https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html' AGD_MSK_EOL_OUTPUT='msk_eol.yaml' AGD_ELASTICACHE_RELEASE_CALENDAR_URL='https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html' AGD_ELASTICACHE_EOL_OUTPUT='elasticache_eol.yaml'

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

### AWS MSK

Parses the supported Apache Kafka versions table and outputs a YAML file with the following structure ([msk_eol.yaml](/output/msk_eol.yaml))

```yaml
---
- eol: <EOL-YEAR-MONTH-DAY>
  version: <Apache-Kafka-version>
...
```

`eol` is taken from the *End of support date* column; rows with no date yet (`--`) are
skipped. There is a single engine here, so unlike the RDS and ElastiCache plugins there is
no `engine` field. Versions keep any `-tiered` or `.x` suffix AWS uses (`2.8.2-tiered`,
`3.7.x`).

### AWS ElastiCache

Parses the AWS ElastiCache end of life schedule and outputs a YAML file with the following structure ([elasticache_eol.yaml](/output/elasticache_eol.yaml))

```yaml
---
- engine: <ElastiCache-engine-name>
  eol: <EOL-YEAR-MONTH-DAY>
  version: <ElastiCache-engine-major-version>
...
```

AWS publishes the schedule for the `redis` engine only; Valkey and Memcached versions are
listed on the same page but without any EOL dates. The dates are only given per major
engine version, so `version` holds a major version (`6`) rather than a minor one. `eol` is
the end of *standard* support, matching the RDS calendars - extended support may be
available for a premium after that date.

## License

This project is licensed under the terms of the MIT license.
