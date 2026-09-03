# Zabbix Template Export

The custom Docker template used by the Mini-SOAR lab is configured in the live Zabbix instance. An authentic export is not currently stored in this directory.

Do not reconstruct or generate an importable template from the trigger documentation. The live Zabbix configuration is the source of truth for item keys, discovery rules, preprocessing, macros, and trigger prototypes.

## Export Workflow

When the live template is ready to version:

1. Open the Zabbix template management page.
2. Select the custom Mini-SOAR Docker template.
3. Export it directly from Zabbix in YAML format.
4. Review the export for environment-specific identifiers or sensitive values.
5. Confirm that stopped containers remain included in discovery.
6. Save the unchanged, authentic export in this directory.
7. Validate it by importing it into a disposable Zabbix environment before relying on it for recovery.

A descriptive filename such as `docker-mini-soar.yaml` may be used, but the exported filename and content should remain traceable to the real Zabbix configuration.

## Expected Coverage

The live template used by this project provides or derives items for:

- container discovery;
- CPU and memory usage;
- running state;
- Docker health state;
- restart count;
- OOMKilled state.

Trigger behavior currently documented by the repository is in [../triggers.md](../triggers.md). This list is descriptive only and is not a substitute for a real template export.
