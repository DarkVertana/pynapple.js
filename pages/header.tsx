import React from 'react'

function SunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4"/>
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  )
}

interface HeaderProps {
  dark: boolean
  setDark: React.Dispatch<React.SetStateAction<boolean>>
  breadcrumb?: React.ReactNode
}

export default function Header({ dark, setDark, breadcrumb }: HeaderProps) {
  return (
    <nav className="sticky top-0 z-20 flex items-center justify-between px-8 py-4 border-b border-stone-100 dark:border-white/5 bg-[#fafaf9]/75 dark:bg-[#0c0c0c]/80 backdrop-blur-xl transition-colors duration-300">
      <div className="flex items-center gap-2">
        <a href="#/" className="flex items-center gap-2 no-underline">
          <span className="text-sm">🍍</span>
          <span className="text-stone-800 dark:text-stone-100 font-semibold text-sm tracking-tight">pynapple js</span>
        </a>
        {breadcrumb && (
          <>
            <span className="text-stone-300 dark:text-stone-600 text-xs">/</span>
            {breadcrumb}
          </>
        )}
      </div>
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-5 text-xs text-stone-400 dark:text-stone-500">
          <a href="#/docs" className="hover:text-stone-700 dark:hover:text-stone-200 transition-colors duration-200 no-underline">docs</a>
          <span className="hover:text-stone-700 dark:hover:text-stone-200 cursor-pointer transition-colors duration-200">github</span>
        </div>
        <button
          onClick={() => setDark(d => !d)}
          className="flex items-center justify-center w-7 h-7 rounded-lg border border-stone-200 dark:border-white/10 text-stone-500 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-white/8 hover:text-stone-700 dark:hover:text-white transition-all duration-200"
          aria-label="Toggle theme"
        >
          {dark ? <SunIcon /> : <MoonIcon />}
        </button>
      </div>
    </nav>
  )
}
