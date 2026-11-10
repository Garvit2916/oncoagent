/* Professional printable clinical report generator.
 *
 * Opens a print-optimized A4 report in a new window built from any OncoAgent
 * result payload (full consultation, symptom screening or imaging analysis)
 * and triggers the browser print / Save-as-PDF dialog.
 */

type AnyResult = Record<string, any>

const esc = (v: any): string =>
  String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

const pick = (obj: AnyResult | undefined, ...keys: string[]): any => {
  for (const k of keys) {
    if (obj && obj[k] !== undefined && obj[k] !== null) return obj[k]
  }
  return undefined
}

const normLists = (v: any): any[] => (Array.isArray(v) ? v : [])

const pct = (v: any, decimals = 1): string => {
  const n = Number(v)
  return Number.isFinite(n) ? `${(n * 100).toFixed(decimals)}%` : '—'
}

const riskClass = (level?: string): string => {
  switch ((level || '').toLowerCase()) {
    case 'high':
      return 'risk-high'
    case 'medium':
    case 'moderate':
      return 'risk-mid'
    default:
      return 'risk-low'
  }
}

function pad(n: number) {
  return n.toString().padStart(2, '0')
}

function fmtDate(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function fmtTime(d: Date) {
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function reportStamp(d: Date) {
  const s = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`
  const t = `${pad(d.getHours())}${pad(d.getMinutes())}`
  return `OA-${s}-${t}`
}

function fieldRow(label: string, value: any, noWrap = false) {
  if (value === undefined || value === null || value === '' || value === '—') return ''
  return `<div class="field"><span class="fk">${label}</span><span class="fv${noWrap ? ' nowrap' : ''}">${esc(value)}</span></div>`
}

function buildHeader(r: AnyResult, now: Date): string {
  const pid = pick(r, 'patient_id', 'patientId') || '—'
  const age = pick(r, 'symptom_findings', 'symptom_result') && (pick(pick(r, 'symptom_findings', 'symptom_result'), 'age'))
  const gender = pick(r, 'symptom_findings', 'symptom_result') && (pick(pick(r, 'symptom_findings', 'symptom_result'), 'gender'))
  const studyType =
    (r.overall_risk !== undefined || r.summary) ? 'Full Multi-Agent Consultation' : 'Preliminary Screening'

  return `<header class="letterhead">
    <div>
      <div class="brand"><span class="mark">✦</span> OncoAgent™</div>
      <div class="brand-sub">Multi-Agent Cancer Diagnostic Screening System</div>
    </div>
    <div class="report-id">
      <div class="rid">Report № ${reportStamp(now)}</div>
      <div class="rid-sub">Confidential patient draft</div>
    </div>
  </header>
  <div class="title-block">
    <h1>Computer-Aided Clinical Support Report</h1>
    <div class="subtitle">${studyType}&ensp;·&ensp;Generated ${fmtDate(now)} at ${fmtTime(now)}</div>
  </div>
  <table class="meta-table">
    <tr>
      <td>${fieldRow('Patient ID', pid, true)}</td>
      <td>${fieldRow('Age / Sex', age != null && gender ? `${esc(age)} / ${esc(gender)}` : (age != null ? esc(age) : (gender ? esc(gender) : '—')), true)}</td>
      <td>${fieldRow('Study type', studyType)}</td>
      <td>${fieldRow('Status', 'Draft — awaiting clinician review')}</td>
    </tr>
  </table>`
}

function buildSummary(r: AnyResult): string {
  const level = pick(r, 'risk_level', 'riskLevel') || 'Low'
  const risk = pick(r, 'overall_risk', 'overallRisk')
  const suspicion = pick(r, 'suspicion_index')
  const confidence = pick(r, 'overall_confidence', 'overallConfidence', 'confidence')
  const agreement = pick(r, 'agent_agreement', 'agreement_level')
  const summary = pick(r, 'summary', 'diagnostic_summary')

  let cells = `<div class="cell"><span class="ck">Overall risk score</span><span class="cv big">${risk != null ? esc(risk) + '%' : '—'}</span></div>
    <div class="cell"><span class="ck">Risk level</span><span class="badge ${riskClass(level)}">${esc(level)}</span></div>`
  if (suspicion != null) cells += `<div class="cell"><span class="ck">Suspicion index</span><span class="cv">${esc(suspicion)}</span></div>`
  cells += `<div class="cell"><span class="ck">System confidence</span><span class="cv">${confidence != null ? esc(confidence) + '%' : '—'}</span></div>`
  if (agreement != null) cells += `<div class="cell"><span class="ck">Agent consensus</span><span class="cv">${esc(agreement)}%</span></div>`

  return `<section class="summary-band"><h2 style="margin-top:0">Clinical Summary</h2>
    <div class="cells">${cells}</div>
    ${summary ? `<p class="summary-text">${esc(summary)}</p>` : ''}</section>`
}

function buildImaging(r: AnyResult): string {
  const img =
    pick(r, 'imaging_findings', 'imaging_result') ||
    (r.organ !== undefined ? r : undefined)
  if (!img) return ''

  const organ = pick(img, 'organ', 'organ_name') || '—'
  const organConf = pick(img, 'organ_confidence')
  const tumor = pick(img, 'has_tumor')
  const tumorConf = pick(img, 'tumor_confidence')
  const vol = pick(img, 'tumor_volume_ratio')
  const area = pick(img, 'tumor_area')
  const bbox = pick(img, 'bounding_box')
  const overlay = pick(img, 'overlay_base64') || pick(r, 'overlay_base64')
  const modality = pick(img, 'modality')
  const ms = pick(img, 'processing_time_ms')

  const finding =
    tumor === true
      ? `<div class="finding-bad"><span class="dot"></span> Lesion detected in the ${esc(organ)} region — further specialist
        evaluation strongly advised. Findings must be confirmed by a qualified physician.</div>`
      : tumor === false
        ? `<div class="finding-good"><span class="dot"></span> No lesion detected in the analyzed slice. A clear scan does not rule
        out pathology elsewhere — always follow clinical advice.</div>`
        : ''

  let table = '<table class="data-table"><thead><tr><th>Modality</th><th>Organ detected</th><th>Organ confidence</th><th>Lesion</th><th>Lesion confidence</th><th>Tumor load</th></tr></thead>'
  table += `<tbody><tr>
    <td>${esc(modality || 'Imaging')}</td>
    <td>${esc(organ)}</td>
    <td>${organConf != null ? pct(Number(organConf) / 100, 1) : '—'}</td>
    <td>${tumor === true ? 'Detected' : tumor === false ? 'None' : '—'}</td>
    <td>${tumorConf != null ? pct(Number(tumorConf) / 100, 1) : '—'}</td>
    <td>${vol != null ? pct(Number(vol), 2) : (area != null ? esc(area) + ' px' : '—')}</td>
  </tr></tbody></table>`

  let boxes = ''
  const rawBoxes = normLists(pick(img, 'boxes'))
  if (rawBoxes.length) {
    boxes = `<div class="sub-sec"><div class="sub-head">Detected objects</div>
      <table class="data-table"><thead><tr><th>#</th><th>Organ</th><th>Confidence</th></tr></thead><tbody>`
    rawBoxes.slice(0, 6).forEach((b: AnyResult, i: number) => {
      boxes += `<tr><td>${i + 1}</td><td>${esc(b.organ ?? '—')}</td><td>${b.confidence != null ? pct(Number(b.confidence) / 100, 1) : '—'}</td></tr>`
    })
    boxes += '</tbody></table></div>'
  }

  let bboxRow = ''
  if (bbox && typeof bbox === 'object') {
    bboxRow = `<div class="sub-sec"><div class="sub-head">Localization</div>
      <div class="mono">RoI [x1=${esc(bbox.x1)}, y1=${esc(bbox.y1)}, x2=${esc(bbox.x2)}, y2=${esc(bbox.y2)}]&ensp;·&ensp;analysed on 256 px tiles&ensp;·&ensp;${ms != null ? esc(ms) + ' ms' : '—'}</div></div>`
  } else if (ms != null) {
    bboxRow = `<div class="sub-sec"><div class="sub-head">Processing</div>
      <div class="mono">Completed in ${esc(ms)} ms on locally hosted GPU inference.</div></div>`
  }

  const overlayImg = overlay
    ? `<div class="overlay"><div class="sub-head">AI annotation overlay</div>
      <img src="data:image/png;base64,${overlay}" alt="AI annotation overlay" /></div>`
    : ''

  return `<h2><span class="secnum">1</span>Imaging Findings
    <span class="secsub">YOLO organ detection · Attention U-Net lesion segmentation</span></h2>
    ${finding}${table}${boxes}${bboxRow}${overlayImg}`
}

function buildSymptoms(r: AnyResult): string {
  const sym =
    pick(r, 'symptom_findings', 'symptom_result') ||
    (r.ml_risk_score !== undefined ? r : undefined)
  if (!sym) return ''

  const score = pick(sym, 'ml_risk_score', 'mlRiskScore')
  const level = pick(sym, 'risk_level', 'riskLevel')
  const model = pick(sym, 'model_type', 'modelType')
  const conf = pick(sym, 'confidence')
  const critical = normLists(pick(sym, 'critical_findings', 'criticalFindings'))

  const severityKeys = [
    ['age', 'Age'],
    ['smoking', 'Smoking'],
    ['passive_smoker', 'Passive smoking'],
    ['coughing_blood', 'Coughing blood'],
    ['chest_pain', 'Chest pain'],
    ['weight_loss', 'Weight loss'],
    ['shortness_of_breath', 'Shortness of breath'],
    ['fatigue', 'Fatigue'],
    ['clubbing', 'Finger clubbing'],
    ['wheezing', 'Wheezing'],
    ['dry_cough', 'Dry cough'],
    ['family_history', 'Family history'],
  ] as const
  const factors = severityKeys
    .map(([k, label]) => ({ label, v: Number(sym[k]) }))
    .filter((f) => Number.isFinite(f.v))
    .sort((a, b) => b.v - a.v)
    .slice(0, 6)
    .map((f) => `<li><b>${esc(f.label)}</b> — severity ${f.v}/8</li>`)
    .join('')

  let criticalHtml = ''
  if (critical.length) {
    criticalHtml = `<div class="finding-bad"><span class="dot"></span><b>Critical flags:</b> ${critical
      .map((c: any) => esc(c))
      .join('; ')}</div>`
  }

  return `<h2><span class="secnum">2</span>Symptom &amp; Risk Assessment
    <span class="secsub">Ensemble machine-learning risk model</span></h2>
    ${criticalHtml}
    <table class="data-table"><thead><tr><th>ML risk score</th><th>Risk level</th><th>Model confidence</th><th>Model</th></tr></thead>
    <tbody><tr><td>${score != null ? esc(score) + '%' : '—'}</td><td><span class="badge ${riskClass(level)}">${esc(level || '—')}</span></td><td>${conf != null ? esc(conf) + '%' : '—'}</td><td>${esc(model || 'Ensemble (clinical factors)')}</td></tr></tbody></table>
    ${factors ? `<div class="sub-sec"><div class="sub-head">Top contributing factors</div><ul class="factors">${factors}</ul></div>` : ''}`
}

function buildAdvisory(r: AnyResult): string {
  const docs = normLists(pick(r, 'doctors_to_consult', 'doctorsToConsult'))
  const meds = normLists(pick(r, 'medications_info', 'medicationsInfo'))
  const steps = normLists(
    pick(r, 'recommended_next_steps', 'recommendedNextSteps', 'simple_steps', 'care_plan') as any
  )
  const whatThis = pick(
    pick(r, 'advisory_findings', 'advisory_result'),
    'what_this_means',
    'simple_title'
  )

  let html = `<h2><span class="secnum">3</span>Clinical Recommendations
    <span class="secsub">Specialist handoff · follow-up plan · supportive care</span></h2>`

  if (whatThis) {
    html += `<p class="note">${esc(whatThis)}</p>`
  }

  const stepsArr = Array.isArray(steps)
    ? steps
    : steps
      ? (() => {
          try {
            const o = JSON.parse(steps)
            return Array.isArray(o) ? o : []
          } catch {
            return [steps]
          }
        })()
      : []
  const stepItems = stepsArr
    .map((s: any, i: number) => {
      const txt = typeof s === 'string' ? s : typeof s === 'object' ? s.title ?? s.detail ?? '' : ''
      return txt ? `<li><span class="stepno">${i + 1}</span>${esc(txt)}</li>` : ''
    })
    .join('')

  if (docs.length) {
    html += `<div class="sub-sec"><div class="sub-head">Recommended specialists</div>
      <div class="doc-grid">${docs
        .map(
          (d: AnyResult) =>
            `<div class="doc-card"><div class="doc-name">${esc(d.name || '—')}</div><div class="doc-dept">${esc(d.department || 'Specialist')}</div>${d.why_visit ? `<div class="doc-why">${esc(d.why_visit)}</div>` : ''}</div>`
        )
        .join('')}</div></div>`
  }

  if (meds.length) {
    html += `<div class="sub-sec"><div class="sub-head">Medication information (educational — prescribe only with a physician)</div>
      ${meds
        .map(
          (m: AnyResult) =>
            `<div class="med"><span class="med-name">${esc(m.name || '—')}</span>
            ${m.type ? `<span class="med-type">${esc(m.type)}</span>` : ''}
            ${m.what_it_does ? `<span class="med-desc">${esc(m.what_it_does)}</span>` : ''}
            ${m.simple_tip ? `<span class="med-tip">${esc(m.simple_tip)}</span>` : ''}</div>`
        )
        .join('')}</div>`
  }

  if (stepItems) {
    html += `<div class="sub-sec"><div class="sub-head">Recommended follow-up steps</div><ol class="steps">${stepItems}</ol></div>`
  }
  return html
}

function buildLiterature(r: AnyResult): string {
  let chunks = normLists(pick(r, 'literature_findings', 'literatureFindings'))
  const litResult = pick(r, 'literature_result')
  if (!chunks.length && litResult) {
    chunks = normLists(pick(litResult, 'context_chunks', 'papers'))
  }
  if (!chunks.length) return ''
  const seen = new Set<string>()
  const rows = chunks
    .filter((c: AnyResult) => {
      const id = c.pmid ?? c.url ?? c.title ?? ''
      if (seen.has(id)) return false
      seen.add(id)
      return true
    })
    .slice(0, 6)
  if (!rows.length) return ''
  const link = (c: AnyResult) => {
    const url = c.url || (c.pmid ? `https://pubmed.ncbi.nlm.nih.gov/${esc(c.pmid)}/` : '')
    return url ? ` <a href="${url}">${url}</a>` : ''
  }
  return `<h2><span class="secnum">4</span>Evidence &amp; References
    <span class="secsub">Live PubMed retrieval supporting this pathway</span></h2>
    <ol class="refs">${rows
      .map(
        (c: AnyResult) =>
          `<li><div class="ref-title">${esc(c.title || 'Untitled')}</div>
          <div class="ref-meta">${esc(c.journal || 'peer-reviewed journal')}${c.pub_date ? ` · ${esc(c.pub_date)}` : ''}${c.pmid ? ` · PMID ${esc(c.pmid)}` : ''}${link(c)}</div></li>`
      )
      .join('')}</ol>`
}

function buildFooter(now: Date): string {
  return `<footer>
    <div class="sign-row">
      <div class="sig"><div class="sig-line"></div><div class="sig-label">Reviewing physician</div></div>
      <div class="sig"><div class="sig-line"></div><div class="sig-label">Patient acknowledgment</div></div>
    </div>
    <div class="disclaimer">
      <b>IMPORTANT NOTICE.</b> This report is generated automatically by the OncoAgent artificial-intelligence
      screening system for educational and research purposes. It is <b>not</b> a diagnosis and is not a substitute
      for professional medical advice, diagnosis, or treatment. All AI findings — including lesion detection, risk
      scores and medication references — must be reviewed and confirmed by a licensed physician. Never ignore professional
      medical advice or delay seeking it because of content generated by this system.
    </div>
    <div class="foot">OncoAgent™ Multi-Agent Cancer Screening System · Report № ${reportStamp(now)} · Generated ${fmtDate(now)} ${fmtTime(now)} · Confidential patient draft</div>
  </footer>`
}

export function buildReportHtml(r: AnyResult): string {
  const now = new Date()

  const summaryHtml = buildSummary(r)
  const imagingHtml = buildImaging(r)
  const symptomHtml = buildSymptoms(r)
  const advisoryHtml = buildAdvisory(r)
  const litHtml = buildLiterature(r)

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>OncoAgent — Clinical Support Report</title>
<style>
  @media print {
    @page { size: A4; margin: 14mm 12mm; }
    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    section, h2 { page-break-inside: avoid; }
  }
  * { box-sizing: border-box; }
  body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1f2933; background: #e8ebf0; margin: 0; }
  .page { max-width: 840px; margin: 0 auto; background: #fff; padding: 42px 48px 34px; box-shadow: 0 18px 60px rgba(15, 23, 42, 0.18); }
  .letterhead { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #0f2a43; padding-bottom: 14px; }
  .brand { font-size: 22px; font-weight: 800; color: #0f2a43; letter-spacing: 0.02em; }
  .brand .mark { color: #0e9f6e; margin-right: 4px; }
  .brand-sub { font-size: 11px; color: #526274; letter-spacing: 0.06em; text-transform: uppercase; margin-top: 2px; }
  .report-id { text-align: right; }
  .rid { font-size: 12px; font-weight: 700; color: #0f2a43; letter-spacing: 0.08em; }
  .rid-sub { font-size: 10px; color: #8a94a6; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px; }
  .title-block { text-align: center; border-bottom: 1px solid #dfe4ec; padding: 20px 0 16px; }
  h1 { font-size: 21px; margin: 0; color: #0f2a43; letter-spacing: 0.02em; }
  .subtitle { font-size: 11.5px; color: #66748a; margin-top: 6px; }
  h2 { font-size: 14px; color: #0f2a43; border-left: 4px solid #0e9f6e; padding-left: 10px; margin: 26px 0 10px; letter-spacing: 0.02em; }
  .secnum { font-size: 12px; color: #0e9f6e; margin-right: 8px; font-weight: 800; }
  .secsub { font-size: 11px; color: #7d8ba1; font-weight: 500; margin-left: 8px; }
  .meta-table { width: 100%; border-collapse: collapse; margin-top: 14px; }
  .meta-table td { vertical-align: top; padding: 6px 10px 6px 0; }
  .field { margin-bottom: 6px; }
  .fk { display: block; font-size: 9.5px; text-transform: uppercase; letter-spacing: 0.07em; color: #8a94a6; margin-bottom: 1px; }
  .fv { display: block; font-size: 12.5px; color: #1f2933; font-weight: 600; }
  .nowrap { white-space: nowrap; }
  .summary-band { background: #f4f8fb; border: 1px solid #dbe6ef; border-radius: 10px; padding: 16px 18px; margin-top: 22px; }
  .cells { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 6px; }
  .cell { flex: 1 1 120px; }
  .ck { display: block; font-size: 9.5px; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7a90; }
  .cv { font-size: 15px; font-weight: 700; color: #14324f; }
  .cv.big { font-size: 22px; color: #0f2a43; }
  .summary-text { font-size: 12.5px; line-height: 1.55; color: #34495e; margin: 12px 0 0; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 700; }
  .risk-low { background: #d9f5e4; color: #0b6b3f; }
  .risk-mid { background: #fdf0d6; color: #92610a; }
  .risk-high { background: #fde0e0; color: #a1151f; }
  .data-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
  .data-table th { background: #0f2a43; color: #fff; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; padding: 7px 9px; text-align: left; }
  .data-table td { font-size: 12px; padding: 8px 9px; border-bottom: 1px solid #e6ebf2; color: #26374d; }
  .data-table tr:nth-child(even) td { background: #f7f9fc; }
  .finding-bad { border: 1px solid #f3c1c1; background: #fdf1f1; color: #8f1d26; border-radius: 8px; padding: 10px 14px; font-size: 12.5px; margin: 10px 0; line-height: 1.5; }
  .finding-good { border: 1px solid #bfe7d2; background: #f0faf4; color: #116b3e; border-radius: 8px; padding: 10px 14px; font-size: 12.5px; margin: 10px 0; line-height: 1.5; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: currentColor; margin-right: 6px; }
  .sub-sec { margin: 12px 0; }
  .sub-head { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #526274; margin: 10px 0 6px; }
  .mono { font-family: Consolas, 'Courier New', monospace; font-size: 11.5px; color: #3b4c61; background: #f4f6f9; border: 1px solid #e3e8ef; border-radius: 6px; padding: 8px 10px; }
  .overlay img { display: block; max-width: 100%; border: 1px solid #dde3ec; border-radius: 8px; margin-top: 8px; }
  .doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; margin-top: 6px; }
  .doc-card { border: 1px solid #dde3ec; border-radius: 8px; padding: 10px 12px; background: #fbfcfe; }
  .doc-name { font-size: 12.5px; font-weight: 700; color: #14324f; }
  .doc-dept { font-size: 11px; color: #0e9f6e; font-weight: 600; margin-top: 2px; }
  .doc-why { font-size: 11px; color: #5a6b80; margin-top: 5px; line-height: 1.45; }
  .med { border: 1px solid #e3d9f2; background: #faf7fe; border-radius: 8px; padding: 9px 12px; margin: 6px 0; }
  .med-name { font-weight: 700; font-size: 12.5px; color: #3b2670; }
  .med-type { display: inline-block; margin-left: 8px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #7c5cbf; }
  .med-desc, .med-tip { display: block; font-size: 11.5px; color: #4a5a6e; margin-top: 4px; line-height: 1.45; }
  .med-tip { color: #8394a8; font-style: italic; }
  .steps { margin: 6px 0 0; padding-left: 0; list-style: none; counter-reset: st; }
  .steps li { display: flex; gap: 10px; align-items: baseline; font-size: 12.5px; color: #26374d; line-height: 1.5; margin: 7px 0; }
  .stepno { flex: 0 0 auto; width: 20px; height: 20px; border-radius: 50%; background: #0e9f6e; color: #fff; font-size: 11px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; margin-top: 1px; }
  .factors { columns: 2; column-gap: 24px; font-size: 12.5px; color: #26374d; margin: 6px 0 0; padding-left: 18px; line-height: 1.7; }
  .refs { font-size: 12px; padding-left: 20px; color: #2c3e50; }
  .refs li { margin: 8px 0; line-height: 1.5; }
  .ref-title { font-weight: 600; color: #14324f; }
  .ref-meta { font-size: 10.5px; color: #6b7a90; }
  .ref-meta a { color: #1661a8; word-break: break-all; }
  .note { font-size: 12.5px; color: #34495e; line-height: 1.55; }
  footer { margin-top: 34px; }
  .sign-row { display: flex; gap: 60px; margin: 10px 0 22px; }
  .sig { flex: 1; }
  .sig-line { border-bottom: 1px solid #97a3b5; height: 26px; }
  .sig-label { font-size: 9.5px; text-transform: uppercase; letter-spacing: 0.07em; color: #7d8ba1; margin-top: 5px; }
  .disclaimer { font-size: 10.5px; line-height: 1.55; color: #5a6b80; border-top: 1px solid #dfe4ec; padding-top: 12px; }
  .foot { text-align: center; font-size: 9.5px; color: #8a94a6; margin-top: 12px; letter-spacing: 0.03em; }
</style>
</head>
<body>
  <div class="page">
    ${buildHeader(r, now)}
    ${summaryHtml}
    ${imagingHtml}
    ${symptomHtml}
    ${advisoryHtml}
    ${litHtml}
    ${buildFooter(now)}
  </div>
</body>
</html>`
}

export function openProfessionalReport(r: AnyResult): void {
  const win = window.open('', '_blank', 'width=900,height=1080,scrollbars=yes')
  if (!win) {
    alert('Please allow pop-ups to download the clinical report.')
    return
  }
  win.document.open()
  win.document.write(buildReportHtml(r || {}))
  win.document.close()
  const finish = () => {
    win.focus()
    window.setTimeout(() => win.print(), 250)
  }
  if (win.document.readyState === 'complete') finish()
  else win.onload = finish
}