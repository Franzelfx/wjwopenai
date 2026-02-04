# WJW Analytics - Document Processing & Analysis Platform

Eine moderne Full-Stack-Anwendung zur Verarbeitung, Analyse und Verwaltung von Dokumenten mit OCR-Funktionalität und AI-gestützter Datenextraktion.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Angular](https://img.shields.io/badge/Angular-DD0031?style=flat&logo=angular&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)

## 📋 Inhaltsverzeichnis

- [Überblick](#überblick)
- [Features](#features)
- [Architektur](#architektur)
- [Technologie-Stack](#technologie-stack)
- [Installation](#installation)
- [Entwicklungsmodus](#entwicklungsmodus)
- [Projektstruktur](#projektstruktur)
- [API-Dokumentation](#api-dokumentation)
- [Deployment](#deployment)

## 🎯 Überblick

WJW Analytics ist eine leistungsstarke Plattform zur automatisierten Dokumentenverarbeitung. Die Anwendung ermöglicht es Benutzern:

- **Projekte zu erstellen und zu verwalten** mit individuellen Workflows
- **Dokumente hochzuladen** (einzelne Dateien oder komplette Ordnerstrukturen)
- **OCR-Verarbeitung** durchzuführen mit KI-gestützter Datenextraktion
- **Ergebnisse zu überprüfen und zu bearbeiten** in einer intuitiven Benutzeroberfläche
- **Daten zu exportieren** in verschiedenen Formaten (CSV, Excel, JSON)

## ✨ Features

### Projekt-Management
- ✅ Projekte erstellen, bearbeiten und löschen
- ✅ Übersichtliches Dashboard mit Projekt-Karten
- ✅ Zeitstempel-basierte Projektordner
- ✅ Empty State mit Onboarding für neue Benutzer

### Datei-Verwaltung
- 📁 Ordner-Upload mit Struktur-Erhaltung
- 📄 Einzeldatei-Upload
- 🗑️ Datei- und Ordner-Löschung
- 🌳 Tree-View Darstellung der Ordnerstruktur
- 🔍 Suchfunktion für Dateien

### OCR & Verarbeitung
- 🤖 AI-gestützte Dokumentenanalyse mit OpenAI
- ⏯️ Start/Pause/Stop-Steuerung der Verarbeitung
- 📊 Echtzeit-Progress-Tracking
- 🎯 Custom Prompts für spezifische Extraktionsanforderungen
- 📈 Trennung von erfolgreichen und fehlgeschlagenen Verarbeitungen

### Ergebnis-Bearbeitung
- ✏️ JSON-Editor für Ergebnis-Anpassungen
- 👁️ Vorschau der verarbeiteten Daten
- 💾 Speicherung von Änderungen
- 📥 Export als CSV oder Excel
- 🎨 Syntax-Highlighting für JSON

### Vektor-Datenbank
- 🔢 ChromaDB-Integration für semantische Suche
- 📚 Embedding-basierte Dokumentensuche
- 🧠 AI-gestützte Ähnlichkeitssuche

## 🏗️ Architektur

```
┌─────────────────┐      HTTP/REST       ┌──────────────────┐
│                 │ ◄──────────────────► │                  │
│  Angular SPA    │                      │  FastAPI Backend │
│  (Port 4200)    │                      │   (Port 6006)    │
│                 │                      │                  │
└─────────────────┘                      └──────────────────┘
                                                  │
                                                  │
                     ┌────────────────────────────┼────────────────────────┐
                     │                            │                        │
                     ▼                            ▼                        ▼
              ┌─────────────┐            ┌──────────────┐        ┌──────────────┐
              │   SQLite    │            │  File System │        │  ChromaDB    │
              │  Database   │            │   (Projects) │        │ Vector Store │
              └─────────────┘            └──────────────┘        └──────────────┘
```

### Komponenten

#### Frontend (Angular 16)
- **Dashboard**: Projekt-Übersicht und -Verwaltung
- **Processing**: Upload, Verarbeitung und Ergebnis-Bearbeitung
- **Services**: Backend-Kommunikation via HTTP
- **Material Design**: Moderne UI-Komponenten

#### Backend (FastAPI)
- **Routers**: API-Endpunkte für Dashboard und Processing
- **Services**: Business-Logik und CRUD-Operationen
- **Models**: SQLAlchemy ORM-Modelle
- **Schemas**: Pydantic Validierung
- **Tools**: Hilfsfunktionen für Geodaten, XML-Parsing, etc.

## 💻 Technologie-Stack

### Frontend
- **Framework**: Angular 16
- **UI Library**: Angular Material
- **Styling**: CSS3 mit Gradient-Designs
- **State Management**: RxJS
- **HTTP Client**: Angular HttpClient
- **File Handling**: file-saver

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: SQLite (Development/Production ready)
- **Vector DB**: ChromaDB 0.5.13
- **AI/ML**: 
  - OpenAI API Integration
  - LangChain
  - FAISS für Vektorsuche
- **Data Processing**:
  - pandas
  - openpyxl (Excel)
  - Pillow (Bildverarbeitung)
- **Validation**: Pydantic

### DevOps
- **Containerization**: Docker & Docker Compose
- **Python Version**: 3.10
- **Node Version**: 18
- **Web Server**: 
  - Uvicorn (Backend)
  - Nginx (Frontend Production)

## 🚀 Installation

### Voraussetzungen

- Docker & Docker Compose
- Git

### Quick Start

1. **Repository klonen**
```bash
git clone <repository-url>
cd wjwopenai
```

2. **Umgebungsvariablen konfigurieren**
```bash
cp .env.example .env
# Bearbeiten Sie .env und fügen Sie Ihre API-Keys hinzu
```

Benötigte Umgebungsvariablen:
```env
ENV=DEV
OPENAI_API_KEY=your_openai_api_key_here
# Weitere Konfigurationen nach Bedarf
```

3. **Docker Container starten**
```bash
docker compose up --build
```

4. **Anwendung aufrufen**
- Frontend: http://localhost:4200
- Backend API: http://localhost:6006
- API Dokumentation: http://localhost:6006/docs

## 🛠️ Entwicklungsmodus

Die Anwendung ist für Hot-Reloading im Entwicklungsmodus konfiguriert.

### Backend (mit Auto-Reload)
```bash
# Container läuft automatisch mit --reload Flag
docker compose up backend
```

Das Backend erkennt automatisch Änderungen in Python-Dateien und lädt die Anwendung neu.

### Frontend (mit Hot-Reloading)
```bash
# Container läuft mit ng serve
docker compose up frontend
```

Angular erkennt Änderungen und aktualisiert die Anwendung im Browser.

### Lokale Entwicklung (ohne Docker)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
ng serve --host 0.0.0.0 --port 4200
```

## 📁 Projektstruktur

```
wjwopenai/
├── backend/
│   ├── main.py                 # FastAPI Hauptanwendung
│   ├── db.py                   # Datenbank-Konfiguration
│   ├── requirements.txt        # Python-Dependencies
│   ├── Dockerfile              # Backend Container-Config
│   ├── models/                 # SQLAlchemy Modelle
│   │   ├── dashboard.py        # Projekt-Modell
│   │   └── processing.py       # Processing-Status-Modell
│   ├── routers/                # API-Endpunkte
│   │   ├── dashboard.py        # Projekt-Management APIs
│   │   └── processing.py       # OCR/Processing APIs
│   ├── schemas/                # Pydantic Schemas
│   │   ├── dashboard.py        # Projekt-Schemas
│   │   └── processing.py       # Processing-Schemas
│   ├── services/               # Business-Logik
│   │   ├── dashboard_crud.py   # Projekt-CRUD
│   │   ├── processing_crud.py  # Processing-Logik
│   │   ├── engine.py           # OCR-Engine
│   │   └── validator.py        # Daten-Validierung
│   ├── tools/                  # Hilfsfunktionen
│   │   ├── geodata.py          # Geo-Datenverarbeitung
│   │   ├── csv_to_json.py      # Konvertierung
│   │   └── extract_xml_from_zip.py
│   ├── projects/               # Projekt-Dateien (generiert)
│   └── vector_store/           # ChromaDB-Daten
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── app.component.*         # Root-Komponente
│   │   │   ├── app-routing.module.ts   # Routing-Konfiguration
│   │   │   ├── dashboard/              # Dashboard-Module
│   │   │   │   ├── project-list/       # Projekt-Übersicht
│   │   │   │   ├── project-detail/     # Projekt-Details
│   │   │   │   └── edit-project-dialog/ # Projekt-Dialog
│   │   │   ├── processing/             # Processing-Module
│   │   │   │   ├── upload/             # Datei-Upload
│   │   │   │   ├── results/            # Ergebnis-Anzeige
│   │   │   │   ├── edit/               # JSON-Editor
│   │   │   │   └── progress-bar/       # Progress-Anzeige
│   │   │   └── services/               # Services
│   │   │       └── backend.service.ts  # API-Kommunikation
│   │   ├── environments/               # Environment-Configs
│   │   │   ├── environment.ts          # Development
│   │   │   └── environment.prod.ts     # Production
│   │   ├── styles.css                  # Globale Styles
│   │   └── index.html                  # Entry-Point
│   ├── angular.json                    # Angular-Konfiguration
│   ├── package.json                    # NPM-Dependencies
│   ├── Dockerfile                      # Frontend Container-Config
│   └── nginx.conf                      # Nginx-Konfiguration (Prod)
│
├── docker-compose.yml          # Docker Compose-Konfiguration
├── .env                        # Umgebungsvariablen
└── README.md                   # Diese Datei
```

## 📡 API-Dokumentation

### Dashboard APIs

#### Projekte verwalten
- `GET /dashboard/` - Alle Projekte abrufen
- `POST /dashboard/` - Neues Projekt erstellen
- `PUT /dashboard/{project_id}` - Projekt aktualisieren
- `DELETE /dashboard/{project_id}` - Projekt löschen
- `GET /dashboard/projects/{project_id}` - Projekt-Details

#### Datei-Management
- `POST /dashboard/projects/{project_id}/upload` - Dateien hochladen
- `POST /dashboard/projects/{project_id}/upload_folder` - Ordner hochladen
- `GET /dashboard/projects/{project_id}/file_tree` - Dateistruktur abrufen
- `DELETE /dashboard/projects/{project_id}/input_files/{folder}` - Ordner löschen

#### Downloads
- `GET /dashboard/projects/{project_id}/download_output` - Alle Ergebnisse
- `GET /dashboard/projects/{project_id}/download_success_output` - Erfolgreiche
- `GET /dashboard/projects/{project_id}/download_fail_output` - Fehlgeschlagene
- `GET /dashboard/projects/{project_id}/download_success_excel` - Excel-Export

### Processing APIs

- `POST /processing/start_ocr` - OCR-Verarbeitung starten
- `POST /processing/pause_ocr` - OCR pausieren
- `POST /processing/stop_ocr` - OCR stoppen
- `GET /processing/status/{project_id}` - Status abrufen
- `PUT /processing/update_result` - Ergebnis aktualisieren

### Interaktive API-Dokumentation

FastAPI stellt automatisch eine interaktive API-Dokumentation bereit:
- **Swagger UI**: http://localhost:6006/docs
- **ReDoc**: http://localhost:6006/redoc

## 🎨 Design-System

### Farbschema
- **Primary Gradient**: `#667eea` → `#764ba2`
- **Success**: `#4CAF50`
- **Error**: `#f56565`
- **Warning**: `#FFA726`
- **Info**: `#42A5F5`

### Komponenten-Styles
- **Cards**: Weiße Karten mit Box-Shadow und Border-Radius
- **Buttons**: Gradient-Backgrounds mit Hover-Animationen
- **Icons**: Material Icons mit konsistenten Farben
- **Typography**: Inter-Font für moderne Lesbarkeit

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📦 Production Build

### Docker Production Build
```bash
# Umgebung auf Production setzen
export ENV=PROD

# Container bauen und starten
docker compose -f docker-compose.prod.yml up --build
```

### Manuelle Production Builds

#### Frontend
```bash
cd frontend
ng build --configuration production
```

Dist-Dateien werden in `frontend/dist/` erstellt.

#### Backend
```bash
cd backend
# Dependencies installieren
pip install -r requirements.txt

# Mit Gunicorn starten (Production)
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🔒 Sicherheit

- ✅ CORS-Konfiguration für sichere Cross-Origin-Requests
- ✅ Umgebungsvariablen für sensitive Daten
- ✅ Input-Validierung mit Pydantic
- ✅ SQL-Injection-Schutz durch SQLAlchemy ORM
- ⚠️ **Hinweis**: Für Production sollte CORS restriktiver konfiguriert werden

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Commit deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Erstelle einen Pull Request

## 📝 Lizenz

Dieses Projekt ist proprietär und gehört WJW Digital.

## 👥 Team

Entwickelt von FFengineering fabian-franz@ffengineering

## 📞 Support

Bei Fragen oder Problemen:
- E-Mail: fabian-franz@ffengineering.de
---

**Version**: 1.0.0  
**Letztes Update**: Februar 2026
