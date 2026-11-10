import { useEffect, useRef } from 'react'
import {
  motion,
  useInView,
  useMotionValue,
  useSpring,
  useTransform,
  useReducedMotion,
} from 'motion/react'

type Props = {
  value: number
  decimals?: number
  prefix?: string
  suffix?: string
  className?: string
  duration?: number
}

export default function AnimatedNumber({
  value,
  decimals = 0,
  prefix = '',
  suffix = '',
  className,
  duration = 1.8,
}: Props) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  const reduce = useReducedMotion()
  const mv = useMotionValue(0)
  const spring = useSpring(mv, { stiffness: 60, damping: 22, mass: 0.9 })
  const text = useTransform(spring, (v) => `${prefix}${v.toFixed(decimals)}${suffix}`)

  useEffect(() => {
    if (inView) {
      mv.set(0)
      const start = performance.now()
      const tick = (now: number) => {
        const t = Math.min((now - start) / (duration * 1000), 1)
        const eased = 1 - Math.pow(1 - t, 4)
        mv.set(value * eased)
        if (t < 1) requestAnimationFrame(tick)
      }
      if (reduce) {
        mv.set(value)
      } else {
        requestAnimationFrame(tick)
      }
    }
  }, [inView, value, duration, reduce, mv])

  return (
    <motion.span ref={ref} className={className}>
      {text}
    </motion.span>
  )
}