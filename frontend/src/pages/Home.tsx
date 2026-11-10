import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  motion,
  AnimatePresence,
  useReducedMotion,
} from 'motion/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  ArrowRight,
  Waypoints,
  Scan,
  Layers,
  Cpu,
  HeartPulse,
  Stethoscope,
  BookOpenText,
  FlaskConical,
  Combine,
  Shield,
} from 'lucide-react'
import AnimatedNumber from '../components/AnimatedNumber'
import TiltCard from '../components/TiltCard'
import MagicButton from '../components/MagicButton'
import SpotlightCard from '../components/SpotlightCard'
import Aurora from '../components/Aurora'
import ShimmerText from '../components/ShimmerText'
import TracingLight from '../components/TracingLight'
import NearbyLocator from '../components/NearbyLocator'
import { SectionHeading } from '../components/SectionHeading'

const ROTATING = ['six organs', '5 autonomous agents', 'real medical imaging', 'one unified report']

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1]

const ORGANS = [
  { key: 'brain', name: 'Brain', source: 'BRISC · MRI', file: 'real_brain_brain_22610.png', mask: 'real_brain_brain_22610_mask.png', mAP: 0.946, modal: 'MRI' },
  { key: 'liver', name: 'Liver', source: 'MSD Task 03 · CT', file: 'real_liver_liver_12313.png', mask: 'real_liver_liver_12313_mask.png', mAP: 0.878, modal: 'CT' },
  { key: 'colon', name: 'Colon', source: 'Kvasir-SEG · Endo', file: 'real_colon_colon_25957.png', mask: 'real_colon_colon_25957_mask.png', mAP: 0.776, modal: 'Endoscopy' },
  { key: 'breast', name: 'Breast', source: 'BUSI · Ultrasound', file: 'real_breast_breast_26679.png', mask: 'real_breast_breast_26679_mask.png', mAP: 0.774, modal: 'Ultrasound' },
  { key: 'lung', name: 'Lung', source: 'MSD Task 06 · CT', file: 'real_lung_lung_01186.png', mask: 'real_lung_lung_01186_mask.png', mAP: 0.805, modal: 'CT' },
  { key: 'pancreas', name: 'Pancreas', source: 'MSD Task 07 · CT', file: 'real_pancreas_pancreas_14799.png', mask: 'real_pancreas_pancreas_14799_mask.png', mAP: 0.758, modal: 'CT' },
] as const

/* Real validation numbers — updated after each training pass on this GPU. */
const MODEL = {
  yoloMap50: 0.823,
  yoloMap5095: 0.534,
  unetDice: 0.258,
  epochs: 30,
} as const

/* ---------- Animmaster-style flip text ---------- */
function TypeRotator() {
  const [i, setI] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setI((v) => (v + 1) % ROTATING.length), 2400)
    return () => clearInterval(id)
  }, [])
  return (
    <span className="relative inline-flex overflow-hidden align-bottom">
      <AnimatePresence mode="wait">
        <motion.span
          key={i}
          initial={{ y: '100%', opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: '-100%', opacity: 0 }}
          transition={{ duration: 0.35, ease: EASE }}
          className="gradient-text font-display whitespace-nowrap"
        >
          {ROTATING[i]}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}

