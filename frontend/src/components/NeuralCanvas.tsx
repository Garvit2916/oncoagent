import { useEffect, useRef } from 'react'

type Node = {
  x: number
  y: number
  vx: number
  vy: number
  r: number
  color: string
}

const PALETTE = [
  '52, 211, 153',
  '34, 211, 238',
  '167, 139, 250',
  '94, 234, 212',
]

function makeNodes(w: number, h: number): Node[] {
  const target = Math.min(110, Math.max(40, Math.floor((w * h) / 26000)))
  const nodes: Node[] = []
  for (let i = 0; i < target; i++) {
    nodes.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      r: Math.random() * 1.8 + 0.8,
      color: PALETTE[Math.floor(Math.random() * PALETTE.length)],
    })
  }
  return nodes
}

export default function NeuralCanvas() {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let dpr = Math.min(window.devicePixelRatio || 1, 2)
    let w = 0
    let h = 0
    let nodes: Node[] = []
    const pointer = { x: -9999, y: -9999 }
    let raf = 0

    const resize = () => {
      w = window.innerWidth
      h = window.innerHeight
      dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      nodes = makeNodes(w, h)
      if (reduced) draw(0)
    }

    const draw = (t: number) => {
      ctx.clearRect(0, 0, w, h)
      const linkDist = Math.min(150, Math.max(90, w * 0.09))
      const pointerDist = 210

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i]
        n.x += n.vx
        n.y += n.vy
        if (n.x < -20) n.x = w + 20
        if (n.x > w + 20) n.x = -20
        if (n.y < -20) n.y = h + 20
        if (n.y > h + 20) n.y = -20

        const dx = pointer.x - n.x
        const dy = pointer.y - n.y
        const d = Math.hypot(dx, dy)
        if (d < pointerDist) {
          n.x += (dx / d) * 0.25
          n.y += (dy / d) * 0.25
        }

        const pulse = 0.55 + 0.45 * Math.sin(t / 900 + i)
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${n.color}, ${0.35 * pulse})`
        ctx.fill()

        for (let j = i + 1; j < nodes.length; j++) {
          const m = nodes[j]
          const dist = Math.hypot(m.x - n.x, m.y - n.y)
          if (dist < linkDist) {
            const alpha = (1 - dist / linkDist) * 0.14
            ctx.strokeStyle = `rgba(148, 163, 184, ${alpha})`
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.moveTo(n.x, n.y)
            ctx.lineTo(m.x, m.y)
            ctx.stroke()
          }
        }
      }
    }

    const loop = (t: number) => {
      draw(t)
      if (!reduced) raf = requestAnimationFrame(loop)
    }

    const onPointer = (e: PointerEvent) => {
      pointer.x = e.clientX
      pointer.y = e.clientY
    }
    const onLeave = () => {
      pointer.x = -9999
      pointer.y = -9999
    }
    const onVis = () => {
      if (document.hidden) {
        cancelAnimationFrame(raf)
      } else if (!reduced) {
        raf = requestAnimationFrame(loop)
      }
    }

    resize()
    window.addEventListener('resize', resize)
    window.addEventListener('pointermove', onPointer, { passive: true })
    window.addEventListener('pointerleave', onLeave)
    document.addEventListener('visibilitychange', onVis)

    if (reduced) {
      draw(0)
    } else {
      raf = requestAnimationFrame(loop)
    }

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointermove', onPointer)
      window.removeEventListener('pointerleave', onLeave)
      document.removeEventListener('visibilitychange', onVis)
    }
  }, [])

  return <canvas ref={ref} className="neural-bg" aria-hidden="true" />
}