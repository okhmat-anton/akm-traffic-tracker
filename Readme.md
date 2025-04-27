![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-blue)
![Vue.js](https://img.shields.io/badge/Vue-2.x-green)
![Vuetify](https://img.shields.io/badge/Vuetify-Material--UI-purple)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)

# 📚 Project Name

**Description:**  
> This project is a modern traffic tracking and campaign management platform, similar to Keitaro, built with FastAPI and Vue 2 + Vuetify. It provides powerful features like real-time data analysis, campaign optimization, affiliate tracking, and detailed reporting. The backend is optimized for high performance and scalability, while the frontend delivers a fully responsive, Material Design-based user experience. Perfect for marketing professionals, ad networks, and affiliate managers who need reliable traffic management and advanced analytics.
---

## 📂 Table of Contents

- [About the Project](#about-the-project)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Running the Project](#running-the-project)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Development Scripts](#development-scripts)
- [Testing](#testing)
- [Contribution Guidelines](#contribution-guidelines)
- [License](#license)
- [Contact](#contact)

---

## 📖 About the Project

This project is a modern web application with a clean separation between the backend and frontend:

- **Backend:** FastAPI — a high-performance asynchronous API server.
- **Frontend:** Vue 2 + Vuetify — a Material Design UI framework for Vue.js.

Key features:
- Rapid development and deployment.
- Clean and modular API architecture.
- Responsive UI compatible with both desktop and mobile.
- Scalable codebase.

---

## 🚀 Tech Stack

**Backend:**
- [Python 3.11+](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [PostgreSQL](https://www.postgresql.org/)

**Frontend:**
- [Vue 2](https://v2.vuejs.org/)
- [Vuetify](https://vuetifyjs.com/en/)
- [Axios](https://axios-http.com/)

**DevOps (Optional):**
- [Docker](https://www.docker.com/)
- [Nginx](https://nginx.org/en/)

---

## 🛠️ Getting Started

### Clone the Repository

```bash
git clone https://github.com/your-username/your-project.git
cd your-project
```

### Install Backend Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## 🚀 Running the Project

### Run Backend Locally

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Run Frontend Locally

```bash
cd frontend
npm run serve
```

By default:
- API will be available at `http://localhost:8000`
- Frontend will be available at `http://localhost:8080`

---

## 🏗️ Project Structure

```bash
backend/
  ├── app_pages/
  │   ├── about.py
  │   ├── campaigns.py
  │   ├── dashboard.py
  │   ├── ...
  ├── install
  │   ├── sql/
  │   ├── install.py
  │   └── requirements.txt
  ├── models/
  │   ├── campaign.py
  │   ├── domain.py
  │   ├── ...
  ├── themes/
  │   ├── main/
  ├── main.py
  ├── auth.py
  └── Dockerfile
  └── requirements.txt
nginx/
  ├── nginx.conf
  ├── nginx.dev.conf
  ├── nginx.prod.conf
  └── Dockerfile
certbot-etc/
certbot-var/
ssl/
  ├──
frontend/
  ├── app.py
  ├── requirements.txt
  └── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## ⚙️ Environment Variables

- Fully self configurable via docker-compose.yml.
- Should be open ports 433 and 80 for nginx.


## ⚙ Testing:

- Not realized yet, but should be in the future.

## 🧰 Contribution Guidelines

- Follow PEP8 coding standards for Python.
- Keep the API modular and organized.
- Write reusable Vue components.
- Use Vuetify components for consistent UI.
- Regularly update dependencies.

---

## 📜 License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for more details.

---

## 📞 Contact

**Author:** [Anton Okhmat](https://akm-media.club)  
**Email:** anton.okhmat@gmail.com  
**GitHub:** [@okhmat-anton](https://github.com/your-username)

---

