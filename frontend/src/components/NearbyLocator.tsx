import { useRef, useState } from 'react'
import { MapPin, Loader2, Hospital, User, Pill, Info, Navigation, RefreshCcw } from 'lucide-react'
import { motion, AnimatePresence } from 'motion/react'
import { apiClient } from '../services/api'

type Place = {
  name: string
  kind: string
  address: string
  phone: string
  website?: string
  opening_hours?: string
  latitude?: number
  lat?: number
  lon?: number
  longitude?: number
  distance_km: number
}

type Kind = 'hospital' | 'doctor' | 'pharmacy'

const KIND_META: Record<Kind, { label: string; icon: any; color: string }> = {
  hospital: { label: 'Hospitals & Clinics', icon: Hospital, color: 'emerald' },
  doctor: { label: 'Doctors & Specialists', icon: User, color: 'cyan' },
  pharmacy: { label: 'Pharmacies', icon: Pill, color: 'violet' },
}

function mapsUrl(lat?: number, lon?: number) {
  if (lat == null || lon == null) return ''
  return `https://www.google.com/maps?q=${lat},${lon}`
}

export default function NearbyLocator({
  specialty,
  radius = 8,
}: {
  specialty?: string
  radius?: number
}) {
  const [open, setOpen] = useState(false)
  const [state, setState] = useState<'idle' | 'locating' | 'loading' | 'done' | 'error' | 'denied'>('idle')
  const [loc, setLoc] = useState<{ lat: number; lon: number } | null>(null)
  const [data, setData] = useState<Record<Kind, Place[]>>({ hospital: [], doctor: [], pharmacy: [] })
  const [active, setActive] = useState<Kind>('hospital')
  const [manualLat, setManualLat] = useState('')
  const [manualLon, setManualLon] = useState('')
  const loadedOnce = useRef(false)

  const fetchAll = async (lat: number, lon: number) => {
    setLoc({ lat, lon })
    setState('loading')
    try {
      const kinds: Kind[] = ['hospital', 'doctor', 'pharmacy']
      const [h, d, p] = await Promise.all(
        kinds.map((k) =>
          apiClient
            .get('/api/v1/nearby', { params: { lat, lon, radius, kind: k } })
            .then((r) => r.data?.nearby || [])
            .catch(() => [])
        )
      )
      setData({ hospital: h, doctor: d, pharmacy: p })
      setState('done')
      loadedOnce.current = true
    } catch {
      setState('error')
    }
  }

  const startLocating = () => {
    setOpen(true)
    if (!('geolocation' in navigator)) {
      setState('denied')
      return
    }
    setState('locating')
    navigator.geolocation.getCurrentPosition(
      (pos) => fetchAll(pos.coords.latitude, pos.coords.longitude),
      () => setState('denied'),
      { timeout: 8000, maximumAge: 600000 }
    )
  }

  const useManual = () => {
    const lat = parseFloat(manualLat)
    const lon = parseFloat(manualLon)
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return
    fetchAll(lat, lon)
  }

  const list = data[active]

  const sections = (['hospital', 'doctor', 'pharmacy'] as Kind[]).map((k) => {
    const meta = KIND_META[k]
    return (
      <button
        key={k}
        onClick={() => setActive(k)}
        className={`flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors ${
          active === k
            ? 'bg-white/10 border border-white/15 text-white'
            : 'text-slate-400 border border-transparent hover:text-slate-200'
        }`}
      >
        <meta.icon className="w-3.5 h-3.5" />
        {meta.label}
        <span className="text-slate-500">{data[k].length}</span>
      </button>
    )
  })

  return (
    <div>
      {!open ? (
        <button onClick={startLocating} className="btn-secondary w-full py-3 group">
          <MapPin className="w-4 h-4 text-emerald-300" />
          Find nearby hospitals, specialists & pharmacies
          <Navigation className="w-3.5 h-3.5 text-slate-500 transition-transform group-hover:translate-x-0.5" />
        </button>
      ) : (
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-xl p-5">
              <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-white">
                  <MapPin className="w-4 h-4 text-emerald-300" />
                  Healthcare nearby
                  {specialty && (
                    <span className="glass-chip text-[10px] text-cyan-300 px-2 py-0.5">Look for: {specialty}</span>
                  )}
                </h4>
                {(state === 'done' || state === 'error') && loc && (
                  <button
                    onClick={() => fetchAll(loc.lat, loc.lon)}
                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    <RefreshCcw className="w-3 h-3" /> Refresh
                  </button>
                )}
              </div>

              {state === 'locating' && (
                <div className="flex items-center gap-2 text-sm text-slate-400 py-6">
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-300" />
                  Getting your location…
                </div>
              )}

              {state === 'loading' && (
                <div className="space-y-2 py-2">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className="h-12 rounded-lg bg-white/[0.04] animate-pulse" />
                  ))}
                </div>
              )}

              {state === 'denied' && (
                <div className="py-4">
                  <p className="text-sm text-slate-400 mb-3">
                    Location permission is off. Enter your coordinates manually to continue:
                  </p>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input
                      value={manualLat}
                      onChange={(e) => setManualLat(e.target.value)}
                      placeholder="Latitude (e.g. 40.7580)"
                      className="input-field"
                    />
                    <input
                      value={manualLon}
                      onChange={(e) => setManualLon(e.target.value)}
                      placeholder="Longitude (e.g. -73.9855)"
                      className="input-field"
                    />
                    <button onClick={useManual} className="btn-primary whitespace-nowrap">
                      Search
                    </button>
                  </div>
                </div>
              )}

              {state === 'error' && (
                <div className="text-sm text-amber-300 py-4">
                  Couldn't reach the healthcare locator. The service may be temporarily unavailable.
                </div>
              )}

              {state === 'done' && (
                <div>
                  <div className="flex flex-wrap gap-2 mb-4">{sections}</div>
                  {loc && (
                    <p className="text-[11px] font-mono text-slate-500 mb-3">
                      {loc.lat.toFixed(4)}, {loc.lon.toFixed(4)} · search radius {radius} km · data from OpenStreetMap
                    </p>
                  )}
                  {list.length === 0 ? (
                    <p className="text-sm text-slate-400 py-4">
                      No {active === 'doctor' ? 'doctors' : active === 'pharmacy' ? 'pharmacies' : 'hospitals'} found
                      within {radius} km. Try a larger radius.
                    </p>
                  ) : (
                    <ul className="grid sm:grid-cols-2 gap-2 max-h-96 overflow-auto pr-1">
                      {list.map((place, i) => (
                        <li
                          key={i}
                          className="group rounded-xl border border-white/[0.07] bg-white/[0.03] p-3 hover:bg-white/[0.06] transition-colors"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="text-sm font-medium text-white">{place.name}</div>
                              {place.address && (
                                <div className="text-xs text-slate-500 mt-0.5">{place.address}</div>
                              )}
                              {place.phone && <div className="text-xs text-slate-400 mt-0.5">{place.phone}</div>}
                            </div>
                            <div className="flex flex-col items-end gap-1 shrink-0">
                              <span className="text-xs font-mono text-emerald-300">{place.distance_km} km</span>
                              <a
                                href={mapsUrl(place.lat ?? place.latitude, place.lon ?? place.longitude)}
                                target="_blank"
                                rel="noreferrer"
                                className="text-[11px] text-cyan-300 hover:text-cyan-200 flex items-center gap-0.5"
                              >
                                Map <Navigation className="w-2.5 h-2.5" />
                              </a>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              <p className="mt-4 flex items-start gap-1.5 text-[10px] text-slate-600 leading-relaxed">
                <Info className="w-3 h-3 mt-0.5 shrink-0" />
                Locations come from the open OpenStreetMap community database and may be incomplete. Always confirm a
                facility's details and whether a specialist treats your condition before visiting.
              </p>
            </div>
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  )
}