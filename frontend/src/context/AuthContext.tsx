import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { getCurrentUser, login as apiLogin, logout as apiLogout, register as apiRegister, type User } from '@/lib/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<{ error?: string }>
  register: (name: string, email: string, password: string) => Promise<{ error?: string }>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .finally(() => setLoading(false))
  }, [])

  const login = async (email: string, password: string) => {
    const result = await apiLogin(email, password)
    if (result.user) {
      setUser(result.user)
      return {}
    }
    return { error: result.error || 'Login failed' }
  }

  const register = async (name: string, email: string, password: string) => {
    const result = await apiRegister(name, email, password)
    if (result.user) {
      setUser(result.user)
      return {}
    }
    return { error: result.error || 'Registration failed' }
  }

  const logout = async () => {
    await apiLogout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

