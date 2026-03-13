<div align="center">

<br />

# 🍍 pynapple.js

**Python + Node.js on a single port. Built from scratch. No magic.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![esbuild](https://img.shields.io/badge/esbuild-0.24-FFCF00?style=flat-square&logo=esbuild&logoColor=black)](https://esbuild.github.io)

<br />

```
┌──────────────────────────────────────┐
│  python3 app.py dev                  │
│                                      │
│  ✓  Virtual environment ready        │
│  ✓  Python dependencies installed    │
│  ✓  Node dependencies ready          │
│                                      │
│  pynapple js  ·  unified  :2000      │
│  http://localhost:2000               │
└──────────────────────────────────────┘
```

</div>

---

## What is pynapple.js?

pynapple.js is a **zero-magic full-stack framework** that runs a React + TypeScript frontend and a Python backend on a **single unified port** — no proxies, no config files, no ceremony.

One command to dev. One command to build. That's it.

---

## Architecture

```
pynapple.js
│
├── app.py                    ← Single entry point (dev | build)
│
├── core/
│   ├── engine/
│   │   ├── dev.js            ← esbuild watch + Tailwind CSS watch
│   │   └── build.js          ← esbuild bundle + Tailwind CSS build
│   │
│   └── serve/
│       └── server.py         ← Python HTTP server (stdlib only)
│                               · dev  → :2000  (SSE live-reload)
│                               · prod → :8000  (static dist)
│
├── pages/                    ← React + TypeScript source
│   ├── app.tsx
│   ├── header.tsx
│   ├── docs.tsx
│   ├── hello.tsx
│   └── styles/
│       └── globals.css       ← Tailwind CSS entry
│
├── package.json              ← Node deps (React, esbuild, Tailwind)
├── requirements.txt          ← Python deps (python-dotenv)
├── tailwind.config.js
├── tsconfig.json
└── postcss.config.js
```

### How it works

```
                    ┌─────────────────────────────────────┐
                    │            app.py (entry)            │
                    └──────────┬──────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
  Bootstrap Python      Bootstrap Node        Launch processes
  virtual env (.python)  node_modules         in parallel
  install pip deps       npm install
  verify imports

                    ┌───────────────┐    ┌──────────────────────┐
                    │  Node Watcher │    │   Python HTTP Server  │
                    │  esbuild      │    │   (stdlib only)       │
                    │  tailwindcss  │    │                       │
                    │               │    │  GET /         → HTML │
                    │  writes to    │    │  GET /bundle.js → JS  │
                    │  pages/.dev/  │    │  GET /bundle.css → CSS│
                    │  + .reload    │    │  GET /_reload  → SSE  │
                    └───────────────┘    └──────────────────────┘
                           │                       │
                           └──────────┬────────────┘
                                      ▼
                              http://localhost:2000
                              (single unified port)
```

### Live Reload

```
  File change
      │
      ▼
  esbuild / tailwind rebuild
      │
      ▼
  writes pages/.dev/.reload  (e.g. "js:1710000000" or "css:1710000000")
      │
      ▼
  Python watcher thread detects change
      │
      ├── type == "css"  →  browser swaps stylesheet (no full reload)
      └── type == "js"   →  browser does location.reload()
```

---

## Getting Started

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 8+ |

### Run in Dev Mode

```bash
python3 app.py dev
```

Opens at **http://localhost:2000** with hot live-reload. Changes to `.tsx`, `.css` files reflect instantly in the browser.

### Build for Production

```bash
python3 app.py build
```

Bundles the frontend into `pages/dist/` and serves at **http://0.0.0.0:8000**.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript |
| Styling | Tailwind CSS 3 + PostCSS |
| Bundler | esbuild (ultra-fast) |
| Server | Python stdlib `http.server` |
| Live Reload | Server-Sent Events (SSE) |
| Env | python-dotenv |

---

## Project Philosophy

- **No magic** — every layer is explicit and readable
- **Zero framework overhead** — no Next.js, no Vite, no Django
- **Single port** — frontend and backend on one address
- **Stdlib first** — Python server uses zero third-party packages
- **Fast builds** — esbuild compiles TypeScript in milliseconds

---

<div align="center">

<br />

**Developed with ❤️ by [Pratik](https://github.com/DarkVertana)**

<br />

`scratch-built · zero magic · single port`

</div>
