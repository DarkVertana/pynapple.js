import React from 'react'
import Header from './header'

interface AppProps {
  dark: boolean
  setDark: React.Dispatch<React.SetStateAction<boolean>>
}

export default function App({ dark, setDark }: AppProps) {
  return (
    <div className={dark ? 'dark' : ''}>
      <div className="min-h-screen bg-[#fafaf9] dark:bg-[#0c0c0c] font-mono flex flex-col transition-colors duration-300">

        {/* Ambient glow */}
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-1/3 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-pine-400/10 dark:bg-pine-400/6 rounded-full blur-[120px]" />
        </div>

        <Header dark={dark} setDark={setDark} />

        {/* Hero */}
        <main className="relative flex-1 flex flex-col items-center justify-center px-6 text-center">

          {/* Floating pineapple */}
          <div className="fade-up mb-6 select-none float text-5xl">🍍</div>

          {/* Eyebrow */}
          <div className="fade-up fade-up-1 mb-7 inline-flex items-center gap-2 bg-white dark:bg-white/5 border border-stone-200 dark:border-white/10 shadow-sm text-[11px] text-stone-400 dark:text-stone-500 px-3.5 py-1.5 rounded-full tracking-wide">
            <span className="w-1.5 h-1.5 rounded-full bg-pine-500 shrink-0" />
            scratch-built · zero magic
          </div>

          {/* Headline */}
          <div className="fade-up fade-up-2 space-y-3 mb-8">
            <h1 className="text-[2.75rem] font-semibold text-stone-900 dark:text-white tracking-[-0.03em] leading-none">
              pynapple js
            </h1>
            <p className="text-stone-400 dark:text-stone-500 text-[15px] max-w-[22rem] mx-auto leading-relaxed font-normal">
              Python&nbsp;+&nbsp;Node.js on a single port.
              <br />
              Built from scratch. No magic.
            </p>
          </div>

          {/* Command block — macOS window chrome */}
          <div className="fade-up fade-up-3 mb-10">
            <div className="inline-flex items-center gap-3 bg-white dark:bg-[#161616] border border-stone-200 dark:border-white/10 rounded-2xl px-5 py-3.5 shadow-sm hover:shadow-md hover:border-stone-300 dark:hover:border-white/20 transition-all duration-300">
              <div className="flex gap-1.5 shrink-0">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
              </div>
              <div className="w-px h-3.5 bg-stone-200 dark:bg-white/10 shrink-0" />
              <span className="text-stone-300 dark:text-stone-600 text-sm select-none">$</span>
              <span className="text-stone-600 dark:text-stone-300 text-sm tracking-tight">python3 app.py dev</span>
            </div>
          </div>

          {/* Feature pills */}
          <div className="fade-up fade-up-4 flex flex-wrap justify-center gap-2">
            {['esbuild', 'tailwindcss', 'react', 'python stdlib', 'live reload'].map(f => (
              <span
                key={f}
                className="text-[11px] text-stone-400 dark:text-stone-500 bg-white dark:bg-white/5 border border-stone-100 dark:border-white/8 shadow-sm px-3 py-1 rounded-full hover:border-stone-200 dark:hover:border-white/15 hover:text-stone-500 dark:hover:text-stone-400 transition-all duration-200"
              >
                {f}
              </span>
            ))}
          </div>

        </main>

        {/* Footer */}
        <footer className="relative flex items-center justify-center gap-4 py-6">
          <span className="text-[11px] text-stone-300 dark:text-stone-600 tracking-widest uppercase">pynapple js</span>
          <span className="text-stone-200 dark:text-stone-700 text-xs">·</span>
          <a href="#/docs" className="text-[11px] text-stone-300 dark:text-stone-600 hover:text-stone-500 dark:hover:text-stone-400 transition-colors duration-200 no-underline tracking-widest uppercase">docs</a>
        </footer>

      </div>
    </div>
  )
}
