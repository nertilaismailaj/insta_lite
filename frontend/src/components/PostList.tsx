import type { Post } from '../types'
import PostCard from './PostCard'

interface Props {
  posts: Post[]
}

export default function PostList({ posts }: Props) {
  if (posts.length === 0) {
    return <p className="status">No posts in this range.</p>
  }

  return (
    <div className="post-list">
      {posts.map((post) => (
        <PostCard key={post.external_id} post={post} />
      ))}
      {/* A deliberate end: no infinite scroll, no "load more". */}
      <p className="status">You're all caught up.</p>
    </div>
  )
}
