#!/bin/bash
set -e

echo "Starting UTrack Bootstrap"

# 1. Set variables
PROJECT_DIR="/home/ubuntu/utrack-backend"
REPO_URL="https://github.com/emreutkan/utrack-be"

# 2. Install system dependencies
echo "Installing system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip postgresql postgresql-contrib git libpq-dev python3-dev nginx

# 3. Clone repository
echo "Setting up project directory..."
if [ ! -d "$PROJECT_DIR" ]; then
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown ubuntu:ubuntu "$PROJECT_DIR"
    git clone "$REPO_URL" "$PROJECT_DIR"
else
    echo "Repository already exists, skipping clone..."
fi

cd "$PROJECT_DIR"

# 4. Create venv
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3.12 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt gunicorn psycopg2-binary

# 5. Handle Secrets (Creates the initial .env)
DB_NAME="${DB_NAME:-utrack_db}"
DB_USER="${DB_USER:-utrack_user}"
DB_PASSWORD="${DB_PASSWORD}"
SECRET_KEY="${SECRET_KEY}"
ALLOWED_HOSTS="${ALLOWED_HOSTS:-*}"

# Validate required secrets
if [ -z "$DB_PASSWORD" ] || [ -z "$SECRET_KEY" ]; then
    echo "ERROR: DB_PASSWORD and SECRET_KEY are required to bootstrap!"
    exit 1
fi

echo "Creating initial .env file..."
cat > .env <<EOF
SECRET_KEY=$SECRET_KEY
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
DEBUG=False
ALLOWED_HOSTS=$ALLOWED_HOSTS
EOF

# 6. Setup PostgreSQL database
echo "Setting up PostgreSQL database..."
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF
    echo "Database created!"
else
    echo "Database already exists!"
fi

# 7. Setup Gunicorn systemd service
echo "Setting up Gunicorn service..."
sudo tee /etc/systemd/system/utrack.service > /dev/null <<EOF
[Unit]
Description=UTrack Django application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=$PROJECT_DIR
# Use the .env file for environment variables
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/gunicorn \\
    --workers 3 \\
    --bind unix:$PROJECT_DIR/utrack.sock \\
    --timeout 120 \\
    utrack.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 8. Setup Nginx configuration
echo "Setting up Nginx..."
# Use EC2_HOST if provided, otherwise fallback to ALLOWED_HOSTS
NGINX_HOST="\${EC2_HOST:-$ALLOWED_HOSTS}"

sudo tee /etc/nginx/sites-available/utrack > /dev/null <<EOF
server {
    listen 80;
    server_name $NGINX_HOST;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
    }

    location /media/ {
        alias $PROJECT_DIR/media/;
    }

    location / {
        proxy_pass http://unix:$PROJECT_DIR/utrack.sock;
        
        # Explicit headers to prevent the 400 Bad Request error
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    client_max_body_size 100M;
}
EOF

# 9. Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/utrack /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 10. Set permissions
echo "Setting permissions..."
sudo chmod 755 /home/ubuntu
sudo chmod 755 "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/media"
sudo chown -R ubuntu:www-data "$PROJECT_DIR"
sudo chmod -R 775 "$PROJECT_DIR"