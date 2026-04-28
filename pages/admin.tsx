import React, { useState, useEffect, useRef, createContext, useContext } from 'react'

// ── Types ───────────────────────────────────────────────────────────────────

interface User {
  id: number
  name: string
  email: string
  role: string
  created_at: string
}

interface Post {
  id: number
  title: string
  slug: string
  excerpt: string
  body: string
  cover_image: string
  published: boolean
  author_id: number | null
  created_at: string
  updated_at: string
}

interface AdminProps {
  dark: boolean
  setDark: React.Dispatch<React.SetStateAction<boolean>>
}

// ── Auth Context ────────────────────────────────────────────────────────────

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<string | null>
  register: (name: string, email: string, password: string) => Promise<string | null>
  logout: () => void
}

const AuthContext = createContext<AuthState>({
  user: null, token: null, loading: true,
  login: async () => null, register: async () => null, logout: () => {},
})

function useAuth() { return useContext(AuthContext) }

function authFetch(url: string, token: string | null, opts: RequestInit = {}) {
  return fetch(url, {
    ...opts,
    headers: {
      ...opts.headers as Record<string, string>,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => {
    try { return localStorage.getItem('admin_token') } catch { return null }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) { setLoading(false); return }
    authFetch('/api/auth/me', token)
      .then(r => r.json())
      .then(d => {
        if (d.user && d.user.role === 'admin') {
          setUser(d.user)
        } else {
          localStorage.removeItem('admin_token')
          setToken(null)
        }
      })
      .catch(() => { localStorage.removeItem('admin_token'); setToken(null) })
      .finally(() => setLoading(false))
  }, [token])

  const login = async (email: string, password: string): Promise<string | null> => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (data.error) return data.error
      if (data.user.role !== 'admin') return 'Admin access required'
      localStorage.setItem('admin_token', data.token)
      setToken(data.token)
      setUser(data.user)
      return null
    } catch {
      return 'Connection failed'
    }
  }

  const register = async (name: string, email: string, password: string): Promise<string | null> => {
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      })
      const data = await res.json()
      if (data.error) return data.error
      localStorage.setItem('admin_token', data.token)
      setToken(data.token)
      setUser(data.user)
      return null
    } catch {
      return 'Connection failed'
    }
  }

  const logout = () => {
    localStorage.removeItem('admin_token')
    setToken(null)
    setUser(null)
    fetch('/api/auth/logout', { method: 'POST' }).catch(() => {})
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// ── Icons ───────────────────────────────────────────────────────────────────

function SunIcon() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>
}

function MoonIcon() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
}

function DashboardIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>
}

function PostsIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
}

function UsersIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
}

function LogoutIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
}

function LockIcon() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
}

// ── Login Screen ────────────────────────────────────────────────────────────

function LoginScreen({ dark, setDark }: { dark: boolean; setDark: React.Dispatch<React.SetStateAction<boolean>> }) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    const err = await login(email, password)
    if (err) setError(err)
    setLoading(false)
  }

  const inputCls = "w-full bg-white dark:bg-[#111] border border-stone-200 dark:border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-stone-700 dark:text-stone-300 placeholder:text-stone-300 dark:placeholder:text-stone-600 focus:outline-none focus:ring-2 focus:ring-pine-400/30 focus:border-pine-400 dark:focus:border-pine-400/50 transition-all"

  return (
    <div className={dark ? 'dark' : ''}>
      <div className="min-h-screen bg-[#fafaf9] dark:bg-[#0c0c0c] font-mono flex items-center justify-center transition-colors duration-300">
        {/* Theme toggle */}
        <button
          onClick={() => setDark(d => !d)}
          className="fixed top-6 right-6 flex items-center justify-center w-8 h-8 rounded-lg border border-stone-200 dark:border-white/10 text-stone-500 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-white/8 transition-all z-50"
        >
          {dark ? <SunIcon /> : <MoonIcon />}
        </button>

        <div className="w-full max-w-sm px-6">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-stone-100 dark:bg-white/5 border border-stone-200 dark:border-white/10 mb-4">
              <LockIcon />
            </div>
            <h1 className="text-lg font-semibold text-stone-800 dark:text-white tracking-tight">Admin Panel</h1>
            <p className="text-xs text-stone-400 dark:text-stone-500 mt-1">Sign in to pynaple js dashboard</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="px-3.5 py-2.5 rounded-lg bg-red-50 dark:bg-red-400/10 border border-red-200 dark:border-red-400/20 text-red-600 dark:text-red-400 text-xs">
                {error}
              </div>
            )}

            <div>
              <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Email</label>
              <input
                type="email"
                placeholder="admin@store.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className={inputCls}
                autoFocus
                required
              />
            </div>

            <div>
              <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Password</label>
              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className={inputCls}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-stone-800 dark:bg-white/90 text-white dark:text-stone-900 text-xs font-medium hover:bg-stone-900 dark:hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="text-center text-[10px] text-stone-300 dark:text-stone-600 mt-6">
            Default: admin@store.com / admin123
          </p>

          <div className="text-center mt-6">
            <a href="#/" className="text-[11px] text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300 transition-colors">
              &larr; Back to site
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function readingTime(text: string): string {
  const words = text.trim().split(/\s+/).length
  const mins = Math.max(1, Math.ceil(words / 200))
  return `${mins}m`
}

