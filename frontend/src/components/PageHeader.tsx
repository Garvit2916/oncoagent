import { motion, useReducedMotion } from 'motion/react'
import type { ReactNode } from 'react'

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1]

type PageHeaderProps = {
  eyebrow: string
  title: ReactNode
  subtitle?: ReactNode
  children?: ReactNode
}

export default function PageHeader({ eyebrow, title, subtitle, children }: PageHeaderProps) {
  const reduce = useReducedMotion()
  return (
    <div className="text-center pt-6 pb-10">
      <motion.div
        initial={reduce ? false : { opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: EASE }}
      >
        <span className="glass-chip text-emerald-300 mb-6">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 animate-ping opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
          </span>
          {eyebrow}
        </span>
      </motion.div>

      <motion.h1
        initial={reduce ? false : { opacity: 0, y: 22 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.06, ease: EASE }}
        className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-[1.08]"
      >
        {title}
      </motion.h1>

      {subtitle && (
        <motion.p
          initial={reduce ? false : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.14, ease: EASE }}
          className="mt-5 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed"
        >
          {subtitle}
        </motion.p>
      )}

      {children && (
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.22, ease: EASE }}
          className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3"
        >
          {children}
        </motion.div>
      )}
    </div>
  )
}