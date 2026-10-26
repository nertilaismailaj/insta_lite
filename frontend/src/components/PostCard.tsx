import { useState } from 'react'
import type { Post } from '../types'

interface Props {
  post: Post
}

export default function PostCard({ post }: Props) {
  // Instagram CDN URLs are signed and expire, so a broken image is an expected state.
  const [imageFailed, setImageFailed] = useState(false)

  return (
    <article className="post-card">
      <header>
        <span className="username">@{post.username}</span>
        <time dateTime={post.taken_at}>{new Date(post.taken_at).toLocaleString()}</time>
      </header>

      {post.media_url && !imageFailed ? (
        <img src={post.media_url} alt="" loading="lazy" onError={() => setImageFailed(true)} />
      ) : (
        <div className="image-placeholder">Image unavailable</div>
      )}

      {post.caption && <p className="caption">{post.caption}</p>}

      <a href={post.permalink} target="_blank" rel="noopener noreferrer">
        Open in Instagram
      </a>
    </article>
  )
}