/* ---------- Live scan console — real scans + real U-Net masks ---------- */
function ScanConsole() {
  const reduce = useReducedMotion()
  const [idx, setIdx] = useState(0)
  const [showMask, setShowMask] = useState(true)
  const organ = ORGANS[idx]

  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 34, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.8, delay: 0.3, ease: EASE }}
      className="relative w-full max-w-xl mx-auto lg:max-w-none"
    >
      <div className="absolute -inset-5 rounded-[2rem] bg-gradient-to-br from-emerald-500/25 via-transparent to-violet-500/25 blur-2xl" aria-hidden />

      <div className="relative rounded-3xl border border-white/10 bg-[#0a0f1c]/85 backdrop-blur-2xl p-3 shadow-glass shine overflow-hidden">
        {/* tabs */}
        <div className="flex flex-wrap gap-1.5 px-2 pt-2 pb-3">
          {ORGANS.map((o, k) => (
            <button
              key={o.key}
              onClick={() => setIdx(k)}
              className={`relative px-3 py-1.5 rounded-full text-[11px] font-semibold uppercase tracking-wider transition-colors duration-300 ${
                k === idx ? 'text-[#05070d]' : 'text-slate-400 hover:text-slate-100 bg-white/[0.04]'
              }`}
            >
              {k === idx && (
                <motion.span
                  layoutId="scan-org-pill"
                  className="absolute inset-0 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                  transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                />
              )}
              <span className="relative z-10">{o.name}</span>
            </button>
          ))}
        </div>

        {/* stage */}
        <div className="relative aspect-[4/3] rounded-2xl overflow-hidden img-grid">
          <img
            src={`/sample_scans/${organ.file}`}
            alt={`${organ.name} scan`}
            className="absolute inset-0 w-full h-full object-cover"
            loading="eager"
          />
          <img
            src={`/sample_scans/${organ.mask}`}
            alt=""
            aria-hidden
            className={`absolute inset-0 w-full h-full object-cover mix-blend-screen transition-opacity duration-700 ${
              showMask ? 'opacity-80' : 'opacity-0'
            }`}
          />

          {/* scanline + crosshairs */}
          <div className="absolute left-0 right-0 h-20 animate-scanline bg-gradient-to-b from-transparent via-emerald-400/20 to-transparent pointer-events-none" />
          <div className="absolute left-3 top-3 h-6 w-6 border-l-2 border-t-2 border-emerald-300/70 rounded-tl-lg pointer-events-none" />
          <div className="absolute right-3 top-3 h-6 w-6 border-r-2 border-t-2 border-emerald-300/70 rounded-tr-lg pointer-events-none" />
          <div className="absolute left-3 bottom-3 h-6 w-6 border-l-2 border-b-2 border-emerald-300/70 rounded-bl-lg pointer-events-none" />
          <div className="absolute right-3 bottom-3 h-6 w-6 border-r-2 border-b-2 border-emerald-300/70 rounded-br-lg pointer-events-none" />

          {/* labels */}
          <div className="absolute top-3 left-1/2 -translate-x-1/2 inline-flex items-center gap-1.5 rounded-full bg-black/50 backdrop-blur-md border border-white/15 px-3 py-1 pointer-events-none">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-semibold text-white tracking-wide">{organ.name} · {organ.source}</span>
          </div>
          <div className="absolute bottom-3 left-3 inline-flex items-center gap-1.5 rounded-full bg-black/50 backdrop-blur-md border border-white/15 px-2.5 py-1 pointer-events-none">
            <Scan className="w-3 h-3 text-emerald-300" />
            <span className="text-[10px] font-mono text-emerald-200">U-Net segment {organ.modal}</span>
          </div>

          {/* mask toggle */}
          <button
            onClick={() => setShowMask((v) => !v)}
            className="absolute bottom-3 right-3 inline-flex items-center gap-1.5 rounded-full bg-white/[0.07] hover:bg-white/[0.14] backdrop-blur-md border border-white/15 px-3 py-1.5 text-[11px] font-medium text-slate-200 transition-colors"
          >
            <Layers className={`w-3.5 h-3.5 ${showMask ? 'text-emerald-300' : 'text-slate-500'}`} />
            {showMask ? 'Lesion overlay on' : 'Lesion overlay off'}
          </button>
        </div>

        {/* readout */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-px px-1 pt-3 pb-1">
          {[
            { k: 'DETECTOR', v: 'YOLOv8' },
            { k: 'SEGMENTER', v: 'Attention U-Net' },
            { k: 'MODALITY', v: organ.modal },
            { k: 'SESSION', v: 'Live' },
          ].map((c) => (
            <div key={c.k} className="text-center px-2 py-2">
              <div className="text-[9px] font-semibold uppercase tracking-[0.2em] text-slate-600">{c.k}</div>
              <div className="mt-1 font-mono text-xs text-slate-200 truncate">{c.v}</div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

/* ---------- Aceternity-style card spotlight (shared component) ---------- */

const FEATURES = [
  {
    icon: HeartPulse,
    title: 'Image Analysis',
    desc: 'YOLO + Attention U-Net detection & segmentation across 6 organs — brain, lung, liver, pancreas, colon, breast.',
    accent: 'from-emerald-400 to-teal-400',
    glow: 'shadow-glow',
    link: '/imaging',
  },
  {
    icon: Stethoscope,
    title: 'Symptom Assessment',
    desc: 'Ensemble ML risk engine that turns 13 clinical factors into a calibrated cancer risk score.',
    accent: 'from-cyan-400 to-sky-400',
    glow: 'shadow-glow-cyan',
    link: '/symptoms',
  },
  {
    icon: BookOpenText,
    title: 'Literature Research',
    desc: 'Live PubMed + crossref retrieval so every finding lands on real, citable evidence.',
    accent: 'from-violet-400 to-fuchsia-400',
    glow: 'shadow-glow-violet',
    link: '/literature',
  },
  {
    icon: FlaskConical,
    title: 'Full Consultation',
    desc: 'All agents run in parallel and a synthesis layer fuses them into one clinical report.',
    accent: 'from-amber-300 to-orange-400',
    glow: 'shadow-glow',
    link: '/consultation',
  },
]

const PIPELINE = [
  { icon: Scan, name: 'Imaging Agent', desc: 'Detect & segment lesions pixel-by-pixel' },
  { icon: Stethoscope, name: 'Symptom Agent', desc: 'Score risk from clinical factors' },
  { icon: BookOpenText, name: 'Literature Agent', desc: 'Ground findings in published evidence' },
  { icon: Shield, name: 'Advisory Agent', desc: 'Recommend follow-up & specialists' },
  { icon: Combine, name: 'Synthesis Agent', desc: 'Fuse everything into the final report' },
]

const TRUST = [
  'Every finding cites published literature',
  'Real imaging from public clinical datasets',
  'Printable clinical report',
  'Nearby specialists & care referrals',
  'Five-agent consensus before any result',
  'Designed to support — not replace — your doctor',
  'Over 27,000 real training slices',
  'Built for education & research support',
]

export default function Home() {
  const reduce = useReducedMotion()
  const container = {
    hidden: {},
    show: { transition: { staggerChildren: reduce ? 0 : 0.1, delayChildren: reduce ? 0 : 0.15 } },
  }
  const item = {
    hidden: { opacity: 0, y: 26 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: EASE } },
  }

  const stats = [
    { value: 6, suffix: '', label: 'Organs Supported' },
    { value: 27, suffix: 'K+', label: 'Real Training Slices' },
    { value: 5, suffix: '', label: 'AI Agents' },
    { value: Math.round(MODEL.yoloMap50 * 100), suffix: '%', label: 'YOLO mAP50 (real)' },
  ]

  const rootRef = useRef<HTMLDivElement>(null)
  const scanRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (reduce || typeof window === 'undefined') return
    gsap.registerPlugin(ScrollTrigger)
    const ctx = gsap.context(() => {
      gsap.to(scanRef.current, {
        yPercent: -10,
        opacity: 0.4,
        ease: 'none',
        scrollTrigger: {
          trigger: scanRef.current,
          start: 'top 92%',
          end: 'top top',
          scrub: true,
        },
      })
    }, rootRef)
    return () => ctx.revert()
  }, [reduce])

  return (
    <div ref={rootRef} className="overflow-x-clip">
      {/* ---------- HERO ---------- */}
      <section className="relative pt-12 pb-10">
        <Aurora className="opacity-80 -z-[1]" />
        <div className="mx-auto grid lg:grid-cols-2 gap-10 lg:gap-14 items-center relative z-10">
          <motion.div variants={container} initial="hidden" animate="show">
            <motion.div variants={item}>
              <span className="glass-chip text-emerald-300 mb-6">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 animate-ping opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                </span>
                Trained on GPU · Real clinical imaging
              </span>
            </motion.div>

            <motion.h1
              variants={item}
              className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-[1.06]"
            >
              Cancer diagnostics,
              <br />
              <ShimmerText text="orchestrated by AI" className="font-display" />
            </motion.h1>

            <motion.p variants={item} className="mt-7 text-base sm:text-lg text-slate-400 max-w-xl leading-relaxed">
              OncoAgent runs <b className="text-slate-200 font-semibold">5 autonomous agents</b> over{' '}
              <TypeRotator />
              <br className="hidden sm:block" />
              then synthesizes a single, evidence-backed clinical picture.
            </motion.p>

            <motion.div variants={item} className="mt-9 flex flex-col sm:flex-row items-start gap-4">
              <MagicButton to="/consultation" className="btn-primary text-base px-8 py-3.5 shine group">
                Run Full Consultation
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </MagicButton>
              <MagicButton to="/imaging" className="btn-secondary text-base px-8 py-3.5">
                Try Image Analysis
              </MagicButton>
            </motion.div>

            <motion.div variants={item} className="mt-8 flex items-center gap-2 text-xs text-slate-500">
              <Cpu className="w-3.5 h-3.5 text-emerald-400/70" />
              Evidence-backed findings · Printable clinical report · Care coordination nearby
            </motion.div>
          </motion.div>

          <div ref={scanRef} className="[will-change:transform]">
            <ScanConsole />
          </div>
        </div>

        {/* marquee */}
        <div className="mt-14 border-y border-white/[0.05] bg-white/[0.02] py-4 overflow-hidden">
          <div className="flex w-max animate-marquee gap-10 whitespace-nowrap">
            {[...TRUST, ...TRUST].map((t, i) => (
              <span key={i} className="inline-flex items-center gap-2 text-sm font-medium text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400" />
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- STATS ---------- */}
      <section className="py-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5, delay: i * 0.08, ease: EASE }}
              className="metric-card"
            >
              <span
                className="metric-top"
                style={{
                  background: `linear-gradient(90deg, transparent,
                    ${['rgba(52,211,153,0.8)', 'rgba(45,212,191,0.8)', 'rgba(103,232,249,0.8)', 'rgba(167,139,250,0.8)'][i]},
                    transparent)`,
                  backgroundSize: '200% 100%',
                }}
              />
              <div className="font-display text-4xl font-bold text-white tabular-nums">
                <AnimatedNumber value={s.value} suffix={s.suffix} />
              </div>
              <div className="text-[11px] font-medium uppercase tracking-[0.22em] text-slate-500 mt-2.5">
                {s.label}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ---------- MODEL ZOO ---------- */}
      <section className="relative py-10">
        <TracingLight className="hidden lg:block" offset="left-4" />
        <div className="relative">
        <SectionHeading
          eyebrow="Model Zoo · honest reporting"
          title="Real numbers, real inference"
          subtitle="Both models were trained end-to-end on locally hosted GPU hardware. These are the actual validation metrics from the final runs."
        />
        <div className="grid lg:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.6, ease: EASE }}
            className="lg:col-span-2 glass-panel p-6 shine-border"
          >
            <div className="flex items-end justify-between mb-5">
              <div>
                <div className="glass-chip text-emerald-300 mb-2">
                  <Scan className="w-3.5 h-3.5" />
                  YOLOv8 · organ detection
                </div>
                <h3 className="font-display text-lg font-semibold text-white">Per-organ mAP@50</h3>
              </div>
              <div className="text-right">
                <div className="font-display text-3xl font-bold gradient-text">
                  <AnimatedNumber value={MODEL.yoloMap50} decimals={3} />
                </div>
                <div className="text-xs text-slate-500 mt-0.5">overall mAP50</div>
                <div className="text-[10px] font-mono text-slate-600 mt-0.5">mAP50-95 {MODEL.yoloMap5095.toFixed(3)}</div>
              </div>
            </div>
            <div className="space-y-3">
              {ORGANS.map((o, i) => (
                <div key={o.key} className="flex items-center gap-3">
                  <span className="w-24 shrink-0 text-sm font-medium text-slate-300">{o.name}</span>
                  <div className="relative flex-1 h-2 rounded-full bg-white/[0.05] overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${o.mAP * 100}%` }}
                      viewport={{ once: true, margin: '-40px' }}
                      transition={{ duration: 1.1, delay: i * 0.08, ease: EASE }}
                      className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400"
                    />
                  </div>
                  <span className="w-14 shrink-0 text-right font-mono text-xs text-slate-300">
                    {(o.mAP * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </motion.div>

          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.6, ease: EASE }}
              className="glass-panel p-6"
            >
              <div className="glass-chip text-violet-300 mb-2">
                <Layers className="w-3.5 h-3.5" />
                Attention U-Net
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className="font-display text-3xl font-bold gradient-text">
                  <AnimatedNumber value={MODEL.unetDice} decimals={3} />
                </span>
                <span className="text-sm text-slate-500">test Dice</span>
              </div>
              <p className="mt-3 text-xs text-slate-500 leading-relaxed">
                {MODEL.epochs} epochs · 9,000 balanced slices · aug rotation/scale/flip · BCE + Dice loss on 128px tiles.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.6, delay: 0.1, ease: EASE }}
              className="glass-panel p-6"
            >
              <div className="glass-chip text-cyan-300 mb-2">
                <Cpu className="w-3.5 h-3.5" />
                On-device stack
              </div>
              <ul className="mt-3 space-y-2 text-sm text-slate-400">
                <li className="flex justify-between"><span>GPU</span><span className="font-mono text-slate-200">RTX 5050</span></li>
                <li className="flex justify-between"><span>CUDA</span><span className="font-mono text-slate-200">12.8 · torch 2.11</span></li>
                <li className="flex justify-between"><span>Latency</span><span className="font-mono text-slate-200">~17 ms / scan</span></li>
                <li className="flex justify-between"><span>Training set</span><span className="font-mono text-slate-200">18.8K slices</span></li>
              </ul>
</motion.div>
          </div>
        </div>
        </div>
      </section>

      {/* ---------- REAL DATA GALLERY ---------- */}
      <section className="py-10">
        <SectionHeading
          eyebrow="The six real datasets"
          title="Real scans. Real masks."
          subtitle="Every thumbnail below is a labeled slice from a public clinical dataset — the same images these models were trained on."
        />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {ORGANS.map((o, i) => (
            <motion.div
              key={o.key}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ duration: 0.5, delay: i * 0.07, ease: EASE }}
            >
              <div className="group relative overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.03]">
                <div className="relative aspect-square img-grid overflow-hidden">
                  <img
                    src={`/sample_scans/${o.file}`}
                    alt={`${o.name} scan`}
                    loading="lazy"
                    className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
                  <span className="absolute top-2 right-2 rounded-full bg-black/50 backdrop-blur-md border border-white/15 px-2 py-0.5 font-mono text-[10px] text-emerald-300">
                    {(o.mAP * 100).toFixed(0)}% mAP
                  </span>
                </div>
                <div className="px-3 py-2.5">
                  <div className="text-sm font-semibold text-white">{o.name}</div>
                  <div className="text-[10px] font-mono text-slate-500 truncate">{o.source}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ---------- FEATURES ---------- */}
      <section className="py-8">
        <SectionHeading
          eyebrow="Capabilities"
          title="Four modules. One brain."
          subtitle="Every module is a real agent with a real model. Upload a scan, describe symptoms, or run the whole orchestra."
        />
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 [perspective:1200px]">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.55, delay: i * 0.1, ease: EASE }}
            >
              <SpotlightCard className="h-full rounded-2xl">
                <TiltCard className="group relative h-full rounded-2xl border border-white/[0.07] bg-white/[0.04] backdrop-blur-xl p-6 shadow-glass hover:border-white/[0.14] transition-colors">
                  <div className="relative z-10 flex items-start justify-between">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.accent} p-2.5 shadow-lg ${f.glow} transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`}>
                      <f.icon className="w-full h-full text-[#05070d]" strokeWidth={2.4} />
                    </div>
                    <span className="font-mono text-xs text-slate-600">{String(i + 1).padStart(2, '0')}</span>
                  </div>
                  <h3 className="relative z-10 mt-5 font-display text-lg font-semibold text-white">{f.title}</h3>
                  <p className="relative z-10 mt-2 text-sm text-slate-400 leading-relaxed">{f.desc}</p>
                  <Link
                    to={f.link}
                    className="relative z-10 mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-emerald-300 hover:text-emerald-200 transition-colors"
                  >
                    Launch module
                    <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
                  </Link>
                </TiltCard>
              </SpotlightCard>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ---------- PIPELINE ---------- */}
      <section className="py-12">
        <SectionHeading
          eyebrow="Orchestration"
          title="The agent pipeline"
          subtitle="A LangGraph state machine runs the agents, carries state between them, and refuses to hand you a report until every specialist has spoken."
        />
        <div className="relative">
          <div className="absolute hidden lg:block left-6 right-6 top-8 h-px bg-gradient-to-r from-transparent via-emerald-400/30 to-transparent" />
          <div className="grid lg:grid-cols-5 gap-6">
            {PIPELINE.map((p, i) => (
              <motion.div
                key={p.name}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-60px' }}
                transition={{ duration: 0.5, delay: i * 0.12, ease: EASE }}
              >
                <div className="relative group h-full rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 backdrop-blur-xl hover:border-emerald-400/30 transition-colors">
                  <div className="relative w-16 h-16 rounded-2xl mx-auto flex items-center justify-center bg-gradient-to-br from-emerald-400/15 to-violet-400/15 border border-white/10 group-hover:scale-105 transition-transform">
                    <p.icon className="w-7 h-7 text-emerald-300" strokeWidth={2} />
                    <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-[#05070d] border border-emerald-400/40 text-emerald-300 text-xs font-bold flex items-center justify-center font-mono">
                      {i + 1}
                    </span>
                  </div>
                  <h4 className="mt-4 text-center font-display font-semibold text-slate-100 text-[15px]">{p.name}</h4>
                  <p className="mt-1.5 text-center text-xs text-slate-500 leading-relaxed">{p.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.6, ease: EASE }}
          className="mt-10 relative overflow-hidden rounded-3xl border border-emerald-400/20 bg-gradient-to-r from-emerald-500/10 via-transparent to-violet-500/10 p-8 text-center shine-border"
        >
          <div className="absolute inset-0 bg-[radial-gradient(60%_120%_at_50%_0%,rgba(52,211,153,0.12),transparent_60%)]" />
          <div className="relative">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-emerald-400 to-cyan-400 p-3 shadow-glow animate-float">
              <Waypoints className="w-full h-full text-[#05070d]" strokeWidth={2.2} />
            </div>
            <h3 className="mt-5 font-display text-2xl font-bold text-white">One unified clinical report</h3>
            <p className="mt-2 text-sm text-slate-400 max-w-xl mx-auto">
              Overall risk, segmentation overlays, agent consensus, recommended specialists and a
              plain-language summary — delivered in seconds.
            </p>
          </div>
        </motion.div>
      </section>

      {/* ---------- NEARBY CARE ---------- */}
      <section className="py-10">
        <SectionHeading
          eyebrow="Community care"
          title="Find care nearby"
          subtitle="Hospitals, specialists and pharmacies around you — pulled live from OpenStreetMap, no account needed."
        />
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.6, ease: EASE }}
          className="glass-panel p-6 max-w-3xl mx-auto"
        >
          <NearbyLocator radius={10} />
        </motion.div>
      </section>

      {/* ---------- FINAL CTA ---------- */}
      <section className="py-10 pb-4 text-center">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: EASE }}
        >
          <h2 className="font-display text-3xl font-bold text-white">
            Ready to <span className="gradient-text">diagnose</span> something?
          </h2>
          <div className="mt-7 flex justify-center">
            <MagicButton to="/consultation" className="btn-primary text-base px-9 py-3.5 shine group">
              Start Full Consultation
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </MagicButton>
          </div>
        </motion.div>
      </section>
    </div>
  )
}