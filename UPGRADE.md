# Upgrade

All instructions to upgrade this project from one release to the next will be documented in this file. Upgrades must be run sequentially, meaning you should not skip minor/major releases while upgrading (fix releases can be skipped).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### 3.x.x to 4.0.0

#### Upgrade history syntax

CLI syntax has been changed from `fetch` & `push` to `read` & `write` affecting the command history. You must replace the command history after updating:
- locate your history file path, which is in `{ RALPH_APP_DIR }/history.json` (defaults to `.ralph/history.json`)
- run the commands below to update history
```
$ sed -i 's/"fetch"/"read"/g' { my_history_file_path }
$ sed -i 's/"push"/"write"/g' { my_history_file_path }
```