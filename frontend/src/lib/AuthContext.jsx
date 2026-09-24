import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from './supabase'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(undefined) // undefined = loading

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    const { data: listener } = supabase.auth.onAuthStateChange((_e, s) => setSession(s))
    return () => listener.subscription.unsubscribe()
  }, [])

  const signUp = async (email, password) => {
    const res = await supabase.auth.signUp({ email, password })
    if (res.data?.user) {
      // Ensure a profile exists for the new user to satisfy foreign key constraints
      const { error } = await supabase
        .from('profiles')
        .upsert({ id: res.data.user.id, username: email.split('@')[0] }, { onConflict: 'id' })
      if (error) console.error('Failed to create profile row:', error)
    }
    return res
  }

  const signIn = async (email, password) => {
    const res = await supabase.auth.signInWithPassword({ email, password })
    if (res.data?.user) {
      // Ensure a profile exists for the user to satisfy foreign key constraints
      const { error } = await supabase
        .from('profiles')
        .upsert({ id: res.data.user.id, username: email.split('@')[0] }, { onConflict: 'id' })
      if (error) console.error('Failed to create profile row:', error)
    }
    return res
  }

  const signOut = () => supabase.auth.signOut()

  return (
    <AuthContext.Provider value={{ session, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}