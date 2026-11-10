import { useState, useRef } from 'react'
import { Activity, HeartPulse, Clock, AlertTriangle, Upload, X, ChevronDown, Download } from 'lucide-react'
import { apiClient } from '../services/api'
import PageHeader from '../components/PageHeader'
import { openProfessionalReport } from '../utils/report'

type OrganHint = 'liver' | 'lung' | 'brain' | 'pancreas' | 'colon' | 'breast'

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

const SAMPLE_SCANS: { label: string; file: string; organ: OrganHint; hasTumor: boolean }[] = [
  { label: 'Lung CT (MSD Task 06) — Slice 01186', file: 'real_lung_lung_01186.png', organ: 'lung', hasTumor: true },
  { label: 'Brain MRI (BRISC) — Slice 22610', file: 'real_brain_brain_22610.png', organ: 'brain', hasTumor: true },
  { label: 'Liver CT (MSD Task 03) — Slice 12313', file: 'real_liver_liver_12313.png', organ: 'liver', hasTumor: true },
  { label: 'Pancreas CT (MSD Task 07) — Slice 14799', file: 'real_pancreas_pancreas_14799.png', organ: 'pancreas', hasTumor: true },
  { label: 'Colonoscopy (Kvasir-SEG) — img 25957', file: 'real_colon_colon_25957.png', organ: 'colon', hasTumor: true },
  { label: 'Breast Ultrasound (BUSI) — img 26679', file: 'real_breast_breast_26679.png', organ: 'breast', hasTumor: true },
]

