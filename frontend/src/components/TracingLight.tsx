import { useRef } from 'react'
import { motion, useScroll, useSpring, useTransform, useReducedMotion } from 'motion/react'

type Props = {
  className?: string
  offset?: string
}

/** Aceternity-style tracing beam — a light line that grows as you scroll the section. */
export default function TracingLight({ className = '', offset = 'left-6' }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const reduce = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end 88%'] })
  const scaleY = useSpring(scrollYProgress, { stiffness: 90, damping: 28 })
  const dotTop = useTransform(scaleY, (v) => `${v * 100}%`)

  return (
    <div
      ref={ref}
      aria-hidden
      className={`pointer-events-none absolute inset-0 ${className}`}
    >
      <div className={`absolute ${offset} top-0 bottom-0 w-px bg-white/[0.07]`} />
      <motion.div
        style={{ scaleY: reduce ? 1 : scaleY }}
        className={`absolute ${offset} top-0 bottom-0 w-px origin-top bg-gradient-to-b from-emerald-400/90 via-cyan-400/80 to-violet-400/70 shadow-[0_0_12px_0_rgba(52,211,153,0.35)]`}
      />
      <motion.span
        style={reduce ? undefined : { top: dotTop }}
        className={`absolute ${offset} -translate-x-[3px] top-0 h-[7px] w-[7px] rounded-full bg-emerald-300 shadow-[0_0_10px_2px_rgba(52,211,153,0.8)]`}
      />
    </div>
  )
}