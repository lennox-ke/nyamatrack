FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations and create superuser on startup
CMD sh -c "python manage.py migrate && \
           python create_superuser.py && \
           gunicorn nyamatrack.wsgi:application --bind 0.0.0.0:$PORT"