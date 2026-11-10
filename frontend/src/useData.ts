import { useEffect, useState } from 'react'
import { api } from './api'

export function useData<T>(path: string) {
  const [state, setState] = useState<{ data?: T; error?: string; path?: string }>({})
  useEffect(() => {
    let active = true
    api<T>(path).then(data => { if (active) setState({ data, path }) },
      error => { if (active) setState({ error: error.message, path }) })
    return () => { active = false }
  }, [path])
  return state.path === path ? state : {}
}
