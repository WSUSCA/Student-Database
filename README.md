# Career Companion Portal (Pilot)

Flask-based, staff-only prototype for managing student career journeys.

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file (do **not** commit secrets) with at least:
   ```env
   SECRET_KEY=dev-change-me
   DATABASE_URL=sqlite:///career_companion.db
   NOTE_ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=changeme
   ```
3. Initialize the database and seed a dev admin:
   ```bash
   flask --app app.py init-db
   flask --app app.py create-admin
   ```
4. Run the app:
   ```bash
   flask --app app.py run
   ```

## Security Notes
- All sensitive notes are encrypted with Fernet using the `NOTE_ENCRYPTION_KEY` env var.
- Authentication uses bcrypt via `auth.py`; sessions expire after inactivity.
- Import/export tools only accept CSV/XLSX and are audited.
- Shocker Central integrations are stubbed for future secure API work.
