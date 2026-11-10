import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { AnimatePresence, motion, useScroll, useSpring } from 'motion/react'
import { Activity, HeartPulse, FileText, Stethoscope, Shield, Sparkles } from 'lucide-react'
import Home from './pages/Home'
import Imaging from './pages/Imaging'
import Symptoms from './pages/Symptoms'
import Literature from './pages/Literature'
import Consultation from './pages/Consultation'
import Results from './pages/Results'
import NeuralCanvas from './components/NeuralCanvas'
import CursorGlow from './components/CursorGlow'
import PageShell from './components/PageShell'
import ScrollToTop from './components/ScrollToTop'
import { initLenis, destroyLenis } from './lib/lenis'

const navLinks = [
  { to: '/', label: 'Home', icon: Activity },
  { to: '/imaging', label: 'Image Analysis', icon: HeartPulse },
  { to: '/symptoms', label: 'Symptom Check', icon: Stethoscope },
  { to: '/literature', label: 'Research', icon: FileText },
  { to: '/consultation', label: 'Full Consultation', icon: Shield },
]

function ScrollProgress() {
  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, { stiffness: 120, damping: 30, restDelta: 0.001 })
  return <motion.div className="scroll-progress" style={{ scaleX }} />
}

function SmoothScroll() {
  useEffect(() => {
    const lenis = initLenis()
    if (!lenis) return
    let raf = 0
    const loop = (time: number) => {
      lenis.raf(time)
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => {
      cancelAnimationFrame(raf)
      destroyLenis()
    }
  }, [])
  return null
}

function Logo() {
  return (
    <motion.div
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.96 }}
      className="flex items-center gap-3 select-none"
    >
      <div className="relative w-10 h-10 shrink-0">
        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-emerald-400 via-teal-300 to-violet-500 opacity-80 blur-[3px]" />
        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-emerald-400 via-teal-300 to-violet-500 flex items-center justify-center">
          <Activity className="w-5 h-5 text-[#05070d] font-bold" strokeWidth={2.6} />
        </div>
        <div className="absolute inset-0 rounded-xl border border-white/20 animate-pulse-ring" />
      </div>
      <div className="leading-none">
        <div className="font-display text-lg font-bold text-white tracking-tight">
          Onco<span className="gradient-text">Agent</span>
        </div>
        <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-slate-500 mt-1">
          Diagnostic Mosaic
        </div>
      </div>
    </motion.div>
  )
}

function NavLinks() {
  return (
    <div className="hidden md:flex items-center gap-1">
      {navLinks.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} end={to === '/'}>
          {({ isActive }) => (
            <span
              className={`relative px-3.5 py-2 rounded-full text-sm font-medium transition-colors duration-300 ${
                isActive ? 'text-white' : 'text-slate-400 hover:text-slate-100'
              }`}
            >
              {isActive && (
                <motion.span
                  layoutId="nav-pill"
                  className="absolute inset-0 rounded-full bg-white/[0.08] border border-white/10"
                  transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <Icon className="w-4 h-4" />
                {label}
              </span>
            </span>
          )}
        </NavLink>
      ))}
    </div>
  )
}

function SystemStatus() {
  return (
    <div className="flex items-center gap-2.5 text-xs text-slate-400">
      <span className="relative flex h-2.5 w-2.5">
        <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 animate-ping opacity-75" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
      </span>
      <span className="hidden sm:inline font-medium tracking-wide">5 Agents Online</span>
      <span className="hidden lg:inline text-slate-600 font-mono">v2.0.0</span>
    </div>
  )
}

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageShell><Home /></PageShell>} />
        <Route path="/imaging" element={<PageShell><Imaging /></PageShell>} />
        <Route path="/symptoms" element={<PageShell><Symptoms /></PageShell>} />
        <Route path="/literature" element={<PageShell><Literature /></PageShell>} />
        <Route path="/consultation" element={<PageShell><Consultation /></PageShell>} />
        <Route path="/results" element={<PageShell><Results /></PageShell>} />
      </Routes>
    </AnimatePresence>
  )
}

export default function App() {
  return (
    <Router>
      <div className="relative min-h-screen bg-base text-slate-300 font-body">
        <NeuralCanvas />
        <div className="gradient-mesh" aria-hidden="true">
          <div
            className="mesh-blob w-[560px] h-[560px] -top-40 -left-32 bg-emerald-500/20 animate-float-slow"
            style={{ background: 'radial-gradient(circle, rgba(16,185,129,0.14), transparent 70%)' }}
          />
          <div
            className="mesh-blob w-[640px] h-[640px] top-10 -right-48 bg-cyan-500/20 animate-float-slow"
            style={{ background: 'radial-gradient(circle, rgba(34,211,238,0.10), transparent 70%)', animationDelay: '-5s' }}
          />
          <div
            className="mesh-blob w-[700px] h-[700px] -bottom-60 left-1/3 bg-violet-500/20 animate-float-slow"
            style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.12), transparent 70%)', animationDelay: '-9s' }}
          />
        </div>
        <div className="grid-overlay fixed inset-0 z-0 pointer-events-none" aria-hidden="true" />
        <CursorGlow />
        <ScrollProgress />
        <SmoothScroll />
        <ScrollToTop />

        <nav className="nav-blur sticky top-0 z-40 border-b border-white/[0.06]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between gap-4">
              <Logo />
              <NavLinks />
              <SystemStatus />
            </div>
          </div>
        </nav>

        <AnimatedRoutes />

        <footer className="relative z-10 mt-8 border-t border-white/[0.06] py-6">
          <div className="mx-auto max-w-7xl px-4 text-center text-sm text-slate-500">
            <span className="inline-flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              OncoAgent — Multi-Agent Cancer Diagnostic System
            </span>
            <span className="mx-2 text-slate-700">•</span>
            For Educational &amp; Research Purposes Only
          </div>
        </footer>
      </div>
    </Router>
  )
}