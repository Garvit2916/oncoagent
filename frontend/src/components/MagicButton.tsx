import { useRef, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  motion,
  useMotionValue,
  useSpring,
  useReducedMotion,
} from 'motion/react'

type Props = {
  children: ReactNode
  to?: string
  onClick?: () => void
  className?: string
  magnetic?: boolean
}

export default function MagicButton({
  children,
  to,
  onClick,
  className = '',
  magnetic = true,
}: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const reduce = useReducedMotion()
  const mx = useMotionValue(0)
  const my = useMotionValue(0)
  const sx = useSpring(mx, { stiffness: 250, damping: 20 })
  const sy = useSpring(my, { stiffness: 250, damping: 20 })

  const onMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!magnetic || reduce) return
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const dx = e.clientX - (rect.left + rect.width / 2)
    const dy = e.clientY - (rect.top + rect.height / 2)
    mx.set(dx * 0.3)
    my.set(dy * 0.35)
  }

  const onLeave = () => {
    mx.set(0)
    my.set(0)
  }

  const inner = to ? (
    <Link to={to} className={className} onClick={onClick}>
      {children}
    </Link>
  ) : (
    <button className={className} onClick={onClick}>
      {children}
    </button>
  )

  return (
    <motion.div
      ref={ref}
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      style={{ x: sx, y: sy }}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.95 }}
      className="inline-block"
    >
      {inner}
    </motion.div>
  )
}