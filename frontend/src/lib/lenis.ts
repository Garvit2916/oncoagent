import Lenis from 'lenis'

let lenis: Lenis | null = null

export function initLenis(): Lenis | null {
  if (typeof window === 'undefined') return null
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return null
  if (lenis) return lenis
  lenis = new Lenis({ lerp: 0.09, smoothWheel: true })
  return lenis
}

export function getLenis(): Lenis | null {
  return lenis
}

export function resetScroll() {
  const l = getLenis()
  if (l) {
    l.scrollTo(0, { immediate: true })
  } else {
    const html = document.documentElement
    const prev = html.style.scrollBehavior
    html.style.scrollBehavior = 'auto'
    window.scrollTo(0, 0)
    html.scrollTop = 0
    document.body.scrollTop = 0
    html.style.scrollBehavior = prev
  }
}

export function destroyLenis() {
  lenis?.destroy()
  lenis = null
}