import type { Post } from '../types'
import { MOCK_POSTS } from './mock'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// The only place in the frontend that talks to the backend.
// Takes Dates (not input strings) so callers never deal with formats or timezones;
// toISOString() always produces UTC, e.g. 2026-10-25T13:00:00.000Z.
export async function getPosts(from: Date, to: Date): Promise<Post[]> {
  if (USE_MOCK) {
    return getMockPosts(from, to)
  }

  const params = new URLSearchParams({ from: from.toISOString(), to: to.toISOString() })
  const res = await fetch(`${API_URL}/posts?${params}`)
  if (!res.ok) {
    throw new Error(`GET /posts failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

// Behaves like the real backend: filters by range, newest first, with some latency
// so loading states are visible during development.
async function getMockPosts(from: Date, to: Date): Promise<Post[]> {
  await new Promise((resolve) => setTimeout(resolve, 300))
  const fromMs = from.getTime()
  const toMs = to.getTime()
  return MOCK_POSTS
    .filter((p) => {
      const t = Date.parse(p.taken_at)
      return t >= fromMs && t <= toMs
    })
    .sort((a, b) => Date.parse(b.taken_at) - Date.parse(a.taken_at))
}
