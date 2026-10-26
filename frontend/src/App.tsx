import { useEffect, useState } from 'react'
import { getPosts } from './api/posts'
import PostList from './components/PostList'
import TimeRangePicker from './components/TimeRangePicker'
import type { Post } from './types'
import './App.css'

interface Range {
  from: Date
  to: Date
}

// The outcome of fetching one specific range, tagged with that range.
type Result = { range: Range; posts: Post[] } | { range: Range; error: string }

function lastHour(): Range {
  const to = new Date()
  return { from: new Date(to.getTime() - 60 * 60 * 1000), to }
}

function App() {
  const [range, setRange] = useState<Range>(lastHour)
  const [result, setResult] = useState<Result | null>(null)

  useEffect(() => {
    // If the range changes before this request finishes, ignore its response,
    // otherwise a slow old request could overwrite the newer one.
    let cancelled = false
    getPosts(range.from, range.to)
      .then((posts) => {
        if (!cancelled) setResult({ range, posts })
      })
      .catch((e: unknown) => {
        if (!cancelled) setResult({ range, error: e instanceof Error ? e.message : String(e) })
      })
    return () => {
      cancelled = true
    }
  }, [range])

  // Derived, not stored: we're loading whenever the result isn't for the current range.
  const current = result?.range === range ? result : null

  return (
    <main className="app">
      <h1>Insta Lite</h1>
      <TimeRangePicker
        from={range.from}
        to={range.to}
        onChange={(from, to) => setRange({ from, to })}
      />

      {!current ? (
        <p className="status">Loading…</p>
      ) : 'error' in current ? (
        <p className="status error">Couldn't load posts: {current.error}</p>
      ) : (
        <PostList posts={current.posts} />
      )}
    </main>
  )
}

export default App
