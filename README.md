# ACEest Fitness & Gym – DevOps CI/CD Pipeline

![CI](https://github.com/<your-username>/aceest-devops/actions/workflows/main.yml/badge.svg)

A Flask web application for gym and fitness management, delivered through an
automated DevOps pipeline: **Git/GitHub → Pytest → Docker → Jenkins → GitHub Actions**.


---

## 1. Features

| Feature | Endpoint |
|---|---|
| Health check | `GET /health` |
| List / view fitness programs (Fat Loss, Muscle Gain, Beginner) | `GET /programs`, `GET /programs/<code>` |
| Daily calorie estimate (weight × program factor) | `POST /calories` |
| BMI and category | `POST /bmi` |
| Client management (create, list, view, delete) | `POST/GET /clients`, `GET/DELETE /clients/<name>` |
| Weekly adherence tracking | `POST/GET /clients/<name>/progress` |
| Workout logging | `POST/GET /clients/<name>/workouts` |
| Program suggestion generator | `POST /clients/<name>/generate-program` |

Data is stored in SQLite (`aceest_fitness.db`, path configurable with the `ACEEST_DB` environment variable).

## 2. Project Structure

```
aceest-devops/
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies (pinned)
├── tests/                    # Pytest suite
│   ├── conftest.py           # Fixtures (temporary DB per test)
│   ├── test_logic.py         # Unit tests for business logic
│   └── test_api.py           # Endpoint tests
├── Dockerfile                # Container image definition
├── .dockerignore
├── Jenkinsfile               # Jenkins BUILD pipeline
├── .github/workflows/main.yml  # GitHub Actions CI pipeline
├── .flake8                   # Lint configuration
```

## 3. Local Setup and Execution

Prerequisites: Python 3.10+, Git, Docker.

```bash
git clone https://github.com/<your-username>/aceest-devops.git
cd aceest-devops
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The app runs at http://localhost:5000. Example requests:

```bash
curl http://localhost:5000/programs
curl -X POST http://localhost:5000/clients -H "Content-Type: application/json" \
     -d '{"name": "Arjun", "age": 28, "weight": 70, "program": "MG"}'
curl -X POST http://localhost:5000/bmi -H "Content-Type: application/json" \
     -d '{"weight": 70, "height": 175}'
```

## 4. Running Tests Manually

```bash
source venv/bin/activate
pytest -v              # run all tests
flake8 app.py tests/   # lint check
```

Each test gets its own temporary SQLite database, so tests never touch real data.

## 5. Running with Docker

```bash
docker build -t aceest-fitness .
docker run -d -p 5000:5000 --name aceest aceest-fitness   # run the app
docker run --rm aceest-fitness pytest -v                  # run tests inside the container
```

Dockerfile design choices: `python:3.12-slim` base for a small image, dependencies installed
before copying code (layer caching), `--no-cache-dir` pip installs, a non-root `appuser`,
a `HEALTHCHECK` on `/health`, and `gunicorn` as the production server.

## 6. CI/CD Integration Overview

```
Developer ──git push──▶ GitHub ──┬──▶ GitHub Actions (GitHub's cloud runner)
                                 │      Build & Lint → Docker Build → Pytest in container
                                 │
                                 └──▶ Jenkins (on the project VM, polls GitHub)
                                        Checkout → Install → Lint → Unit Tests
                                        → Docker Build → Pytest in container
```

### GitHub Actions (`.github/workflows/main.yml`)
Triggered on every `push` and `pull_request`. Runs on a fresh GitHub-hosted Ubuntu runner:
1. **Build & Lint** – installs dependencies, compiles `app.py`, runs `flake8`.
2. **Docker Image Assembly** – builds the image (runs only if stage 1 passes).
3. **Automated Testing** – runs `pytest` inside the built container, then smoke-tests `/health`.

### Jenkins (`Jenkinsfile`)
A Pipeline job configured with *Pipeline script from SCM* pointing at this repository.
Jenkins polls GitHub (`H/5 * * * *`) and, on new commits, performs a clean build on the
VM: checkout, virtual-env install, lint, unit tests (JUnit report published),
Docker image build tagged with the build number, and tests inside the container.
The workspace is deleted after each run so every build starts clean.
This acts as a secondary quality gate in a controlled build environment.

## 7. Branching Strategy

- `main` – stable, always passing CI.
- `feature/*` – new features (e.g. `feature/flask-app`, `feature/docker`).
- `fix/*` – bug fixes.
- Changes are merged into `main` via pull requests after CI passes.
- Commit messages follow the Conventional Commits style (`feat:`, `fix:`, `test:`, `ci:`, `docs:`).
# ACEest Fitness & Gym - DevOps CI/CD Pipeline
