import './styles/globals.css'
import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import Home from './app'
import Docs from './docs'
import Blog from './blog'
import Admin from './admin'

function Router() {
  const [hash, setHash] = useState(window.location.hash)
  const [dark, setDark] = useState(() => {
    try { return localStorage.getItem('theme') === 'dark' } catch { return false }
  })

  useEffect(() => {
    try { localStorage.setItem('theme', dark ? 'dark' : 'light') } catch {}
  }, [dark])

  useEffect(() => {
    const handler = () => setHash(window.location.hash)
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])

  if (hash.startsWith('#/admin')) return <Admin dark={dark} setDark={setDark} />
  if (hash.startsWith('#/blog')) return <Blog dark={dark} setDark={setDark} />
  if (hash.startsWith('#/docs')) return <Docs dark={dark} setDark={setDark} />
  return <Home dark={dark} setDark={setDark} />
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><Router /></React.StrictMode>
)
