import { useState } from 'react'

interface Props {
  from: Date
  to: Date
  onChange: (from: Date, to: Date) => void
}

const HOUR_MS = 60 * 60 * 1000

const PRESETS: { label: string; range: () => [Date, Date] }[] = [
  { label: 'Last hour', range: () => [new Date(Date.now() - HOUR_MS), new Date()] },
  { label: 'Last 3 hours', range: () => [new Date(Date.now() - 3 * HOUR_MS), new Date()] },
  {
    label: 'Today',
    range: () => {
      const midnight = new Date()
      midnight.setHours(0, 0, 0, 0)
      return [midnight, new Date()]
    },
  },
]

// <input type="datetime-local"> wants "YYYY-MM-DDTHH:mm" in *local* time.
// toISOString() would give UTC, which shows the wrong hour, so build it by hand.
function toInputValue(d: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// A string without an offset is parsed as local time, which is what the user means.
function fromInputValue(value: string): Date | null {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

export default function TimeRangePicker({ from, to, onChange }: Props) {
  // Draft strings let the user type freely; only valid ranges are sent to the parent.
  const [fromDraft, setFromDraft] = useState(toInputValue(from))
  const [toDraft, setToDraft] = useState(toInputValue(to))

  const fromDate = fromInputValue(fromDraft)
  const toDate = fromInputValue(toDraft)
  const error =
    !fromDate || !toDate ? 'Pick both dates' : fromDate > toDate ? '"From" must be before "To"' : null

  function update(nextFrom: string, nextTo: string) {
    setFromDraft(nextFrom)
    setToDraft(nextTo)
    const f = fromInputValue(nextFrom)
    const t = fromInputValue(nextTo)
    if (f && t && f <= t) onChange(f, t)
  }

  function applyPreset(range: () => [Date, Date]) {
    const [f, t] = range()
    update(toInputValue(f), toInputValue(t))
  }

  return (
    <div className="time-range-picker">
      <div className="presets">
        {PRESETS.map((p) => (
          <button key={p.label} type="button" onClick={() => applyPreset(p.range)}>
            {p.label}
          </button>
        ))}
      </div>

      <div className="inputs">
        <label>
          From
          <input
            type="datetime-local"
            value={fromDraft}
            max={toDraft}
            onChange={(e) => update(e.target.value, toDraft)}
          />
        </label>
        <label>
          To
          <input
            type="datetime-local"
            value={toDraft}
            min={fromDraft}
            onChange={(e) => update(fromDraft, e.target.value)}
          />
        </label>
      </div>

      {error && <p className="error">{error}</p>}
    </div>
  )
}
