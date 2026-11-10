import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  AlertTriangle,
  CheckCircle,
  ScanLine,
  UserPlus,
  ClipboardList,
  Leaf,
  ShieldPlus,
  ArrowRight,
  Info,
  Activity,
  HeartPulse,
} from 'lucide-react'
import { apiClient } from '../services/api'
import NearbyLocator from '../components/NearbyLocator'
import AnimatedNumber from '../components/AnimatedNumber'

type SymptomForm = {
  age: number
  gender: string
  smoking: number
  passive_smoker: number
  coughing_blood: number
  chest_pain: number
  weight_loss: number
  shortness_of_breath: number
  fatigue: number
  clubbing: number
  wheezing: number
  dry_cough: number
  family_history: number
}

type CarePlanStep = {
  category: string
  title: string
  detail: string
}

const CARE_ICONS: Record<string, { icon: any; cls: string }> = {
  imaging: { icon: ScanLine, cls: 'text-emerald-300 bg-emerald-400/10 border-emerald-400/20' },
  referral: { icon: UserPlus, cls: 'text-cyan-300 bg-cyan-400/10 border-cyan-400/20' },
  review: { icon: ClipboardList, cls: 'text-violet-300 bg-violet-400/10 border-violet-400/20' },
  lifestyle: { icon: Leaf, cls: 'text-amber-300 bg-amber-400/10 border-amber-400/20' },
}

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1]