// ── Image Upload Hook ───────────────────────────────────────────────────────

function useImageUpload() {
  const [uploading, setUploading] = useState(false)
  const upload = async (file: File): Promise<string | null> => {
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      const data = await res.json()
      return data.error ? null : data.url
    } catch { return null }
    finally { setUploading(false) }
  }
  return { upload, uploading }
}

// ── Cover Image Upload ──────────────────────────────────────────────────────

function CoverImageUpload({ value, onChange }: { value: string; onChange: (url: string) => void }) {
  const { upload, uploading } = useImageUpload()
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    const url = await upload(file)
    if (url) onChange(url)
  }

  return (
    <div>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
      {value ? (
        <div className="relative group">
          <img src={value} alt="Cover" className="w-full h-36 object-cover rounded-lg border border-stone-200 dark:border-white/10" />
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 rounded-lg flex items-center justify-center gap-2 transition-opacity">
            <button type="button" onClick={() => inputRef.current?.click()} className="px-3 py-1.5 rounded-lg bg-white/20 text-white text-[11px] hover:bg-white/30 transition-colors">Replace</button>
            <button type="button" onClick={() => onChange('')} className="px-3 py-1.5 rounded-lg bg-red-500/40 text-white text-[11px] hover:bg-red-500/60 transition-colors">Remove</button>
          </div>
        </div>
      ) : (
        <div
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}
          onClick={() => inputRef.current?.click()}
          className="w-full h-28 border-2 border-dashed border-stone-200 dark:border-white/10 rounded-lg flex flex-col items-center justify-center gap-1.5 cursor-pointer hover:border-pine-400 dark:hover:border-pine-400/50 transition-colors"
        >
          {uploading ? (
            <span className="text-xs text-stone-400 dark:text-stone-500">Uploading...</span>
          ) : (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-stone-300 dark:text-stone-600"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
              <span className="text-[10px] text-stone-300 dark:text-stone-600">Drop or click to upload</span>
            </>
          )}
        </div>
      )}
    </div>
  )
}

// ── Dashboard View ──────────────────────────────────────────────────────────

