const API_BASE = '/api'

interface User {
  id: number
  name: string
  email: string
}

interface AuthResponse {
  user?: User
  error?: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

// Get CSRF token from cookie
function getCsrfToken(): string {
  const name = 'csrf_token='
  const decodedCookie = decodeURIComponent(document.cookie)
  const cookies = decodedCookie.split(';')
  for (let cookie of cookies) {
    cookie = cookie.trim()
    if (cookie.indexOf(name) === 0) {
      return cookie.substring(name.length)
    }
  }
  return ''
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  })
  return response.json()
}

export async function register(name: string, email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    credentials: 'include',
    body: JSON.stringify({ name, email, password }),
  })
  return response.json()
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE}/logout`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
    },
    credentials: 'include',
  })
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    const response = await fetch(`${API_BASE}/me`, {
      credentials: 'include',
    })
    if (response.ok) {
      return response.json()
    }
    return null
  } catch {
    return null
  }
}

export async function getChatHistory(): Promise<ChatMessage[]> {
  const response = await fetch(`${API_BASE}/history`, {
    credentials: 'include',
  })
  if (response.ok) {
    return response.json()
  }
  return []
}

export async function* streamChat(query: string, sessionId: string): AsyncGenerator<string> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    credentials: 'include',
    body: JSON.stringify({ query, session_id: sessionId }),
  })

  if (!response.ok) {
    throw new Error('Failed to send message')
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('No response body')
  }

  const decoder = new TextDecoder()
  
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    
    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split('\n').filter(line => line.trim())
    
    for (const line of lines) {
      try {
        const data = JSON.parse(line)
        if (data.error) {
          throw new Error(data.error)
        }
        if (data.answer) {
          yield data.answer
        }
      } catch (e) {
        if (e instanceof SyntaxError) continue
        throw e
      }
    }
  }
}

export type { User, ChatMessage }

