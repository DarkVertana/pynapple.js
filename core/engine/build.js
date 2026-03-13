/**
 * core/engine/build.js — pynapple js · production build
 *
 * 1. esbuild bundles  pages/hello.tsx  →  pages/dist/bundle.js  (minified)
 *    PostCSS + Tailwind runs inline     →  pages/dist/bundle.css (minified)
 * 2. Generates                             pages/dist/index.html
 */

import * as esbuild from 'esbuild'
import postcss       from 'postcss'
import tailwindcss   from 'tailwindcss'
import autoprefixer  from 'autoprefixer'
import fs            from 'fs'
import path          from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT  = path.resolve(__dirname, '../..')
const PAGES = path.resolve(ROOT, 'pages')
const DIST  = path.resolve(PAGES, 'dist')
const TW_CONFIG = path.join(ROOT, 'tailwind.config.js')

fs.mkdirSync(DIST, { recursive: true })

// PostCSS + Tailwind plugin
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
      }
    })
  },
}

// ── Bundle TSX + CSS ───────────────────────────────────────────────────────────
process.stdout.write('  →  Bundling TSX + CSS …\n')

await esbuild.build({
  entryPoints: [path.join(PAGES, 'hello.tsx')],
  bundle:      true,
  format:      'esm',
  jsx:         'automatic',
  outfile:     path.join(DIST, 'bundle.js'),   // CSS lands at bundle.css alongside
  minify:      true,
  define:      { 'process.env.NODE_ENV': '"production"' },
  plugins:     [cssPlugin],
})

process.stdout.write('  ✓  bundle.js + bundle.css\n')

// ── index.html ─────────────────────────────────────────────────────────────────
fs.writeFileSync(path.join(DIST, 'index.html'), `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>pynapple js</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🍍</text></svg>"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="/bundle.css"/>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/bundle.js"></script>
</body>
</html>`)

process.stdout.write('  ✓  index.html\n\n  Built → pages/dist/\n\n')
