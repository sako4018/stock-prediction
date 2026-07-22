const cache = new Map<string, { data: any; expiry: number }>()
const DEFAULT_TTL = 5 * 60 * 1000 // 5 minutes

export async function cachedFetch(url: string, ttl: number = DEFAULT_TTL): Promise<any> {
  const now = Date.now()
  const cached = cache.get(url)

  if (cached && cached.expiry > now) {
    return cached.data
  }

  const res = await fetch(url)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()

  cache.set(url, { data, expiry: now + ttl })
  return data
}

export function clearCache(pattern?: string) {
  if (pattern) {
    for (const key of cache.keys()) {
      if (key.includes(pattern)) cache.delete(key)
    }
  } else {
    cache.clear()
  }
}