export default function Consultation() {
  const [isConsulting, setIsConsulting] = useState(false)
  const [isImaging, setIsImaging] = useState(false)
  const [overallResult, setOverallResult] = useState<any>(null)
  const [organHint, setOrganHint] = useState<OrganHint>('lung')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [showSamplePicker, setShowSamplePicker] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [formData, setFormData] = useState<SymptomForm>({
    age: 60,
    gender: 'Male',
    smoking: 5,
    passive_smoker: 3,
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

  const severityLabels = ['Minimal', 'Mild', 'Moderate', 'Moderately Severe', 'Severe', 'Very Severe', 'Critical', 'Extreme']

  const updateSeverity = (field: keyof SymptomForm, value: number) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setPreview(URL.createObjectURL(file))
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(null)
  }

  const loadSampleScan = async (sample: typeof SAMPLE_SCANS[0]) => {
    setShowSamplePicker(false)
    try {
      const response = await fetch(`/sample_scans/${sample.file}`)
      if (!response.ok) {
        // Fallback: load from backend API
        const apiResp = await apiClient.get(`/api/v1/samples/${sample.file}`, { responseType: 'blob' })
        const blob = apiResp.data as Blob
        const file = new File([blob], sample.file, { type: 'image/png' })
        setSelectedFile(file)
        setPreview(URL.createObjectURL(blob))
      } else {
        const blob = await response.blob()
        const file = new File([blob], sample.file, { type: 'image/png' })
        setSelectedFile(file)
        setPreview(URL.createObjectURL(blob))
      }
      setOrganHint(sample.organ)
    } catch {
      // Use backend static endpoint
      try {
        const resp = await fetch(`/api/v1/samples/${sample.file}`)
        if (!resp.ok) throw new Error('sample fetch failed')
        const blob = await resp.blob()
        const file = new File([blob], sample.file, { type: 'image/png' })
        setSelectedFile(file)
        setPreview(URL.createObjectURL(blob))
        setOrganHint(sample.organ)
      } catch {
        alert('Could not load sample. Please upload manually from tests/sample_scans/')
      }
    }
  }

  const handleAnalyzeImage = async () => {
    if (!selectedFile) return
    setIsImaging(true)
    setOverallResult(null)
    const fd = new FormData()
    fd.append('file', selectedFile)
    fd.append('organ_hint', organHint)
    try {
      const response = await apiClient.post('/api/v1/imaging', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setOverallResult(response.data)
    } catch (err: any) {
      setOverallResult({ error: err.response?.data?.detail || err.message || 'Image analysis failed' })
    } finally {
      setIsImaging(false)
    }
  }

  const handleAssessSymptoms = async () => {
    setIsConsulting(true)
    setOverallResult(null)
    try {
      const response = await apiClient.post('/api/v1/symptoms', formData)
      setOverallResult(response.data)
    } catch (err: any) {
      setOverallResult({ error: err.response?.data?.detail || err.message || 'Symptom assessment failed' })
    } finally {
      setIsConsulting(false)
    }
  }

  const handleFullConsultation = async () => {
    setIsConsulting(true)
    setOverallResult(null)

    try {
      if (selectedFile) {
        // Multipart form with image + symptom data
        const fd = new FormData()
        fd.append('file', selectedFile)
        fd.append('organ_hint', organHint)
        fd.append('include_literature', 'true')
        fd.append('patient_id', 'demo-patient')
        // Append symptom fields
        Object.entries(formData).forEach(([k, v]) => fd.append(k, String(v)))
        const response = await apiClient.post('/api/v1/consultation/full', fd, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        setOverallResult(response.data)
      } else {
        // JSON payload — symptom-only
        const payload = {
          imaging_result: {
            organ: organHint,
            has_tumor: false,
            tumor_confidence: 0.0,
            organ_confidence: 0.85,
            mask_base64: null,
          },
          symptom_risk: {
            ml_risk_score: formData.smoking * 6 + formData.coughing_blood * 7,
            risk_level: 'Medium',
            suspicion_index: 'Moderate',
            critical_findings: [],
            confidence: 80,
            model_agreement: 90,
          },
          include_literature: true,
          urgency_override: 'none',
          patient_id: 'demo-patient',
          ...formData,
        }
        const response = await apiClient.post('/api/v1/consultation', payload)
        setOverallResult(response.data)
      }
    } catch (err: any) {
      setOverallResult({ error: err.response?.data?.detail || err.message || 'Consultation failed' })
    } finally {
      setIsConsulting(false)
    }
  }

  const SeveritySlider = ({ field, label }: { field: keyof SymptomForm; label: string }) => (
    <div className="mb-3">
      <div className="flex justify-between mb-1">
        <label className="text-sm font-medium text-slate-700">{label}</label>
        <span className="text-sm font-medium text-primary-600">{formData[field]}/8</span>
      </div>
      <input
        type="range"
        min="1"
        max="8"
        value={formData[field] as number}
        onChange={(e) => updateSeverity(field, Number(e.target.value))}
        className="w-full accent-primary-600"
      />
      <span className="text-xs text-slate-400 mt-1">{severityLabels[Math.min(Math.max((formData[field] as number) - 1, 0), 7)]}</span>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-4">
      <PageHeader
        eyebrow="AI Multi-Agent Cancer Consultation"
        title={<>Full <span className="gradient-text">Agentic Consultation</span></>}
        subtitle="Integrated analysis combining imaging, symptom assessment, evidence research, and clinical recommendations — orchestrated by five autonomous agents."
      />

      {/* Status Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="kpi-tile">
          <div className="text-3xl font-bold gradient-text font-display">{selectedFile ? '1' : '0'} Scan{selectedFile ? '' : 's'}</div>
          <div className="text-sm text-slate-400 mt-1">Imaging</div>
        </div>
        <div className="kpi-tile">
          <div className="text-3xl font-bold gradient-text font-display">13 Factors</div>
          <div className="text-sm text-slate-400 mt-1">Symptoms</div>
        </div>
        <div className="kpi-tile">
          <div className="text-3xl font-bold gradient-text font-display">5 Agents</div>
          <div className="text-sm text-slate-400 mt-1">Orchestrated</div>
        </div>
        <div className="kpi-tile">
          <div className={`text-3xl font-bold font-display ${isConsulting ? 'text-cyan-300' : 'text-emerald-300'}`}>
            {isConsulting ? 'Running...' : 'Ready'}
          </div>
          <div className="text-sm text-slate-400 mt-1">Consultation</div>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Left Column: Inputs */}
        <div className="md:w-1/3">
          <div className="card mb-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Upload Medical Scan</h3>

            {/* Sample Scan Quick Load */}
            <div className="relative mb-4">
              <button
                onClick={() => setShowSamplePicker(!showSamplePicker)}
                className="w-full flex items-center justify-between px-3 py-2 border border-primary-300 rounded-lg text-sm text-primary-700 hover:bg-primary-50 transition-colors"
              >
                <span>Load Sample Scan (Demo)</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {showSamplePicker && (
                <div className="absolute z-10 top-10 left-0 right-0 bg-white border border-slate-200 rounded-lg shadow-xl overflow-hidden">
                  {SAMPLE_SCANS.map(s => (
                    <button
                      key={s.file}
                      onClick={() => loadSampleScan(s)}
                      className="w-full text-left px-4 py-2 text-sm hover:bg-primary-50 text-slate-700 flex items-center justify-between"
                    >
                      <span>{s.label}</span>
                      {s.hasTumor && <span className="text-xs text-red-500 font-medium">TUMOR</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div
              className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center mb-4 hover:border-primary-400 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="w-8 h-8 text-primary-500 mx-auto mb-2" />
              <span className="text-sm text-primary-600">Click to upload or drop scan</span>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".png,.jpg,.jpeg,.bmp,.nii,.nii.gz"
                onChange={handleFileSelect}
              />
            </div>

            {preview && (
              <div className="mt-2 relative mb-4">
                <img src={preview} alt="Preview" className="w-full rounded-lg object-contain" />
                <button
                  onClick={removeFile}
                  className="absolute top-1 right-1 w-7 h-7 bg-white rounded-full flex items-center justify-center shadow"
                >
                  <X className="w-4 h-4 text-slate-600" />
                </button>
              </div>
            )}

            <select
              value={organHint}
              onChange={(e) => setOrganHint(e.target.value as OrganHint)}
              className="input-field w-full mt-1"
            >
              <option value="lung">Lung</option>
              <option value="brain">Brain</option>
              <option value="liver">Liver</option>
              <option value="pancreas">Pancreas</option>
              <option value="colon">Colon</option>
              <option value="breast">Breast</option>
            </select>

            <button
              onClick={handleAnalyzeImage}
              disabled={isImaging || !selectedFile}
              className="w-full btn-primary mt-3 py-3"
            >
              {isImaging ? 'Analyzing...' : 'Run Imaging Analysis'}
            </button>
          </div>
        </div>

        {/* Right Column: Symptom Form */}
        <div className="md:w-2/3">
          <div className="card mb-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Symptom Assessment</h3>

            <div className="grid md:grid-cols-2 gap-3 mb-4">
              <div>
                <label className="label text-xs text-slate-600 mb-1">Age</label>
                <input
                  type="number"
                  min="0"
                  max="120"
                  value={formData.age}
                  onChange={(e) => updateSeverity('age', Number(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="label text-xs text-slate-600 mb-1">Gender</label>
                <select
                  value={formData.gender}
                  onChange={(e) => setFormData(prev => ({ ...prev, gender: e.target.value }))}
                  className="input-field"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
            </div>

            <h4 className="text-sm font-medium text-slate-600 mb-3">Risk Factors</h4>
            <div className="grid md:grid-cols-3 gap-2">
              <div className="border rounded-lg p-3"><SeveritySlider field="smoking" label="Smoking" /></div>
              <div className="border rounded-lg p-3"><SeveritySlider field="passive_smoker" label="Passive Smoking" /></div>
              <div className="border rounded-lg p-3"><SeveritySlider field="family_history" label="Family History" /></div>
            </div>

            <h4 className="text-sm font-medium text-slate-600 mb-3 mt-3">Symptoms</h4>
            <div className="grid md:grid-cols-3 gap-2">
              {(['coughing_blood', 'chest_pain', 'weight_loss', 'shortness_of_breath', 'fatigue', 'clubbing', 'wheezing', 'dry_cough'] as Array<keyof SymptomForm>).map((field) => (
                <div key={field} className="border rounded-lg p-3">
                  <SeveritySlider field={field} label={String(field).replace(/_/g, ' ')} />
                </div>
              ))}
            </div>

            <button
              onClick={handleAssessSymptoms}
              disabled={isConsulting}
              className="w-full btn-primary py-3 mt-6 font-medium"
            >
              {isConsulting ? 'Assessing...' : 'Run Symptom Assessment'}
            </button>
          </div>
        </div>
      </div>

      {/* Full Consultation CTA */}
      <div className="text-center py-6">
        <div className="border-4 border-dashed border-primary-300 rounded-2xl mb-6 flex flex-col items-center justify-center py-10">
          <button onClick={handleFullConsultation} disabled={isConsulting} className="cursor-pointer">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-3 mx-auto">
              <HeartPulse className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-primary-800 mb-2">Start Full Consultation</h3>
            <p className="text-sm text-slate-500">Comprehensive multi-agent analysis with scan + symptoms + literature</p>
          </button>
          {isConsulting && (
            <div className="mt-4 text-center">
              <Clock className="w-10 h-10 text-primary-500 animate-spin mx-auto" />
              <p className="text-sm text-slate-500 mt-2">Synthesizing multi-modal analysis...</p>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {overallResult && !isConsulting && (
        <div className="card border-primary-200">
          <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <div className="flex items-center gap-3">
              <Activity className="w-6 h-6 text-primary-600" />
              <h2 className="text-xl font-semibold text-slate-800">Consultation Results</h2>
            </div>
            <button
              onClick={() => openProfessionalReport(overallResult)}
              className="btn-primary px-4 py-2.5"
            >
              <Download className="w-4 h-4" />
              Download Clinical Report (PDF)
            </button>
          </div>

          {overallResult.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 mb-4">
              {overallResult.error}
            </div>
          )}

          {overallResult.overall_risk !== undefined && (
            <div className="text-center mb-6">
              <div className={`text-4xl font-bold ${overallResult.overall_risk >= 70 ? 'text-red-600' : overallResult.overall_risk >= 30 ? 'text-yellow-600' : 'text-green-600'}`}>
                {overallResult.overall_risk}%
              </div>
              <div className="text-sm text-slate-500 mt-1">Overall Risk Score — <span className="font-medium">{overallResult.risk_level}</span></div>
            </div>
          )}

          {/* Overlay if available */}
          {overallResult.overlay_base64 && (
            <div className="mb-4">
              <div className="text-sm text-slate-500 mb-1">AI Segmentation Overlay</div>
              <img src={`data:image/png;base64,${overallResult.overlay_base64}`} alt="AI Overlay" className="rounded-lg max-h-64 mx-auto" />
            </div>
          )}

          {overallResult.agent_agreement !== undefined && (
            <div className="mb-4">
              <div className="text-sm text-slate-500 mb-1">Agent Consensus</div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-primary-600 rounded-full h-2 transition-all" style={{ width: `${overallResult.agent_agreement}%` }} />
              </div>
              <div className="text-xs text-slate-500 mt-1">{overallResult.agent_agreement}% agreement</div>
            </div>
          )}

          {overallResult.critical_alerts && overallResult.critical_alerts.length > 0 && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <h3 className="font-medium text-red-700">Critical Alerts</h3>
              </div>
              <ul className="text-sm text-red-700 space-y-1">
                {overallResult.critical_alerts.map((alert: string, index: number) => (
                  <li key={index}>{alert}</li>
                ))}
              </ul>
            </div>
          )}

          {overallResult.recommended_next_steps && overallResult.recommended_next_steps.length > 0 && (
            <div className="mb-4">
              <div className="text-sm text-slate-500 mb-2">Recommended Next Steps</div>
              <ol className="list-decimal list-inside text-sm text-slate-700 space-y-1">
                {overallResult.recommended_next_steps.map((step: string, index: number) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {overallResult.doctors_to_consult && overallResult.doctors_to_consult.length > 0 && (
            <div className="mb-4">
              <div className="text-sm text-slate-500 mb-1">Recommended Specialists</div>
              <div className="grid md:grid-cols-3 gap-2 text-sm text-slate-700">
                {overallResult.doctors_to_consult.map((doc: any, i: number) => (
                  <div key={i} className="border rounded-md p-3">
                    <h4 className="font-medium text-slate-800">{doc.name}</h4>
                    <p className="text-xs text-slate-500">{doc.department}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {overallResult.summary && (
            <div className="mt-6 p-4 bg-slate-50 rounded-lg text-center">
              <p className="text-base text-slate-800">{overallResult.summary}</p>
            </div>
          )}
        </div>
      )}

      {(!overallResult || isConsulting) && (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Activity className="w-8 h-8 text-primary-500" />
          </div>
          <h3 className="text-lg font-medium text-slate-600 mb-2">Ready for consultation</h3>
          <p className="text-sm text-slate-500">
            Upload a medical scan and/or provide symptom data to receive a comprehensive AI-powered analysis
          </p>
        </div>
      )}
    </div>
  )
}
