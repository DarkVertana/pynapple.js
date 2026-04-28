import React, { useState, useEffect, useRef } from 'react'
import Header from './header'

interface BlogProps {
  dark: boolean
  setDark: React.Dispatch<React.SetStateAction<boolean>>
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

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function readingTime(text: string): string {
  const words = text.trim().split(/\s+/).length
  const mins = Math.max(1, Math.ceil(words / 200))
  return `${mins} min read`
}

// ── Image Upload Hook ────────────────────────────────────────────────────────

function useImageUpload() {
  const [uploading, setUploading] = useState(false)

  const upload = async (file: File): Promise<string | null> => {
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      const data = await res.json()
      if (data.error) return null
      return data.url
    } catch {
      return null
    } finally {
      setUploading(false)
    }
  }

  return { upload, uploading }
}

// ── Cover Image Upload Component ─────────────────────────────────────────────

function CoverImageUpload({ value, onChange }: { value: string; onChange: (url: string) => void }) {
  const { upload, uploading } = useImageUpload()
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    const url = await upload(file)
    if (url) onChange(url)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
      />

      {value ? (
        <div className="relative group">
          <img
            src={value}
            alt="Cover"
            className="w-full h-40 object-cover rounded-lg border border-stone-200 dark:border-white/10"
          />
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 rounded-lg flex items-center justify-center gap-2 transition-opacity">
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="px-3 py-1.5 rounded-lg bg-white/20 text-white text-[11px] hover:bg-white/30 transition-colors"
            >
              Replace
            </button>
            <button
              type="button"
              onClick={() => onChange('')}
              className="px-3 py-1.5 rounded-lg bg-red-500/40 text-white text-[11px] hover:bg-red-500/60 transition-colors"
            >
              Remove
            </button>
          </div>
        </div>
      ) : (
        <div
          onDragOver={e => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className="w-full h-32 border-2 border-dashed border-stone-200 dark:border-white/10 rounded-lg flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-pine-400 dark:hover:border-pine-400/50 transition-colors"
        >
          {uploading ? (
            <span className="text-xs text-stone-400 dark:text-stone-500">Uploading...</span>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-stone-300 dark:text-stone-600">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </svg>
              <span className="text-[11px] text-stone-300 dark:text-stone-600">Drop image or click to upload</span>
            </>
          )}
        </div>
      )}
    </div>
  )
}

// ── Public Blog List ─────────────────────────────────────────────────────────

