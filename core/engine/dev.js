/**
 * core/engine/dev.js — pynapple js · build watcher (no HTTP server)
 *
 * Python handles the single unified server on :2000.
 * This process only does:
 *   - esbuild watches pages/hello.tsx  →  pages/.dev/bundle.js + bundle.css
 *     (Tailwind CSS is processed inline via PostCSS plugin — like Next.js)
 *   - writes pages/.dev/.reload on each successful rebuild (signals Python SSE)
 */

import * as esbuild from 'esbuild'
import postcss       from 'postcss'
import tailwindcss   from 'tailwindcss'
import autoprefixer  from 'autoprefixer'
import fs            from 'fs'
import path          from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT   = path.resolve(__dirname, '../..')
const PAGES  = path.resolve(ROOT, 'pages')
const DEV    = path.resolve(PAGES, '.dev')
const TW_CONFIG = path.join(ROOT, 'tailwind.config.js')

fs.mkdirSync(DEV, { recursive: true })

const RELOAD_FILE = path.join(DEV, '.reload')

// Signal Python server to broadcast live-reload to all clients
function signalReload(type = 'js') {
  fs.writeFileSync(RELOAD_FILE, `${type}:${Date.now()}`)
}

// Collect all TS/TSX files so esbuild knows to re-run the CSS plugin
// when any component file changes (Tailwind needs to rescan for new classes)
function getContentFiles(dir) {
  const files = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory() && !['node_modules', '.dev', 'dist'].includes(entry.name)) {
      files.push(...getContentFiles(full))
    } else if (entry.isFile() && /\.(ts|tsx)$/.test(entry.name)) {
      files.push(full)
    }
  }
  return files
}

// PostCSS + Tailwind plugin — runs inside esbuild so CSS and JS stay in sync
const cssPlugin = {
  name: 'postcss-tailwind',
  setup(build) {
    build.onLoad({ filter: /\.css$/ }, async (args) => {
      const css = await fs.promises.readFile(args.path, 'utf8')
      const result = await postcss([
        tailwindcss({ config: TW_CONFIG }),
        autoprefixer,
      ]).process(css, { from: args.path })

      return {
        contents: result.css,
        loader: 'css',
        // Tell esbuild to re-run this loader when any TSX file changes
        // so Tailwind rescans for newly added utility classes
        watchFiles: [args.path, TW_CONFIG, ...getContentFiles(PAGES)],
      }
    })
  },
}

// ── esbuild watch ──────────────────────────────────────────────────────────────
const ctx = await esbuild.context({
  entryPoints: [path.join(PAGES, 'hello.tsx')],
  bundle:      true,
  format:      'esm',
  jsx:         'automatic',
  outfile:     path.join(DEV, 'bundle.js'),   // CSS lands at bundle.css alongside
  sourcemap:   true,
  define:      { 'process.env.NODE_ENV': '"development"' },
  plugins: [
    cssPlugin,
    {
      name: 'pynapple-signal',
      setup(build) {
        build.onEnd(result => {
          if (result.errors.length === 0) {
            process.stdout.write('  ↺  bundle rebuilt\n')
            signalReload('js')
          } else {
            process.stdout.write(`  ✗  ${result.errors.length} error(s)\n`)
          }
        })
      },
    },
  ],
})

await ctx.watch()
process.stdout.write('  ✓  esbuild watching (JS + Tailwind CSS)\n\n')

// ── Shutdown ───────────────────────────────────────────────────────────────────
process.on('SIGINT', () => {
  ctx.dispose()
  process.exit(0)
})
