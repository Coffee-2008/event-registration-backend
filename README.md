# Event Registration Backend

Backend for the **Celestius Backend Team recruitment task**.

**Event:** Backend Development Workshop · 20 October 2026 · 50 seats

Built with **Python + Flask + SQLite**. SQLite saves everything in one file (`registrations.db`), so there's nothing extra to install or set up.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Server starts at http://127.0.0.1:5000. The database file is created automatically.

Run the checks:

```bash
python test_app.py
```

## API

| Method | Route | What it does |
|--------|-------|--------------|
| POST | `/register` | Register a student |
| GET | `/registrations` | List all registrations (for organizers) |
| GET | `/registrations/<id>` | Get one registration by ID |
| GET | `/registrations/email/<email>` | Get one registration by email |
| GET | `/` | Event info and seats left |

### Register

```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Shreya", "email": "shreya@example.com", "college": "CIT - AI&DS"}'
```

`name` and `email` are required. `college` is optional. The registration time is added by the server.

### Responses

| Situation | Status | Message |
|-----------|--------|---------|
| Registered | 201 | "Registration successful" |
| Missing / bad name or email | 400 | "Invalid or missing information" + list of problems |
| Email already registered | 409 | "This email is already registered." |
| 50 / 50 seats filled | 409 | "Event is full" |
| ID or email not found | 404 | "Registration not found." |

## How it works (and why)

- **Capacity:** before saving, the app counts existing registrations. If it's 50 already, it says "Event is full".
- **Two people at the same time:** the check and the save happen inside one locked step (`BEGIN IMMEDIATE`), so two people can't both take seat 50.
- **Duplicates:** checked in code, and the database also has a `UNIQUE` rule on email as a safety net. Emails are lowercased, so `A@x.com` and `a@x.com` count as the same person.
- **Safe queries:** all database queries use `?` placeholders, which stops SQL injection.

## Files

- `app.py` – the whole backend
- `test_app.py` – checks for every case in the task
- `requirements.txt` – dependencies

## Note

I'm a first-semester student at CIT, and this is my first backend project. I used AI to help me build it, then ran and tested it myself (registering, viewing, duplicates, errors). I'm still learning how each part works, especially the database and capacity logic.
