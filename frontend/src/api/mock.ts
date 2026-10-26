import type { Post } from '../types'

const USERNAMES = ['anna', 'marco', 'sofia', 'liam', 'elena', 'noah']

// Generated relative to "now" so presets like "Last hour" always have data.
// One post every 20 minutes over the last 24 hours.
function generateMockPosts(): Post[] {
  const now = Date.now()
  const posts: Post[] = []
  for (let i = 0; i < 72; i++) {
    const shortcode = `MOCK${i.toString().padStart(3, '0')}`
    posts.push({
      id: i + 1,
      external_id: shortcode,
      username: USERNAMES[i % USERNAMES.length],
      taken_at: new Date(now - i * 20 * 60 * 1000).toISOString(),
      caption: `Mock post #${i + 1}`,
      media_url: `https://picsum.photos/seed/${shortcode}/600/600`,
      permalink: `https://www.instagram.com/p/${shortcode}/`,
    })
  }
  return posts
}

export const MOCK_POSTS = generateMockPosts()
