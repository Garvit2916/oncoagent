import { motion } from 'motion/react'

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1]

export function SectionHeading({
  eyebrow,
  title,
  subtitle,
  align = 'center',
}: {
  eyebrow?: string
  title: string
  subtitle?: string
  align?: 'center' | 'left'
}) {
  const alignCls = align === 'center' ? 'text-center mx-auto' : 'text-left'
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.6, ease: EASE }}
      className={`max-w-3xl ${alignCls} mb-12`}
    >
      {eyebrow && (
        <span className="glass-chip mb-4 inline-flex text-emerald-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
          {eyebrow}
        </span>
      )}
      <h2 className="font-display text-3xl sm:text-4xl text-slate-100 tracking-tight font-bold">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-base sm:text-lg text-slate-400 leading-relaxed">{subtitle}</p>
      )}
    </motion.div>
  )
}