function DashboardView() {
  const { user, token } = useAuth()
  const [stats, setStats] = useState({ posts: 0, published: 0, drafts: 0, users: 0 })

  useEffect(() => {
    authFetch('/api/posts/all', token)
      .then(r => r.json())
      .then(d => {
        const posts = d.posts || []
        setStats({
          posts: posts.length,
          published: posts.filter((p: Post) => p.published).length,
          drafts: posts.filter((p: Post) => !p.published).length,
          users: 0,
        })
      })
      .catch(() => {})
  }, [token])

  const cards = [
    { label: 'Total Posts', value: stats.posts, color: 'text-blue-500 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-400/10' },
    { label: 'Published', value: stats.published, color: 'text-green-500 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-400/10' },
    { label: 'Drafts', value: stats.drafts, color: 'text-amber-500 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-400/10' },
  ]

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-lg font-semibold text-stone-800 dark:text-white tracking-tight">
          Welcome back, {user?.name}
        </h1>
        <p className="text-xs text-stone-400 dark:text-stone-500 mt-1">
          Here's what's happening with your site.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {cards.map(card => (
          <div key={card.label} className="bg-white dark:bg-white/[0.02] border border-stone-100 dark:border-white/8 rounded-xl p-5">
            <p className="text-[11px] text-stone-400 dark:text-stone-500 uppercase tracking-wider mb-2">{card.label}</p>
            <p className={`text-2xl font-semibold ${card.color}`}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* Quick info */}
      <div className="bg-white dark:bg-white/[0.02] border border-stone-100 dark:border-white/8 rounded-xl p-5">
        <h2 className="text-xs font-semibold text-stone-700 dark:text-stone-200 mb-4">Account</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-stone-400 dark:text-stone-500">Email</span>
            <span className="text-xs text-stone-700 dark:text-stone-300">{user?.email}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-stone-400 dark:text-stone-500">Role</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-pine-50 dark:bg-pine-400/10 text-pine-600 dark:text-pine-400 border border-pine-200 dark:border-pine-400/20">
              {user?.role}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-stone-400 dark:text-stone-500">Member since</span>
            <span className="text-xs text-stone-700 dark:text-stone-300">{user?.created_at ? formatDate(user.created_at) : '—'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Posts Management View ────────────────────────────────────────────────────

const EMPTY_FORM = { title: '', slug: '', excerpt: '', body: '', cover_image: '', published: false }

function PostsView() {
  const { token } = useAuth()
  const [posts, setPosts] = useState<Post[]>([])
  const [form, setForm] = useState<typeof EMPTY_FORM>({ ...EMPTY_FORM })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: 'ok' | 'err' }>({ text: '', type: 'ok' })

  const loadPosts = () => {
    authFetch('/api/posts/all', token)
      .then(r => r.json())
      .then(d => setPosts(d.posts || []))
  }

  useEffect(() => { loadPosts() }, [])

  const flash = (text: string, type: 'ok' | 'err' = 'ok') => {
    setMessage({ text, type })
    setTimeout(() => setMessage({ text: '', type: 'ok' }), 3000)
  }

  const resetForm = () => { setForm({ ...EMPTY_FORM }); setEditingId(null); setShowForm(false) }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.title.trim()) return flash('Title is required', 'err')
    try {
      if (editingId) {
        const res = await authFetch(`/api/posts/${editingId}`, token, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form),
        })
        const data = await res.json()
        if (data.error) return flash(data.error, 'err')
        flash('Post updated')
      } else {
        const res = await authFetch('/api/posts', token, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form),
        })
        const data = await res.json()
        if (data.error) return flash(data.error, 'err')
        flash('Post created')
      }
      resetForm()
      loadPosts()
    } catch { flash('Something went wrong', 'err') }
  }

  const handleEdit = (post: Post) => {
    setForm({ title: post.title, slug: post.slug, excerpt: post.excerpt, body: post.body, cover_image: post.cover_image, published: post.published })
    setEditingId(post.id)
    setShowForm(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleDelete = async (id: number) => {
    await authFetch(`/api/posts/${id}`, token, { method: 'DELETE' })
    flash('Post deleted')
    if (editingId === id) resetForm()
    loadPosts()
  }

  const handleTogglePublish = async (post: Post) => {
    await authFetch(`/api/posts/${post.id}`, token, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ published: !post.published }),
    })
    loadPosts()
  }

  const inputCls = "w-full bg-white dark:bg-[#111] border border-stone-200 dark:border-white/10 rounded-lg px-3 py-2.5 text-xs text-stone-700 dark:text-stone-300 placeholder:text-stone-300 dark:placeholder:text-stone-600 focus:outline-none focus:ring-2 focus:ring-pine-400/30 focus:border-pine-400 dark:focus:border-pine-400/50 transition-all"

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-stone-800 dark:text-white tracking-tight">Posts</h1>
          <p className="text-xs text-stone-400 dark:text-stone-500 mt-0.5">Manage your blog content</p>
        </div>
        <button
          onClick={() => { resetForm(); setShowForm(!showForm) }}
          className="px-4 py-2 rounded-lg bg-stone-800 dark:bg-white/90 text-white dark:text-stone-900 text-xs font-medium hover:bg-stone-900 dark:hover:bg-white transition-colors"
        >
          {showForm && !editingId ? 'Cancel' : '+ New Post'}
        </button>
      </div>

      {/* Flash message */}
      {message.text && (
        <div className={`px-3.5 py-2.5 rounded-lg text-xs ${
          message.type === 'ok'
            ? 'bg-leaf-400/10 border border-leaf-400/20 text-leaf-700 dark:text-leaf-400'
            : 'bg-red-50 dark:bg-red-400/10 border border-red-200 dark:border-red-400/20 text-red-600 dark:text-red-400'
        }`}>
          {message.text}
        </div>
      )}

      {/* Form */}
      {showForm && (
        <div className="bg-white dark:bg-white/[0.02] border border-stone-100 dark:border-white/8 rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-stone-700 dark:text-stone-200 mb-5">
            {editingId ? 'Edit Post' : 'New Post'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Cover Image</label>
              <CoverImageUpload value={form.cover_image} onChange={url => setForm(f => ({ ...f, cover_image: url }))} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Title</label>
                <input type="text" placeholder="Post title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} className={inputCls} />
              </div>
              <div>
                <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Slug</label>
                <input type="text" placeholder="auto-generated if empty" value={form.slug} onChange={e => setForm(f => ({ ...f, slug: e.target.value }))} className={inputCls} />
              </div>
            </div>
            <div>
              <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Excerpt</label>
              <input type="text" placeholder="Short description" value={form.excerpt} onChange={e => setForm(f => ({ ...f, excerpt: e.target.value }))} className={inputCls} />
            </div>
            <div>
              <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Body</label>
              <textarea placeholder="Write your post..." value={form.body} onChange={e => setForm(f => ({ ...f, body: e.target.value }))} rows={12} className={inputCls + " resize-y leading-relaxed"} />
            </div>
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2.5 text-xs text-stone-500 dark:text-stone-400 cursor-pointer select-none">
                <div className="relative">
                  <input type="checkbox" checked={form.published} onChange={e => setForm(f => ({ ...f, published: e.target.checked }))} className="sr-only peer" />
                  <div className="w-8 h-[18px] bg-stone-200 dark:bg-white/10 rounded-full peer-checked:bg-leaf-500 transition-colors" />
                  <div className="absolute top-[3px] left-[3px] w-3 h-3 bg-white rounded-full peer-checked:translate-x-3.5 transition-transform shadow-sm" />
                </div>
                Publish
              </label>
              <div className="flex gap-2">
                {editingId && (
                  <button type="button" onClick={resetForm} className="px-4 py-2 rounded-lg border border-stone-200 dark:border-white/10 text-xs text-stone-500 dark:text-stone-400 hover:bg-stone-50 dark:hover:bg-white/5 transition-colors">
                    Cancel
                  </button>
                )}
                <button type="submit" className="px-5 py-2 rounded-lg bg-stone-800 dark:bg-white/90 text-white dark:text-stone-900 text-xs font-medium hover:bg-stone-900 dark:hover:bg-white transition-colors">
                  {editingId ? 'Save Changes' : 'Create Post'}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Posts table */}
      {posts.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-white/[0.02] border border-stone-100 dark:border-white/8 rounded-xl">
          <p className="text-stone-400 dark:text-stone-500 text-xs">No posts yet. Create your first one!</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-white/[0.02] border border-stone-100 dark:border-white/8 rounded-xl overflow-hidden">
          {/* Table header */}
          <div className="px-5 py-3 border-b border-stone-100 dark:border-white/5 bg-stone-50/50 dark:bg-white/[0.02]">
            <div className="flex items-center gap-4">
              <span className="text-[10px] text-stone-400 dark:text-stone-500 uppercase tracking-wider flex-1">Post</span>
              <span className="text-[10px] text-stone-400 dark:text-stone-500 uppercase tracking-wider w-20 text-center">Status</span>
              <span className="text-[10px] text-stone-400 dark:text-stone-500 uppercase tracking-wider w-20 text-center">Date</span>
              <span className="text-[10px] text-stone-400 dark:text-stone-500 uppercase tracking-wider w-28 text-right">Actions</span>
            </div>
          </div>

          {/* Table rows */}
          {posts.map((post, i) => (
            <div
              key={post.id}
              className={`px-5 py-3 flex items-center gap-4 transition-colors hover:bg-stone-50/50 dark:hover:bg-white/[0.02] ${
                i < posts.length - 1 ? 'border-b border-stone-50 dark:border-white/[0.03]' : ''
              } ${editingId === post.id ? 'bg-pine-50/30 dark:bg-pine-400/5' : ''}`}
            >
              {/* Post info */}
              <div className="flex items-center gap-3 min-w-0 flex-1">
                {post.cover_image ? (
                  <img src={post.cover_image} alt="" className="w-10 h-10 rounded-lg object-cover shrink-0" />
                ) : (
                  <div className="w-10 h-10 rounded-lg bg-stone-100 dark:bg-white/5 shrink-0 flex items-center justify-center text-stone-300 dark:text-stone-600 text-xs">
                    <PostsIcon />
                  </div>
                )}
                <div className="min-w-0">
                  <p className="text-xs font-medium text-stone-700 dark:text-stone-200 truncate">{post.title}</p>
                  <p className="text-[10px] text-stone-300 dark:text-stone-600 truncate">/{post.slug} · {readingTime(post.body)} read</p>
                </div>
              </div>

              {/* Status */}
              <div className="w-20 text-center">
                <button
                  onClick={() => handleTogglePublish(post)}
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium transition-colors ${
                    post.published
                      ? 'bg-green-50 dark:bg-green-400/10 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-400/20'
                      : 'bg-stone-50 dark:bg-white/5 text-stone-400 dark:text-stone-500 border border-stone-200 dark:border-white/10'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${post.published ? 'bg-green-500' : 'bg-stone-300 dark:bg-stone-600'}`} />
                  {post.published ? 'Live' : 'Draft'}
                </button>
              </div>

              {/* Date */}
              <div className="w-20 text-center">
                <span className="text-[10px] text-stone-400 dark:text-stone-500">{formatDate(post.created_at)}</span>
              </div>

              {/* Actions */}
              <div className="w-28 flex items-center justify-end gap-1">
                <button onClick={() => handleEdit(post)} className="px-2 py-1 rounded-md text-[10px] text-stone-400 dark:text-stone-500 hover:text-stone-700 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-white/10 transition-colors">
                  Edit
                </button>
                <button onClick={() => handleDelete(post.id)} className="px-2 py-1 rounded-md text-[10px] text-red-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-400/10 transition-colors">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Users Management View ───────────────────────────────────────────────────

function UsersView() {
  const { token } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-stone-800 dark:text-white tracking-tight">Users</h1>
        <p className="text-xs text-stone-400 dark:text-stone-500 mt-0.5">User management coming soon</p>
      </div>

      <div className="bg-white dark:bg-white/[0.02] border border-stone-100 dark:border-white/8 rounded-xl p-12 text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-stone-100 dark:bg-white/5 mb-4">
          <UsersIcon />
        </div>
        <p className="text-sm text-stone-500 dark:text-stone-400">User management is on the roadmap.</p>
        <p className="text-xs text-stone-300 dark:text-stone-600 mt-1">Check back in a future update.</p>
      </div>
    </div>
  )
}

// ── Admin Layout (Sidebar + Content) ────────────────────────────────────────

type AdminView = 'dashboard' | 'posts' | 'users'

function AdminLayout({ dark, setDark }: AdminProps) {
  const { user, logout } = useAuth()
  const [view, setView] = useState<AdminView>('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems: { id: AdminView; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
    { id: 'posts', label: 'Posts', icon: <PostsIcon /> },
    { id: 'users', label: 'Users', icon: <UsersIcon /> },
  ]

  return (
    <div className={dark ? 'dark' : ''}>
      <div className="min-h-screen bg-[#f5f5f4] dark:bg-[#0a0a0a] font-mono flex transition-colors duration-300">

        {/* Mobile overlay */}
        {sidebarOpen && (
          <div className="fixed inset-0 bg-black/30 z-30 lg:hidden" onClick={() => setSidebarOpen(false)} />
        )}

        {/* Sidebar */}
        <aside className={`fixed lg:sticky top-0 left-0 z-40 h-screen w-56 bg-[#fafaf9] dark:bg-[#0c0c0c] border-r border-stone-200 dark:border-white/5 flex flex-col transition-transform lg:transition-none duration-200 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}>
          {/* Logo */}
          <div className="px-5 py-5 border-b border-stone-100 dark:border-white/5">
            <a href="#/" className="flex items-center gap-2 no-underline">
              <span className="text-sm">🍍</span>
              <span className="text-stone-800 dark:text-stone-100 font-semibold text-sm tracking-tight">pynaple js</span>
            </a>
            <p className="text-[10px] text-stone-300 dark:text-stone-600 mt-1 pl-6">admin panel</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-0.5">
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => { setView(item.id); setSidebarOpen(false) }}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs transition-all ${
                  view === item.id
                    ? 'bg-stone-100 dark:bg-white/8 text-stone-800 dark:text-white font-medium'
                    : 'text-stone-500 dark:text-stone-400 hover:bg-stone-50 dark:hover:bg-white/5 hover:text-stone-700 dark:hover:text-stone-200'
                }`}
              >
                <span className={view === item.id ? 'text-stone-700 dark:text-stone-200' : 'text-stone-400 dark:text-stone-500'}>{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>

          {/* User + logout */}
          <div className="px-3 py-4 border-t border-stone-100 dark:border-white/5">
            <div className="flex items-center gap-3 px-3 mb-3">
              <div className="w-7 h-7 rounded-full bg-pine-100 dark:bg-pine-400/10 flex items-center justify-center text-pine-600 dark:text-pine-400 text-[10px] font-semibold shrink-0">
                {user?.name?.charAt(0)?.toUpperCase() || 'A'}
              </div>
              <div className="min-w-0">
                <p className="text-xs text-stone-700 dark:text-stone-200 truncate">{user?.name}</p>
                <p className="text-[10px] text-stone-400 dark:text-stone-500 truncate">{user?.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setDark(d => !d)}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-[11px] text-stone-400 dark:text-stone-500 hover:bg-stone-100 dark:hover:bg-white/5 hover:text-stone-600 dark:hover:text-stone-300 transition-colors"
              >
                {dark ? <SunIcon /> : <MoonIcon />}
                {dark ? 'Light' : 'Dark'}
              </button>
              <button
                onClick={logout}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-[11px] text-red-400 hover:bg-red-50 dark:hover:bg-red-400/10 hover:text-red-600 transition-colors"
              >
                <LogoutIcon />
                Sign out
              </button>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Top bar (mobile) */}
          <div className="sticky top-0 z-20 lg:hidden flex items-center justify-between px-5 py-3 bg-[#f5f5f4]/80 dark:bg-[#0a0a0a]/80 backdrop-blur-xl border-b border-stone-200 dark:border-white/5">
            <button
              onClick={() => setSidebarOpen(true)}
              className="flex items-center justify-center w-8 h-8 rounded-lg border border-stone-200 dark:border-white/10 text-stone-500 dark:text-stone-400"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
            </button>
            <span className="text-xs text-stone-500 dark:text-stone-400 capitalize">{view}</span>
            <div className="w-8" />
          </div>

          {/* Page content */}
          <main className="p-6 md:p-8 lg:p-10 max-w-4xl">
            {view === 'dashboard' && <DashboardView />}
            {view === 'posts' && <PostsView />}
            {view === 'users' && <UsersView />}
          </main>
        </div>
      </div>
    </div>
  )
}

// ── Main Export ──────────────────────────────────────────────────────────────

export default function Admin({ dark, setDark }: AdminProps) {
  return (
    <AuthProvider>
      <AdminInner dark={dark} setDark={setDark} />
    </AuthProvider>
  )
}

function AdminInner({ dark, setDark }: AdminProps) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className={dark ? 'dark' : ''}>
        <div className="min-h-screen bg-[#fafaf9] dark:bg-[#0c0c0c] font-mono flex items-center justify-center">
          <div className="text-xs text-stone-400 dark:text-stone-500">Loading...</div>
        </div>
      </div>
    )
  }

  if (!user) {
    return <LoginScreen dark={dark} setDark={setDark} />
  }

  return <AdminLayout dark={dark} setDark={setDark} />
}
