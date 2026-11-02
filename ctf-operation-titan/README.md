# Operation Titan CTF

Operation Titan is a local, isolated CTF with ten intentionally vulnerable
services, CTFd, MariaDB and Redis. The vulnerabilities are deliberately
limited to the challenge containers; do not expose these ports to the public
internet.

## Requirements

- Docker Desktop on Windows/macOS, or Docker Engine with Compose v2 on Linux.
- Python 3.9+ for the launcher (only the standard library is used).
- At least 4 GB of free memory.

## Start

From this directory:

```bash
python titan.py config
python titan.py up
```

Windows PowerShell:

```powershell
py .\titan.py config
py .\titan.py up
```

To run only the first challenge:

```powershell
py .\titan.py flag1
```

The first challenge runs in an nginx Docker container. Docker maps the
container's port 80 to the local-only host address `127.0.0.1:8001`, so open
`http://localhost:8001` in your browser. The archive and its hidden logs are
generated during the image build; they do not need to exist in the repository.

Check that it is ready with:

```powershell
docker compose ps flag1_git
```

The status should show `healthy`. If it does not start, inspect the build and
container output:

```powershell
py .\titan.py logs flag1_git
```

The legacy Linux/macOS wrapper also works:

```bash
chmod +x setup.sh
./setup.sh
```

CTFd auto-setup runs in the `ctfd_setup` one-shot container. Open
`http://localhost:8000` and log in with `admin` / `admin` after its logs report
that provisioning is complete.

## Challenge endpoints

| Challenge | URL |
|---|---|
| 01-10 | `http://localhost:8001` through `http://localhost:8010` |
| CTFd | `http://localhost:8000` |

Use `python titan.py status` and `python titan.py logs ctfd_setup` when
diagnosing startup.

## Optional VPN profile

OpenVPN is disabled by default because it needs host capabilities and an
initialized PKI. To include it:

```bash
python titan.py --vpn up
```

The VPN portal is then available at `http://localhost:5050`. For a public VPN
deployment, replace the local-only setup with a reviewed network configuration
and firewall rules.

## Stop and reset

```bash
python titan.py down
python titan.py reset
```

`reset` removes the MariaDB volume and requires explicit confirmation. Use it
when re-running CTFd setup from a clean state.
