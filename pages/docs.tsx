import React, { useState } from 'react'
import Header from './header'

interface DocsProps {
  dark: boolean
  setDark: React.Dispatch<React.SetStateAction<boolean>>
}

// ── Types ─────────────────────────────────────────────────────────────────────
interface Section {
  id: string
  label: string
  content: () => JSX.Element
}

// ── Prose helpers — dark: variants work because parent has the `dark` class ───
function H1({ children }: { children: React.ReactNode }) {
  return <h1 className="text-xl font-semibold text-stone-800 dark:text-white mb-1">{children}</h1>
}
function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="text-sm font-semibold text-pine-600 dark:text-pine-400 mt-7 mb-2">{children}</h2>
}
function P({ children }: { children: React.ReactNode }) {
  return <p className="text-stone-400 dark:text-stone-500 text-sm leading-relaxed mb-3">{children}</p>
}
function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="text-pine-700 dark:text-pine-300 bg-pine-50 dark:bg-pine-400/10 border border-pine-200 dark:border-pine-400/20 px-1.5 py-px rounded text-xs font-mono">
      {children}
    </code>
  )
}
function Pre({ children }: { children: string }) {
  return (
    <div className="bg-stone-50 dark:bg-[#111] border border-stone-200 dark:border-white/8 rounded-xl p-4 mb-3 overflow-x-auto">
      <pre className="text-xs text-stone-500 dark:text-stone-400 font-mono leading-relaxed whitespace-pre">{children}</pre>
    </div>
  )
}
function Note({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-l-2 border-pine-300 dark:border-pine-500/40 pl-3 mb-3 text-xs text-stone-400 dark:text-stone-500 leading-relaxed">
      {children}
    </div>
  )
}
function Tree({ lines }: { lines: string[] }) {
  return (
    <div className="bg-stone-50 dark:bg-white/5 border border-stone-200 dark:border-white/8 rounded-xl p-4 mb-3 font-mono text-xs text-stone-400 dark:text-stone-500 leading-relaxed">
      {lines.map((l, i) => <div key={i}>{l}</div>)}
    </div>
  )
}

