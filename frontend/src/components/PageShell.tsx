import { motion, useReducedMotion } from 'motion/react'
import type { ReactNode } from 'react'

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1]

export default function PageShell({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion()
  return (
    <motion.main
      initial={reduce ? false : { opacity: 0, y: 18, scale: 0.995 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.995 }}
      transition={{ duration: 0.32, ease: EASE }}
      className="themed relative z-10 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-12"
    >
      {children}
    </motion.main>
  )
}