# For more information, please refer to https://aka.ms/vscode-docker-python
#FROM python:3-slim

# Keeps Python from generating .pyc files in the container
#ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
#ENV PYTHONUNBUFFERED=1

# Install pip requirements
#COPY requirements.txt .
#RUN python -m pip install -r requirements.txt

#WORKDIR /app
#COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
#RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
#USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#CMD ["python", "app.py"]


# Utiliser une image Python officielle
FROM python:3.9

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY app.py .
COPY templates/ templates/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port 5000
EXPOSE 5000

# Commande pour exécuter l’application
CMD ["python", "app.py", "gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]