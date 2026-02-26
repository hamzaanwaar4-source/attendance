### 1. Clone & Setup Virtual Environment

```bash
git clone <repo-url>
cd AttendoX
python -m venv venv
```

#### Activate (Windows PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

#### Activate (Linux/Mac):
```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example env file and update values:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=attendox_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4. Create the PostgreSQL Database

```sql
CREATE DATABASE attendox_db;
```

### 5. Run Migrations

```bash
python manage.py makemigrations accounts
python manage.py makemigrations employees
python manage.py makemigrations attendance
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run the Server

```bash
python manage.py runserver
```

The API is available at `http://localhost:8000/api/v1/`