export default function Symptoms() {
  const [formData, setFormData] = useState<SymptomForm>({
    age: 45,
    gender: 'Male',
    smoking: 3,
    passive_smoker: 2,
    coughing_blood: 1,
    chest_pain: 1,
    weight_loss: 1,
    shortness_of_breath: 1,
    fatigue: 1,
    clubbing: 1,
    wheezing: 1,
    dry_cough: 1,
    family_history: 1,
  })
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const updateField = (field: keyof SymptomForm, value: number | string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    setErrorMsg(null)
    setResult(null)
    try {
      const response = await apiClient.post('/api/v1/symptoms', formData)
      setResult(response.data)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Assessment failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const riskLevel: string = result?.risk_level
  const riskTone =
    riskLevel === 'High'
      ? { text: 'text-rose-400', ring: 'ring-rose-400/30', bar: 'from-rose-500 to-red-500', chip: 'bg-rose-400/10 text-rose-300 border-rose-400/30' }
      : riskLevel === 'Medium'
        ? { text: 'text-amber-300', ring: 'ring-amber-400/30', bar: 'from-amber-400 to-orange-500', chip: 'bg-amber-400/10 text-amber-300 border-amber-400/30' }
        : { text: 'text-emerald-300', ring: 'ring-emerald-400/30', bar: 'from-emerald-400 to-teal-500', chip: 'bg-emerald-400/10 text-emerald-300 border-emerald-400/30' }

  const suggestsImaging = result?.imaging_recommendation?.recommended

  return (
    <div className="mx-auto max-w-4xl">
      <motion.header
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE }}
        className="mb-8 text-center"
      >
        <div className="glass-chip text-emerald-300 mb-4 inline-flex">
          <Activity className="w-3.5 h-3.5" />
          Symptom Agent · Ensemble ML
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-bold text-white tracking-tight">
          Symptom Risk Assessment
        </h1>
        <p className="mt-3 text-sm text-slate-400 max-w-xl mx-auto">
          Answer the clinical questions below. If a risk is detected, OncoAgent recommends next steps — including
          imaging, the right specialist, a care plan, and providers near you.
        </p>
      </motion.header>

      {/* ───────────── FORM ───────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: EASE }}
        className="card mb-6"
      >
        <h2 className="text-lg font-semibold text-white mb-4">Patient Information</h2>

        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="label">Age</label>
            <input
              type="number"
              min="1"
              max="120"
              value={formData.age}
              onChange={(e) => updateField('age', Number(e.target.value))}
              className="input-field"
            />
          </div>
          <div>
            <label className="label">Gender</label>
            <select
              value={formData.gender}
              onChange={(e) => updateField('gender', e.target.value)}
              className="input-field [&>option]:bg-[#0a0f1c]"
            >
              <option value="Male">Male</option>
              <option value="Female">Female</option>
            </select>
          </div>
        </div>

        <h3 className="text-md font-semibold text-slate-200 mb-3">Risk Factors</h3>
        <div className="grid md:grid-cols-2 gap-x-6">
          <SeveritySlider field="smoking" label="Smoking" value={formData.smoking} onChange={updateField} />
          <SeveritySlider field="passive_smoker" label="Passive Smoking" value={formData.passive_smoker} onChange={updateField} />
          <SeveritySlider field="family_history" label="Family History" value={formData.family_history} onChange={updateField} />
          <SeveritySlider field="dry_cough" label="Dry Cough" value={formData.dry_cough} onChange={updateField} />
        </div>

        <h3 className="text-md font-semibold text-slate-200 mt-6 mb-3">Symptoms</h3>
        <div className="grid md:grid-cols-2 gap-x-6">
          <SeveritySlider field="coughing_blood" label="Coughing of Blood" value={formData.coughing_blood} onChange={updateField} />
          <SeveritySlider field="chest_pain" label="Chest Pain" value={formData.chest_pain} onChange={updateField} />
          <SeveritySlider field="weight_loss" label="Weight Loss" value={formData.weight_loss} onChange={updateField} />
          <SeveritySlider field="shortness_of_breath" label="Shortness of Breath" value={formData.shortness_of_breath} onChange={updateField} />
          <SeveritySlider field="fatigue" label="Fatigue" value={formData.fatigue} onChange={updateField} />
          <SeveritySlider field="clubbing" label="Clubbing of Finger Nails" value={formData.clubbing} onChange={updateField} />
          <SeveritySlider field="wheezing" label="Wheezing" value={formData.wheezing} onChange={updateField} />
        </div>

        <button onClick={handleAnalyze} disabled={isAnalyzing} className="w-full btn-primary text-lg py-3 mt-6 shine">
          {isAnalyzing ? (
            <span className="flex items-center gap-2 justify-center">
              <Activity className="w-5 h-5 animate-spin" />
              Assessing risk with 13 clinical factors…
            </span>
          ) : (
            'Assess Cancer Risk'
          )}
        </button>
      </motion.div>

      {/* ───────────── RESULTS ───────────── */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE }}
          className="space-y-5"
        >
          {/* Score strip */}
          <div className="card border !border-white/[0.09]">
            <div className="flex items-center gap-3 mb-5">
              <CheckCircle className="w-6 h-6 text-emerald-300" />
              <h2 className="text-xl font-semibold text-white">Risk Assessment Results</h2>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-5">
              <div className="kpi-tile">
                <div className="text-sm text-slate-500 mb-1">Risk Score</div>
                <div className="text-3xl font-bold gradient-text">
                  <AnimatedNumber value={result.ml_risk_score} decimals={1} suffix="%" />
                </div>
              </div>
              <div className="kpi-tile">
                <div className="text-sm text-slate-500 mb-1">Risk Level</div>
                <div className={`text-3xl font-bold ${riskTone.text}`}>{riskLevel}</div>
              </div>
              <div className="kpi-tile">
                <div className="text-sm text-slate-500 mb-1">Confidence</div>
                <div className="text-3xl font-bold text-slate-100">
                  <AnimatedNumber value={result.confidence ?? 0} decimals={0} suffix="%" />
                </div>
              </div>
            </div>

            <div className="h-2.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.max(result.ml_risk_score, 4)}%` }}
                transition={{ duration: 1.2, ease: EASE }}
                className={`h-full rounded-full bg-gradient-to-r ${riskTone.bar}`}
              />
            </div>

            {result.model_type && (
              <div className="text-xs text-slate-500 text-center mt-3 font-mono">Model: {result.model_type}</div>
            )}
          </div>

          {/* Critical findings */}
          {result.critical_findings && result.critical_findings.length > 0 && (
            <div className="rounded-2xl border border-rose-400/25 bg-rose-400/[0.07] p-5">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-rose-300" />
                <h3 className="font-medium text-rose-200">Critical Findings</h3>
              </div>
              <ul className="list-disc list-inside text-sm text-rose-200/90 space-y-1">
                {result.critical_findings.map((f: string, i: number) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}

          {/* ── Imaging recommendation ── */}
          {suggestsImaging && (
            <div className="relative overflow-hidden rounded-2xl border border-amber-400/30 bg-gradient-to-r from-amber-400/[0.10] via-orange-500/[0.06] to-transparent p-6">
              <div className="absolute inset-0 bg-[radial-gradient(60%_120%_at_10%_0%,rgba(251,191,36,0.15),transparent_60%)]" />
              <div className="relative flex flex-col sm:flex-row items-start sm:items-center gap-5">
                <div className="w-14 h-14 shrink-0 rounded-2xl bg-amber-400/15 border border-amber-400/30 flex items-center justify-center animate-float">
                  <ScanLine className="w-7 h-7 text-amber-300" />
                </div>
                <div className="flex-1">
                  <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold border ${riskTone.chip}`}>
                    <HeartPulse className="w-3 h-3" />
                    {riskLevel} risk detected
                  </span>
                  <h3 className="mt-2 font-display text-xl font-semibold text-white">
                    {result.imaging_recommendation?.modality || 'Medical imaging'} recommended
                  </h3>
                  <p className="mt-1.5 text-sm text-slate-300 leading-relaxed">
                    {result.imaging_recommendation?.reason}
                  </p>
                </div>
                <Link
                  to="/imaging"
                  className="btn-primary px-5 py-2.5 shrink-0 shine group"
                >
                  Run Image Analysis
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </div>
            </div>
          )}

          {/* ── Care plan ── */}
          {result.care_plan && result.care_plan.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <ShieldPlus className="w-5 h-5 text-emerald-300" />
                <h3 className="font-semibold text-white">Your next steps — care plan</h3>
              </div>
              <ol className="space-y-3">
                {result.care_plan.map((step: CarePlanStep, i: number) => {
                  const meta = CARE_ICONS[step.category] || CARE_ICONS.review
                  return (
                    <li
                      key={i}
                      className="flex gap-4 items-start rounded-xl border border-white/[0.06] bg-white/[0.03] p-4"
                    >
                      <span className={`w-8 h-8 shrink-0 rounded-lg border flex items-center justify-center text-xs font-mono font-semibold ${meta.cls}`}>
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <div>
                        <div className="text-sm font-medium text-white">{step.title}</div>
                        {step.detail !== step.title && (
                          <div className="text-xs text-slate-400 mt-0.5 leading-relaxed">{step.detail}</div>
                        )}
                      </div>
                    </li>
                  )
                })}
              </ol>
            </div>
          )}

          {/* ── Specialist recommendation ── */}
          {result.doctors_to_consult && result.doctors_to_consult.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <UserPlus className="w-5 h-5 text-cyan-300" />
                <h3 className="font-semibold text-white">Suggested specialists</h3>
              </div>
              <div className="grid md:grid-cols-2 gap-3">
                {result.doctors_to_consult.map((doc: any, i: number) => (
                  <div key={i} className="rounded-xl border border-cyan-400/15 bg-cyan-400/[0.05] p-4">
                    <div className="text-sm font-semibold text-white">{doc.name}</div>
                    <div className="text-xs text-slate-400 mt-1">{doc.department}</div>
                    {doc.why_visit && <div className="text-xs text-slate-400 mt-2 leading-relaxed">{doc.why_visit}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Medication information ── */}
          {result.medications_info && result.medications_info.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <ShieldPlus className="w-5 h-5 text-violet-300" />
                <h3 className="font-semibold text-white">Associated treatments (informational)</h3>
              </div>
              <p className="text-xs text-slate-500 mb-4">
                Commonly used in this pathway. What they do and how they're taken — educational summary only.
              </p>
              <div className="grid md:grid-cols-2 gap-3">
                {result.medications_info.map((med: any, i: number) => (
                  <div key={i} className="rounded-xl border border-violet-400/15 bg-violet-400/[0.05] p-4">
                    <div className="text-sm font-semibold text-white">{med.name}</div>
                    <div className="text-[11px] font-mono text-violet-300 uppercase tracking-wide mt-0.5">{med.type}</div>
                    <div className="text-xs text-slate-400 mt-2 leading-relaxed">{med.what_it_does}</div>
                    {med.simple_tip && (
                      <div className="text-xs text-slate-500 mt-1.5 italic">{med.simple_tip}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Nearby locator ── */}
          <div className="card">
            <NearbyLocator specialty={result.suggested_specialist} />
          </div>

          {/* Disclaimer */}
          {result.disclaimer && (
            <div className="flex items-start gap-2 rounded-xl border border-white/[0.05] bg-white/[0.02] p-4 text-xs text-slate-500 leading-relaxed">
              <Info className="w-3.5 h-3.5 mt-0.5 shrink-0 text-slate-400" />
              {result.disclaimer}
            </div>
          )}
        </motion.div>
      )}

      {/* ── Error ── */}
      {errorMsg && (
        <div className="rounded-2xl border border-rose-400/25 bg-rose-400/[0.07] p-5 text-rose-200 text-sm">
          {errorMsg}
        </div>
      )}
    </div>
  )
}

function SeveritySlider({
  field,
  label,
  value,
  onChange,
}: {
  field: keyof SymptomForm
  label: string
  value: number
  onChange: (f: keyof SymptomForm, v: number) => void
}) {
  const severityLabels = ['Minimal', 'Mild', 'Moderate', 'Moderately Severe', 'Severe', 'Very Severe', 'Critical', 'Extreme']
  return (
    <div className="mb-4">
      <div className="flex justify-between mb-1">
        <label className="text-sm font-medium text-slate-200">{label}</label>
        <span className="text-sm font-medium text-emerald-300">{value}/8</span>
      </div>
      <input
        type="range"
        min="1"
        max="8"
        value={value}
        onChange={(e) => onChange(field, Number(e.target.value))}
        className="w-full accent-emerald-400"
      />
      <div className="text-xs text-slate-500 mt-1">{severityLabels[Math.min(Math.max(value - 1, 0), 7)]}</div>
    </div>
  )
}