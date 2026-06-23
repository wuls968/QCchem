# QCchem Workflow Plugin Examples

This directory contains example Python packages for custom workflow steps. They
are not installed by default.

Install the echo demo in editable mode from the repository root:

```bash
python -m pip install -e examples/workflow_plugins/qcchem_workflow_echo_plugin
qcchem workflow plugins
qcchem workflow run -c examples/workflows/plugin_loop_workflow.yaml
```

Plugins register classes under the `qcchem.workflow_steps` entry point group.
Installed plugins are trusted local Python code, while QCchem still records
plugin metadata and applies workflow limits plus the existing runtime/hardware
confirmation gates.
