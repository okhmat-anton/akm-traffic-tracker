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

This is free opensource copy of Keitaro Tracker https://keitaro.io:

- **Frontend:** FastAPI — a high-performance asynchronous API server.
- **Backend:** Vue 2 + Vuetify — a Material Design UI framework for Vue.js.

Key features:
- Collecting metric data from different sources with deep analytics.
- Landing pages storage with PHP support.
- Ability to make custom routes for different domains and countries.
- All other features that have Keitaro platform

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

## 🚀 Running the Project

### Install

```bash
make install
```

### Restart

```bash
make restart
```

### Super admin user login 

```bash
login tracker_user 
password admin 
```

### Run Locally

```bash
make install-local
```

By default:
- API will be available at `https://localhost`
- Dashboard will be available at `https://localhost/backend`

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
  │   ├── default/
  ├── app.py
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

