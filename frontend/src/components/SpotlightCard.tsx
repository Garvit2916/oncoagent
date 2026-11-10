import { useRef, type MouseEvent as ReactMouseEvent, type ReactNode } from 'react'

type Props = {
  className?: string
  children: ReactNode
}

/** Aceternity-style card spotlight — a soft, professional light that follows the cursor. */
export default function SpotlightCard({ className = '', children }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const onMove = (e: ReactMouseEvent) => {
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    el.style.setProperty('--mx', `${e.clientX - r.left}px`)
    el.style.setProperty('--my', `${e.clientY - r.top}px`)
  }
  return (
    <div ref={ref} onMouseMove={onMove} className={`group/spot relative overflow-hidden ${className}`}>
      {/* soft neutral light */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 z-[1] opacity-0 transition-opacity duration-500 group-hover/spot:opacity-100"
        style={{
          background:
            'radial-gradient(420px circle at var(--mx, 50%) var(--my, 50%), rgba(148, 233, 216, 0.10), transparent 65%)',
        }}
      />
      {/* hairline top highlight on hover */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-300/50 to-transparent opacity-0 transition-opacity duration-500 group-hover/spot:opacity-100"
      />
      <div className="relative z-[2] h-full">{children}</div>
    </div>
  )
}