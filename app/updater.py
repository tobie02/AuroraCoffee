import requests
import os
import sys
import subprocess
import gdown

# URLs del servidor de actualizaciones en Google Drive
VERSION_FILE_ID = "18lvUlm3Et8sCnJHsGo19gcAciBd4uFqy"
INSTALLER_FILE_ID = "1WaXJeliya4Ld-XEMgj8jXnu3xV-_nb-v"

VERSION_URL = f"https://drive.google.com/uc?export=download&id={VERSION_FILE_ID}"
INSTALLER_URL = f"https://drive.google.com/uc?export=download&id={INSTALLER_FILE_ID}"

LOCAL_VERSION_FILE = "version.txt"
UPDATE_INSTALLER = "AuroraCoffee_setup.exe"

def get_local_version():
    try:
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"  # Si no se encuentra el archivo de versión local

def get_remote_version():
    response = requests.get(VERSION_URL)
    response.raise_for_status()
    return response.text.strip()

def download_update():
    gdown.download(INSTALLER_URL, UPDATE_INSTALLER, quiet=False)

def check_for_updates():
    local_version = get_local_version()
    remote_version = get_remote_version()

    if remote_version != local_version:
        print(f"Nueva versión disponible: {remote_version}")
        download_update()
        print("Actualización descargada. Ejecutando el instalador...")
        try:
            subprocess.Popen([UPDATE_INSTALLER, '/VERYSILENT', '/DIR=.', '/NORESTART'])
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar el instalador: {str(e)}")
            sys.exit(1)
        sys.exit(0)  # Salir de la aplicación actual para permitir la actualización

if __name__ == "__main__":
    check_for_updates()