function BlogList({ onSelect }: { onSelect: (slug: string) => void }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/posts')
      .then(r => r.json())
      .then(d => { setPosts(d.posts || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-white dark:bg-white/5 border border-stone-100 dark:border-white/8 rounded-xl p-5 animate-pulse">
            <div className="h-40 bg-stone-100 dark:bg-white/5 rounded-lg mb-4" />
            <div className="h-3 bg-stone-100 dark:bg-white/5 rounded w-1/3 mb-3" />
            <div className="h-4 bg-stone-100 dark:bg-white/5 rounded w-2/3 mb-2" />
            <div className="h-3 bg-stone-100 dark:bg-white/5 rounded w-full" />
          </div>
        ))}
      </div>
    )
  }

  if (posts.length === 0) {
    return (
      <div className="text-center py-24">
        <div className="text-5xl mb-5 select-none">📝</div>
        <h2 className="text-sm font-semibold text-stone-700 dark:text-stone-200 mb-1">No posts yet</h2>
        <p className="text-stone-400 dark:text-stone-500 text-xs">Check back later for new content.</p>
      </div>
    )
  }

  // Featured first post, rest in grid
  const [featured, ...rest] = posts

  return (
    <div className="space-y-8">
      {/* Featured */}
      <button onClick={() => onSelect(featured.slug)} className="block w-full text-left group">
        <article className="bg-white dark:bg-white/5 border border-stone-100 dark:border-white/8 rounded-2xl overflow-hidden hover:border-stone-200 dark:hover:border-white/15 hover:shadow-md transition-all duration-300">
          {featured.cover_image && (
            <div className="h-56 overflow-hidden">
              <img
                src={featured.cover_image}
                alt={featured.title}
                className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-500"
              />
            </div>
          )}
          <div className="p-6">
            <div className="flex items-center gap-3 mb-3">
              <time className="text-[11px] text-stone-300 dark:text-stone-600">{formatDate(featured.created_at)}</time>
              <span className="text-[10px] text-stone-300 dark:text-stone-600">·</span>
              <span className="text-[11px] text-stone-300 dark:text-stone-600">{readingTime(featured.body)}</span>
            </div>
            <h2 className="text-base font-semibold text-stone-800 dark:text-white mb-2 group-hover:text-pine-600 dark:group-hover:text-pine-400 transition-colors">
              {featured.title}
            </h2>
            {featured.excerpt && (
              <p className="text-stone-400 dark:text-stone-500 text-xs leading-relaxed line-clamp-2">{featured.excerpt}</p>
            )}
          </div>
        </article>
      </button>

      {/* Grid */}
      {rest.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {rest.map(post => (
            <button key={post.id} onClick={() => onSelect(post.slug)} className="block w-full text-left group">
              <article className="bg-white dark:bg-white/5 border border-stone-100 dark:border-white/8 rounded-xl overflow-hidden hover:border-stone-200 dark:hover:border-white/15 hover:shadow-sm transition-all duration-200 h-full">
                {post.cover_image && (
                  <div className="h-36 overflow-hidden">
                    <img src={post.cover_image} alt={post.title} className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-500" />
                  </div>
                )}
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <time className="text-[10px] text-stone-300 dark:text-stone-600">{formatDate(post.created_at)}</time>
                    <span className="text-[10px] text-stone-300 dark:text-stone-600">·</span>
                    <span className="text-[10px] text-stone-300 dark:text-stone-600">{readingTime(post.body)}</span>
                  </div>
                  <h3 className="text-xs font-semibold text-stone-800 dark:text-white mb-1 group-hover:text-pine-600 dark:group-hover:text-pine-400 transition-colors line-clamp-2">
                    {post.title}
                  </h3>
                  {post.excerpt && (
                    <p className="text-stone-400 dark:text-stone-500 text-[11px] leading-relaxed line-clamp-2">{post.excerpt}</p>
                  )}
                </div>
              </article>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Single Post View ─────────────────────────────────────────────────────────

function PostView({ slug, onBack }: { slug: string; onBack: () => void }) {
  const [post, setPost] = useState<Post | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/posts/${slug}`)
      .then(r => r.json())
      .then(d => { setPost(d.post || null); setLoading(false) })
      .catch(() => setLoading(false))
  }, [slug])

  if (loading) return (
    <div className="max-w-2xl animate-pulse">
      <div className="h-3 bg-stone-100 dark:bg-white/5 rounded w-20 mb-8" />
      <div className="h-64 bg-stone-100 dark:bg-white/5 rounded-2xl mb-6" />
      <div className="h-5 bg-stone-100 dark:bg-white/5 rounded w-2/3 mb-4" />
      <div className="space-y-2">
        <div className="h-3 bg-stone-100 dark:bg-white/5 rounded w-full" />
        <div className="h-3 bg-stone-100 dark:bg-white/5 rounded w-5/6" />
        <div className="h-3 bg-stone-100 dark:bg-white/5 rounded w-4/6" />
      </div>
    </div>
  )
  if (!post) return <p className="text-red-400 text-sm">Post not found.</p>

  return (
    <article className="max-w-2xl">
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-xs text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300 mb-8 transition-colors group"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-hover:-translate-x-0.5 transition-transform"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        back to blog
      </button>

      {post.cover_image && (
        <div className="mb-8 -mx-2 sm:-mx-6">
          <img
            src={post.cover_image}
            alt={post.title}
            className="w-full h-64 sm:h-80 object-cover rounded-2xl"
          />
        </div>
      )}

      <div className="flex items-center gap-3 mb-4">
        <time className="text-[11px] text-stone-300 dark:text-stone-600">{formatDate(post.created_at)}</time>
        <span className="text-[10px] text-stone-300 dark:text-stone-600">·</span>
        <span className="text-[11px] text-stone-300 dark:text-stone-600">{readingTime(post.body)}</span>
      </div>

      <h1 className="text-2xl font-semibold text-stone-800 dark:text-white mb-4 tracking-tight leading-tight">
        {post.title}
      </h1>

      {post.excerpt && (
        <p className="text-stone-400 dark:text-stone-500 text-sm mb-8 leading-relaxed border-l-2 border-pine-300 dark:border-pine-500/40 pl-4 italic">
          {post.excerpt}
        </p>
      )}

      <div className="text-stone-600 dark:text-stone-400 text-[13px] leading-[1.85] whitespace-pre-wrap">
        {post.body}
      </div>

      {/* Bottom nav */}
      <div className="mt-12 pt-6 border-t border-stone-100 dark:border-white/5">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300 transition-colors group"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-hover:-translate-x-0.5 transition-transform"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
          all posts
        </button>
      </div>
    </article>
  )
}

// ── Admin Panel ──────────────────────────────────────────────────────────────

const EMPTY_FORM = { title: '', slug: '', excerpt: '', body: '', cover_image: '', published: false }

function AdminPanel() {
  const [posts, setPosts] = useState<Post[]>([])
  const [form, setForm] = useState<typeof EMPTY_FORM>({ ...EMPTY_FORM })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [message, setMessage] = useState<{ text: string; type: 'ok' | 'err' }>({ text: '', type: 'ok' })

  const loadPosts = () => {
    fetch('/api/posts/all')
      .then(r => r.json())
      .then(d => setPosts(d.posts || []))
  }

  useEffect(() => { loadPosts() }, [])

  const flash = (text: string, type: 'ok' | 'err' = 'ok') => {
    setMessage({ text, type })
    setTimeout(() => setMessage({ text: '', type: 'ok' }), 3000)
  }

  const resetForm = () => {
    setForm({ ...EMPTY_FORM })
    setEditingId(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.title.trim()) return flash('Title is required', 'err')

    try {
      if (editingId) {
        const res = await fetch(`/api/posts/${editingId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form),
        })
        const data = await res.json()
        if (data.error) return flash(data.error, 'err')
        flash('Post updated')
      } else {
        const res = await fetch('/api/posts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form),
        })
        const data = await res.json()
        if (data.error) return flash(data.error, 'err')
        flash('Post created')
      }
      resetForm()
      loadPosts()
    } catch {
      flash('Something went wrong', 'err')
    }
  }

  const handleEdit = (post: Post) => {
    setForm({
      title: post.title,
      slug: post.slug,
      excerpt: post.excerpt,
      body: post.body,
      cover_image: post.cover_image,
      published: post.published,
    })
    setEditingId(post.id)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleDelete = async (id: number) => {
    await fetch(`/api/posts/${id}`, { method: 'DELETE' })
    flash('Post deleted')
    if (editingId === id) resetForm()
    loadPosts()
  }

  const handleTogglePublish = async (post: Post) => {
    await fetch(`/api/posts/${post.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ published: !post.published }),
    })
    loadPosts()
  }

  const inputCls = "w-full bg-white dark:bg-[#111] border border-stone-200 dark:border-white/10 rounded-lg px-3 py-2.5 text-xs text-stone-700 dark:text-stone-300 placeholder:text-stone-300 dark:placeholder:text-stone-600 focus:outline-none focus:ring-2 focus:ring-pine-400/30 focus:border-pine-400 dark:focus:border-pine-400/50 transition-all"

  return (
    <div className="space-y-8">
      {/* Form */}
      <div className="bg-white dark:bg-white/[0.02] border border-stone-100 dark:border-white/8 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-stone-700 dark:text-stone-200 mb-5">
          {editingId ? 'Edit Post' : 'New Post'}
        </h2>

        {message.text && (
          <div className={`mb-4 px-3 py-2.5 rounded-lg text-xs ${
            message.type === 'ok'
              ? 'bg-leaf-400/10 border border-leaf-400/20 text-leaf-700 dark:text-leaf-400'
              : 'bg-red-50 dark:bg-red-400/10 border border-red-200 dark:border-red-400/20 text-red-600 dark:text-red-400'
          }`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Cover image */}
          <div>
            <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Cover Image</label>
            <CoverImageUpload
              value={form.cover_image}
              onChange={url => setForm(f => ({ ...f, cover_image: url }))}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Title</label>
              <input
                type="text"
                placeholder="Post title"
                value={form.title}
                onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                className={inputCls}
              />
            </div>
            <div>
              <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Slug</label>
              <input
                type="text"
                placeholder="auto-generated if empty"
                value={form.slug}
                onChange={e => setForm(f => ({ ...f, slug: e.target.value }))}
                className={inputCls}
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Excerpt</label>
            <input
              type="text"
              placeholder="A short description for the blog listing"
              value={form.excerpt}
              onChange={e => setForm(f => ({ ...f, excerpt: e.target.value }))}
              className={inputCls}
            />
          </div>

          <div>
            <label className="block text-[11px] text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">Body</label>
            <textarea
              placeholder="Write your post content here..."
              value={form.body}
              onChange={e => setForm(f => ({ ...f, body: e.target.value }))}
              rows={14}
              className={inputCls + " resize-y leading-relaxed"}
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center gap-2.5 text-xs text-stone-500 dark:text-stone-400 cursor-pointer select-none">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={form.published}
                  onChange={e => setForm(f => ({ ...f, published: e.target.checked }))}
                  className="sr-only peer"
                />
                <div className="w-8 h-[18px] bg-stone-200 dark:bg-white/10 rounded-full peer-checked:bg-leaf-500 transition-colors" />
                <div className="absolute top-[3px] left-[3px] w-3 h-3 bg-white rounded-full peer-checked:translate-x-3.5 transition-transform shadow-sm" />
              </div>
              Publish
            </label>

            <div className="flex gap-2">
              {editingId && (
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 rounded-lg border border-stone-200 dark:border-white/10 text-xs text-stone-500 dark:text-stone-400 hover:bg-stone-50 dark:hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                className="px-5 py-2 rounded-lg bg-stone-800 dark:bg-white/90 text-white dark:text-stone-900 text-xs font-medium hover:bg-stone-900 dark:hover:bg-white transition-colors"
              >
                {editingId ? 'Save Changes' : 'Create Post'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Posts table */}
      <div>
        <h2 className="text-sm font-semibold text-stone-700 dark:text-stone-200 mb-4">
          All Posts <span className="text-stone-300 dark:text-stone-600 font-normal">({posts.length})</span>
        </h2>

        {posts.length === 0 ? (
          <div className="text-center py-12 bg-white dark:bg-white/[0.02] border border-stone-100 dark:border-white/8 rounded-xl">
            <p className="text-stone-400 dark:text-stone-500 text-xs">No posts yet. Create your first one above!</p>
          </div>
        ) : (
          <div className="space-y-2">
            {posts.map(post => (
              <div
                key={post.id}
                className={`flex items-center gap-4 p-3 rounded-xl border transition-all ${
                  editingId === post.id
                    ? 'border-pine-300 dark:border-pine-400/30 bg-pine-50/50 dark:bg-pine-400/5 shadow-sm'
                    : 'border-stone-100 dark:border-white/8 bg-white dark:bg-white/[0.02] hover:bg-stone-50/50 dark:hover:bg-white/[0.03]'
                }`}
              >
                {/* Thumbnail */}
                {post.cover_image ? (
                  <img src={post.cover_image} alt="" className="w-12 h-12 rounded-lg object-cover shrink-0" />
                ) : (
                  <div className="w-12 h-12 rounded-lg bg-stone-100 dark:bg-white/5 shrink-0 flex items-center justify-center text-stone-300 dark:text-stone-600 text-sm">
                    📝
                  </div>
                )}

                {/* Info */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-medium text-stone-700 dark:text-stone-200 truncate">{post.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-stone-300 dark:text-stone-600">/{post.slug}</span>
                    <span className="text-[10px] text-stone-300 dark:text-stone-600">·</span>
                    <span className="text-[10px] text-stone-300 dark:text-stone-600">{formatDate(post.created_at)}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => handleTogglePublish(post)}
                    className={`px-2 py-1 rounded text-[10px] transition-colors ${
                      post.published
                        ? 'text-leaf-600 dark:text-leaf-400 hover:bg-leaf-50 dark:hover:bg-leaf-400/10'
                        : 'text-stone-400 dark:text-stone-500 hover:bg-stone-100 dark:hover:bg-white/10'
                    }`}
                  >
                    {post.published ? 'published' : 'draft'}
                  </button>
                  <button
                    onClick={() => handleEdit(post)}
                    className="px-2 py-1 rounded text-[10px] text-stone-400 dark:text-stone-500 hover:text-stone-700 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-white/10 transition-colors"
                  >
                    edit
                  </button>
                  <button
                    onClick={() => handleDelete(post.id)}
                    className="px-2 py-1 rounded text-[10px] text-red-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-400/10 transition-colors"
                  >
                    delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main Blog Page ───────────────────────────────────────────────────────────

export default function Blog({ dark, setDark }: BlogProps) {
  const [view, setView] = useState<'list' | 'post' | 'admin'>('list')
  const [selectedSlug, setSelectedSlug] = useState('')

  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash
      if (hash === '#/blog/admin') {
        setView('admin')
      } else if (hash.startsWith('#/blog/') && hash !== '#/blog') {
        const slug = hash.replace('#/blog/', '')
        if (slug && slug !== 'admin') {
          setSelectedSlug(slug)
          setView('post')
        }
      } else {
        setView('list')
        setSelectedSlug('')
      }
    }
    handleHash()
    window.addEventListener('hashchange', handleHash)
    return () => window.removeEventListener('hashchange', handleHash)
  }, [])

  const navigate = (target: string) => {
    window.location.hash = target
  }

  return (
    <div className={dark ? 'dark' : ''}>
      <div className="min-h-screen bg-[#fafaf9] dark:bg-[#0c0c0c] font-mono flex flex-col transition-colors duration-300">

        <Header
          dark={dark}
          setDark={setDark}
          breadcrumb={<span className="text-stone-400 dark:text-stone-500 text-xs">blog</span>}
        />

        <main className="flex-1 px-6 md:px-10 py-8 max-w-3xl mx-auto w-full">

          {/* Tab bar */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-1 bg-stone-100/60 dark:bg-white/5 rounded-lg p-0.5">
              <button
                onClick={() => navigate('#/blog')}
                className={`px-3.5 py-1.5 rounded-md text-xs transition-all ${
                  view !== 'admin'
                    ? 'text-stone-700 dark:text-stone-200 bg-white dark:bg-white/10 shadow-sm'
                    : 'text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300'
                }`}
              >
                Posts
              </button>
              <button
                onClick={() => navigate('#/blog/admin')}
                className={`px-3.5 py-1.5 rounded-md text-xs transition-all ${
                  view === 'admin'
                    ? 'text-stone-700 dark:text-stone-200 bg-white dark:bg-white/10 shadow-sm'
                    : 'text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300'
                }`}
              >
                Admin
              </button>
            </div>
          </div>

          {/* Content */}
          {view === 'admin' && <AdminPanel />}
          {view === 'list' && (
            <BlogList onSelect={(slug) => navigate(`#/blog/${slug}`)} />
          )}
          {view === 'post' && selectedSlug && (
            <PostView slug={selectedSlug} onBack={() => navigate('#/blog')} />
          )}

        </main>
      </div>
    </div>
  )
}