// ── Sections ──────────────────────────────────────────────────────────────────
const SECTIONS: Section[] = [
  {
    id: 'overview',
    label: 'Overview',
    content: () => (
      <div>
        <H1>pynapple js</H1>
        <P>
          pynapple js is a minimal, zero-magic web framework that runs Python and Node.js
          on a single port. No proxies, no config hell — just a clean build engine
          and a Python stdlib HTTP server working together.
        </P>
        <H2>How it works</H2>
        <P>
          When you run <Code>python3 app.py dev</Code>, two processes start:
        </P>
        <Tree lines={[
          'python3 app.py dev',
          '├── npm run dev        → core/engine/dev.js',
          '│   ├── esbuild watch  → pages/.dev/bundle.js',
          '│   └── tailwindcss    → pages/.dev/bundle.css',
          '└── python server      → core/serve/server.py :2000',
          '    ├── GET /          → _DEV_HTML (inlined)',
          '    ├── GET /bundle.js → pages/.dev/bundle.js',
          '    ├── GET /bundle.css→ pages/.dev/bundle.css',
          '    └── GET /_reload   → SSE live-reload stream',
        ]} />
        <P>
          Node.js handles only the build step. Python serves everything — static assets,
          API routes, and the SSE live-reload channel — all on <Code>:2000</Code>.
        </P>
        <H2>Cross-language IPC</H2>
        <P>
          No sockets or message queues. When esbuild finishes a rebuild, <Code>dev.js</Code> writes
          a timestamp to <Code>pages/.dev/.reload</Code>. A background Python thread polls
          this file every 150ms and signals all connected SSE clients to reload.
        </P>
      </div>
    ),
  },
  {
    id: 'getting-started',
    label: 'Getting Started',
    content: () => (
      <div>
        <H1>Getting Started</H1>
        <H2>Requirements</H2>
        <Tree lines={['Python 3.10+', 'Node.js 18+', 'npm']} />
        <H2>Dev server</H2>
        <Pre>{`python3 app.py dev`}</Pre>
        <P>
          This bootstraps a Python venv at <Code>.python/</Code>, installs dependencies,
          then starts both the Node build watcher and the Python server.
          Open <Code>http://localhost:2000</Code>.
        </P>
        <H2>Production build</H2>
        <Pre>{`python3 app.py build`}</Pre>
        <P>
          Bundles and minifies everything into <Code>pages/dist/</Code>,
          then starts the production server on <Code>:8000</Code>.
        </P>
        <Note>
          The first run creates a <Code>.python/</Code> virtual environment automatically.
          Delete it to force a clean rebuild.
        </Note>
      </div>
    ),
  },
  {
    id: 'structure',
    label: 'Project Structure',
    content: () => (
      <div>
        <H1>Project Structure</H1>
        <Tree lines={[
          '.',
          '├── app.py                 ← entry point & bootstrapper',
          '├── requirements.txt       ← Python deps',
          '├── package.json           ← Node deps',
          '├── tailwind.config.js     ← Tailwind config',
          '├── tsconfig.json          ← TypeScript config',
          '│',
          '├── pages/                 ← frontend (React + TSX)',
          '│   ├── hello.tsx          ← app entry (ReactDOM.render)',
          '│   ├── app.tsx            ← home page',
          '│   ├── docs.tsx           ← docs page',
          '│   ├── header.tsx         ← shared nav component',
          '│   ├── styles/',
          '│   │   └── globals.css    ← Tailwind + custom CSS',
          '│   ├── .dev/              ← dev build output (gitignored)',
          '│   └── dist/              ← prod build output (gitignored)',
          '│',
          '└── core/                  ← Python backend',
          '    ├── api/               ← API route handlers',
          '    ├── serve/',
          '    │   └── server.py      ← HTTP server',
          '    └── engine/',
          '        ├── dev.js         ← build watcher',
          '        └── build.js       ← production build',
        ]} />
      </div>
    ),
  },
  {
    id: 'pages',
    label: 'Pages',
    content: () => (
      <div>
        <H1>Pages</H1>
        <P>
          All frontend code lives in <Code>pages/</Code>. The entry point is{' '}
          <Code>pages/hello.tsx</Code> which mounts the router and manages global state.
        </P>
        <H2>Adding a page</H2>
        <P>
          Create a new TSX file in <Code>pages/</Code> and import it in <Code>hello.tsx</Code>.
          Routing is hash-based — no dependencies needed.
        </P>
        <Pre>{`// pages/hello.tsx — hash router
function Router() {
  const [hash, setHash] = useState(window.location.hash)
  useEffect(() => {
    const h = () => setHash(window.location.hash)
    window.addEventListener('hashchange', h)
    return () => window.removeEventListener('hashchange', h)
  }, [])
  if (hash.startsWith('#/about')) return <About dark={dark} setDark={setDark} />
  return <Home dark={dark} setDark={setDark} />
}`}</Pre>
        <H2>Shared components</H2>
        <P>
          Place shared components in <Code>pages/</Code> alongside your pages.
          The <Code>Header</Code> component is a good example — imported by both
          <Code>app.tsx</Code> and <Code>docs.tsx</Code>.
        </P>
        <H2>Styling</H2>
        <P>
          Tailwind CSS is processed inline by esbuild via a PostCSS plugin.
          Add custom styles to <Code>pages/styles/globals.css</Code>.
          Dark mode uses the <Code>class</Code> strategy — add <Code>dark:</Code> variants freely.
        </P>
      </div>
    ),
  },
  {
    id: 'api-routes',
    label: 'API Routes',
    content: () => (
      <div>
        <H1>API Routes</H1>
        <P>
          Each API route is a Python file in <Code>core/api/</Code> with a{' '}
          <Code>handle(handler)</Code> function. The server calls it with the
          active <Code>BaseHTTPRequestHandler</Code> instance.
        </P>
        <H2>Creating a route</H2>
        <Pre>{`# core/api/hello.py

def handle(handler):
    handler._respond(
        200,
        "application/json",
        b'{"message": "Hello from pynapple!"}'
    )`}</Pre>
        <H2>Registering in the server</H2>
        <Pre>{`# core/serve/server.py
import core.api.hello as api_hello

def do_POST(self):
    route = urlparse(self.path).path
    if route == "/api/hello":
        api_hello.handle(self)
    ...`}</Pre>
        <H2>Streaming responses</H2>
        <P>
          For streaming (e.g. AI tokens, file downloads), write bytes directly
          to <Code>handler.wfile</Code> and flush after each chunk.
        </P>
        <Pre>{`def handle(handler):
    handler.send_response(200)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.end_headers()
    for chunk in generate():
        handler.wfile.write(chunk.encode())
        handler.wfile.flush()`}</Pre>
        <Note>
          pynapple uses <Code>ThreadingHTTPServer</Code> — each request runs in its
          own thread, so streaming handlers don't block other requests.
        </Note>
      </div>
    ),
  },
  {
    id: 'config',
    label: 'Configuration',
    content: () => (
      <div>
        <H1>Configuration</H1>
        <H2>Tailwind</H2>
        <P>
          <Code>tailwind.config.js</Code> at the project root. Content paths scan{' '}
          <Code>{'pages/**/*.{ts,tsx}'}</Code> automatically. Dark mode uses <Code>class</Code> strategy.
        </P>
        <Pre>{`// tailwind.config.js
export default {
  darkMode: 'class',
  content: ['./pages/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { 400: '#f59e0b', 500: '#d97706' },
      },
    },
  },
}`}</Pre>
        <H2>TypeScript</H2>
        <P>
          <Code>tsconfig.json</Code> at project root covers all files in{' '}
          <Code>pages/</Code>. esbuild handles transpilation — tsc is for type checking only.
        </P>
        <H2>Environment variables</H2>
        <P>
          Create a <Code>.env</Code> file at the project root.
          Python loads it via <Code>python-dotenv</Code> on server start.
        </P>
        <Pre>{`# .env
MY_API_KEY=sk-...
PORT=2000`}</Pre>
        <H2>Python dependencies</H2>
        <P>Add packages to <Code>requirements.txt</Code>. The bootstrapper installs them on next run.</P>
        <H2>Node dependencies</H2>
        <P>Edit <Code>package.json</Code> normally — <Code>npm install</Code> runs automatically on startup.</P>
      </div>
    ),
  },
  {
    id: 'build',
    label: 'Build & Deploy',
    content: () => (
      <div>
        <H1>Build & Deploy</H1>
        <H2>Build</H2>
        <Pre>{`python3 app.py build`}</Pre>
        <P>Produces:</P>
        <Tree lines={[
          'pages/dist/',
          '├── bundle.js    ← minified React app',
          '├── bundle.css   ← minified Tailwind CSS',
          '└── index.html   ← static HTML shell',
        ]} />
        <H2>Serve</H2>
        <P>
          After building, the Python server starts automatically on <Code>:8000</Code>{' '}
          serving the <Code>pages/dist/</Code> directory. No Node.js process runs in production.
        </P>
        <H2>Deploy</H2>
        <P>
          Copy the project to your server (excluding <Code>node_modules/</Code>,{' '}
          <Code>.python/</Code>, and <Code>pages/.dev/</Code>), then run:
        </P>
        <Pre>{`python3 app.py build`}</Pre>
        <Note>
          pynapple's server has zero external Python runtime dependencies beyond
          the packages in <Code>requirements.txt</Code>. The stdlib HTTP server
          is production-capable for moderate traffic.
        </Note>
      </div>
    ),
  },
]

