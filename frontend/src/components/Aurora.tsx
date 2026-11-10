import type { CSSProperties } from 'react'
import { motion, useReducedMotion } from 'motion/react'

type Props = {
  className?: string
  intensity?: number
}

const LAYERS: { style: CSSProperties; cls: string }[] = [
  {
    cls: 'aurora-blob opacity-70',
    style: {
      background:
        'radial-gradient(circle at 35% 40%, rgba(45,212,191,0.24), transparent 62%)',
      top: '-14rem',
      left: '6%',
      width: '44rem',
      height: '44rem',
    },
  },
  {
    cls: 'aurora-blob slow opacity-60',
    style: {
      background:
        'radial-gradient(circle at 60% 35%, rgba(56,189,248,0.18), transparent 62%)',
      top: '-6rem',
      right: '-8rem',
      width: '38rem',
      height: '38rem',
    },
  },
  {
    cls: 'aurora-blob reverse opacity-50',
    style: {
      background:
        'radial-gradient(circle at 45% 60%, rgba(129,140,248,0.16), transparent 62%)',
      bottom: '-16rem',
      left: '24%',
      width: '42rem',
      height: '42rem',
    },
  },
]

export default function Aurora({ className = '', intensity = 1 }: Props) {
  const reduce = useReducedMotion()
  return (
    <motion.div
      aria-hidden
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
      initial={{ opacity: reduce ? 0.6 : 0 }}
      animate={{ opacity: reduce ? 0.6 : 0.9 * intensity }}
      transition={{ duration: 1.6, ease: [0.22, 1, 0.36, 1] }}
    >
      {LAYERS.map((l, i) => (
        <div
          key={i}
          className={`absolute rounded-full ${l.cls}`}
          style={{ animationPlayState: reduce ? 'paused' : 'running', ...l.style }}
        />
      ))}
    </motion.div>
  )
}