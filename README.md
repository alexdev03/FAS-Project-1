# FAS Project 1

Collects Linux system metrics and journal log snippets into CSV files under `data/`, optionally pushing them to a GitHub repository on a fixed interval.

## Requirements

- Linux (uses `/proc`, `journalctl`, GNU `df`)
- `bash`, `git`, `python3`
- On Debian/Ubuntu, if `python3 -m venv` fails, install the matching venv package (e.g. `python3-venv` or `python3.11-venv`)

## First-time setup

1. Copy `.env.example` to `.env` and set `GITHUB_TOKEN` (needed for the auto-push loop only). Create a token in GitHub: [Creating a fine-grained personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token).
2. Adjust `config.ini` (`repo`, `interval`, log `regex` / `lines` as needed).
3. Run the setup script with **bash** (not `sh`; Debian’s `/bin/sh` is `dash` and will error on `pipefail`):

   ```bash
   bash setup.sh
   ```

4. Optionally activate the virtualenv:

   ```bash
   source .venv/bin/activate
   ```

## Commands

| Goal | Command |
|------|---------|
| One collection cycle (metrics + errors CSV) | `make run` or `bash collect.sh` |
| Continuous loop + git push (uses `.env` and `config.ini`) | `make loop` or `bash autocommit.sh` |
| Remove generated CSVs and `__pycache__` | `make clean` |

### Run the loop in the background

**Detach with `nohup`:**

```bash
cd /path/to/FAS-Project-1
nohup bash autocommit.sh >> autocommit.log 2>&1 &
```

**Detach with GNU Screen** (install if needed: `apt install screen`):

1. Start a named session and run the loop:

   ```bash
   screen -S fas
   cd /path/to/FAS-Project-1
   bash autocommit.sh
   ```

2. **Leave Screen but keep the process running:** press **Ctrl+A**, release, then press **D** (detach).
3. **Attach again** to that session:

   ```bash
   screen -r fas
   ```

If only one Screen session exists, `screen -r` is enough. List sessions with `screen -ls`.
