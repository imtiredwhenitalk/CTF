# VolynGas Service — CTF

A fictional gas service website with a deliberately vulnerable Jinja2 message-preview feature.

## Architecture

```text
volyngas-ctf/
├── app.py                # Flask routes, SQLite, preview challenge
├── templates/
│   ├── base.html         # Shared navigation/layout
│   ├── index.html        # Home and services
│   ├── request.html      # Create request
│   ├── status.html       # Request status
│   ├── preview.html      # Vulnerable template preview
│   └── admin.html        # PIN-protected staff area
├── static/style.css      # Responsive styling
├── requirements.txt
├── Dockerfile
└── compose.yaml
```

## Start

```bash
docker compose up --build
```

Open http://127.0.0.1:5000

Or install requirements and run `python app.py`.

## Organizer notes (spoilers)

- Vulnerability: Jinja2 SSTI in `/preview`.
- Test payload: `{{ 7*7 }}` gives `49`.
- Flag payload: `{{ ctf.flag }}`.
- The template environment intentionally exposes only a **mock CTF variable**. This is a beginner challenge, not an unrestricted code-execution exercise.
- For an event, change `CTF_FLAG`, `SECRET_KEY` and `ADMIN_PIN`; don't expose the service directly to the internet. Place behind an isolated event reverse proxy/network.
- The staff PIN is a demonstration feature, not a production authentication system.
- Use fictional names, phone numbers and addresses; this demo stores submitted requests in temporary SQLite.
