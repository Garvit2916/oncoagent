import { useRef, type ReactNode } from 'react'
import {
  motion,
  useMotionValue,
  useSpring,
  useTransform,
  useReducedMotion,
} from 'motion/react'

type Props = {
  children: ReactNode
  className?: string
  intensity?: number
}

export default function TiltCard({ children, className, intensity = 10 }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const reduce = useReducedMotion()

  const rx = useMotionValue(0)
  const ry = useMotionValue(0)
  const gx = useMotionValue(50)
  const gy = useMotionValue(50)

  const srx = useSpring(rx, { stiffness: 150, damping: 18 })
  const sry = useSpring(ry, { stiffness: 150, damping: 18 })
  const sgx = useSpring(gx, { stiffness: 150, damping: 18 })
  const sgy = useSpring(gy, { stiffness: 150, damping: 18 })

  const glareX = useTransform(sgx, (v) => `${v}%`)
  const glareY = useTransform(sgy, (v) => `${v}%`)

  const onMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (reduce) return
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const px = (e.clientX - rect.left) / rect.width
    const py = (e.clientY - rect.top) / rect.height
    ry.set((px - 0.5) * intensity * 2)
    rx.set((0.5 - py) * intensity * 2)
    gx.set(px * 100)
    gy.set(py * 100)
  }

  const onLeave = () => {
    rx.set(0)
    ry.set(0)
    gx.set(50)
    gy.set(50)
  }

  return (
    <motion.div
      ref={ref}
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      style={{
        rotateX: srx,
        rotateY: sry,
        transformStyle: 'preserve-3d',
        perspective: 1000,
      }}
      className={className}
    >
      {children}
      <div
        className="pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `radial-gradient(420px circle at ${glareX} ${glareY}, rgba(255,255,255,0.16), transparent 60%)`,
        }}
      />
    </motion.div>
  )
}