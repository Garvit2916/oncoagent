import { useEffect, useState } from 'react'
import {
  motion,
  useMotionValue,
  useSpring,
  useReducedMotion,
} from 'motion/react'

export default function CursorGlow() {
  const [enabled, setEnabled] = useState(false)
  const reduce = useReducedMotion()
  const x = useMotionValue(-9999)
  const y = useMotionValue(-9999)
  const sx = useSpring(x, { stiffness: 55, damping: 20, mass: 0.8 })
  const sy = useSpring(y, { stiffness: 55, damping: 20, mass: 0.8 })

  useEffect(() => {
    if (reduce) return
    const coarse = window.matchMedia('(pointer: coarse)').matches
    if (coarse) return
    setEnabled(true)

    const move = (e: PointerEvent) => {
      x.set(e.clientX)
      y.set(e.clientY)
    }
    window.addEventListener('pointermove', move, { passive: true })
    return () => window.removeEventListener('pointermove', move)
  }, [x, y, reduce])

  if (!enabled) return null

  return (
    <motion.div
      className="cursor-glow"
      style={{ left: sx, top: sy }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      aria-hidden="true"
    />
  )
}