// ── Docs layout ───────────────────────────────────────────────────────────────
export default function Docs({ dark, setDark }: DocsProps) {
  const [active, setActive] = useState('overview')
  const section = SECTIONS.find(s => s.id === active) ?? SECTIONS[0]

  return (
    <div className={dark ? 'dark' : ''}>
      <div className="min-h-screen bg-[#fafaf9] dark:bg-[#0c0c0c] font-mono flex flex-col transition-colors duration-300">

        <Header
          dark={dark}
          setDark={setDark}
          breadcrumb={<span className="text-stone-400 dark:text-stone-500 text-xs">docs</span>}
        />

        <div className="flex flex-1 overflow-hidden">

          {/* Sidebar */}
          <aside className="w-44 shrink-0 border-r border-stone-100 dark:border-white/5 py-5 px-3 overflow-y-auto bg-[#fafaf9] dark:bg-[#0c0c0c] transition-colors duration-300">
            <nav className="space-y-px">
              {SECTIONS.map(s => (
                <button
                  key={s.id}
                  onClick={() => setActive(s.id)}
                  className={`w-full text-left px-2 py-1.5 rounded text-xs transition-colors duration-150 ${
                    active === s.id
                      ? 'text-stone-700 dark:text-stone-100 bg-stone-100 dark:bg-white/10'
                      : 'text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </nav>
          </aside>

          {/* Content */}
          <main className="flex-1 overflow-y-auto px-10 py-8 max-w-2xl">
            {section.content()}
          </main>

        </div>
      </div>
    </div>
  )
}
