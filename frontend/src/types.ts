// Mirrors the backend API contract (GET /posts). Timestamps are UTC ISO strings.
export interface Post {
  id: number
  external_id: string
  username: string
  taken_at: string
  caption: string | null
  media_url: string | null
  permalink: string
}
