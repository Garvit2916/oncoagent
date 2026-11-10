import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { resetScroll } from '../lib/lenis'

export default function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    const t = setTimeout(() => resetScroll(), 70)
    return () => clearTimeout(t)
  }, [pathname])

  return null
}