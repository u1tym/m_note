/** 行動予定（action）パーツの data JSON */

export interface ActionPlanPoint {
  place: string
  time?: string
  arrive?: string
  depart?: string
}

export interface ActionPlanLeg {
  memo: string
}

export interface ActionPlanData {
  points: ActionPlanPoint[]
  legs: ActionPlanLeg[]
}

function strip(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function pointIsEmpty(point: ActionPlanPoint): boolean {
  return !strip(point.place) && !strip(point.time) && !strip(point.arrive) && !strip(point.depart)
}

export function emptyActionPlan(): ActionPlanData {
  return {
    points: [{ place: '', time: '' }],
    legs: [],
  }
}

export function parseActionPlan(data: string): ActionPlanData | null {
  try {
    const raw = JSON.parse(data) as unknown
    if (!raw || typeof raw !== 'object') {
      return null
    }
    const obj = raw as Record<string, unknown>
    if (!Array.isArray(obj.points) || obj.points.length < 1) {
      return null
    }
    const points = obj.points.map((item) => {
      const p = item as Record<string, unknown>
      return {
        place: strip(p.place),
        time: strip(p.time) || undefined,
        arrive: strip(p.arrive) || undefined,
        depart: strip(p.depart) || undefined,
      }
    })
    const legs = Array.isArray(obj.legs)
      ? obj.legs.map((item) => {
          const leg = item as Record<string, unknown>
          return { memo: strip(leg.memo) }
        })
      : []
    return normalizeActionPlan({ points, legs })
  } catch {
    return null
  }
}

export function normalizeActionPlan(plan: ActionPlanData): ActionPlanData {
  const editor = normalizeActionPlanForEditor(plan)
  const points: ActionPlanPoint[] = []

  editor.points.forEach((point, index) => {
    if (index === 0) {
      points.push({
        place: strip(point.place),
        time: strip(point.time),
      })
      return
    }
    if (pointIsEmpty(point)) {
      return
    }
    const normalized: ActionPlanPoint = { place: strip(point.place) }
    const time = strip(point.time)
    const arrive = strip(point.arrive)
    const depart = strip(point.depart)
    if (arrive || depart) {
      if (arrive) {
        normalized.arrive = arrive
      }
      if (depart) {
        normalized.depart = depart
      }
    } else if (time) {
      normalized.time = time
    }
    points.push(normalized)
  })

  if (points.length === 0) {
    points.push({ place: '', time: '' })
  }

  const legs: ActionPlanLeg[] = []
  for (let i = 0; i < points.length - 1; i += 1) {
    legs.push({ memo: editor.legs[i]?.memo?.trim() ?? '' })
  }

  return { points, legs }
}

/** 編集中用。空の地点も保持する（地点追加直後のプレースホルダー用） */
export function normalizeActionPlanForEditor(plan: ActionPlanData): ActionPlanData {
  const points = plan.points.map((point, index) => {
    if (index === 0) {
      return {
        place: strip(point.place),
        time: strip(point.time),
      }
    }
    const normalized: ActionPlanPoint = { place: strip(point.place) }
    const time = strip(point.time)
    const arrive = strip(point.arrive)
    const depart = strip(point.depart)
    if (arrive || depart) {
      if (arrive) {
        normalized.arrive = arrive
      }
      if (depart) {
        normalized.depart = depart
      }
    } else if (time) {
      normalized.time = time
    }
    return normalized
  })

  if (points.length === 0) {
    points.push({ place: '', time: '' })
  }

  const legs: ActionPlanLeg[] = []
  for (let i = 0; i < points.length - 1; i += 1) {
    legs.push({ memo: plan.legs[i]?.memo?.trim() ?? '' })
  }

  return { points, legs }
}

export function serializeActionPlan(plan: ActionPlanData): string {
  const normalized = normalizeActionPlan(plan)
  const points = normalized.points.map((point, index) => {
    if (index === 0) {
      return { place: point.place, time: point.time ?? '' }
    }
    const out: ActionPlanPoint = { place: point.place }
    if (point.arrive || point.depart) {
      if (point.arrive) {
        out.arrive = point.arrive
      }
      if (point.depart) {
        out.depart = point.depart
      }
    } else if (point.time) {
      out.time = point.time
    }
    return out
  })
  return JSON.stringify({ points, legs: normalized.legs })
}

export function validateActionPlan(plan: ActionPlanData): string | null {
  const normalized = normalizeActionPlan(plan)
  if (!strip(normalized.points[0]?.place)) {
    return '地点1の場所は必須です'
  }
  if (!strip(normalized.points[0]?.time)) {
    return '地点1の時刻は必須です'
  }
  for (let i = 1; i < normalized.points.length; i += 1) {
    const point = normalized.points[i]
    const hasTime = Boolean(strip(point.time) || strip(point.arrive) || strip(point.depart))
    if (!strip(point.place) && !hasTime) {
      return `地点${i + 1} に場所または時刻を入力してください`
    }
    if (strip(point.time) && (strip(point.arrive) || strip(point.depart))) {
      return `地点${i + 1} は単一時刻と到着・出発を同時に指定できません`
    }
  }
  return null
}

export function formatPointTimes(point: ActionPlanPoint, index: number): string {
  if (index === 0) {
    return strip(point.time)
  }
  if (strip(point.arrive) || strip(point.depart)) {
    const parts: string[] = []
    if (strip(point.arrive)) {
      parts.push(`到着 ${point.arrive}`)
    }
    if (strip(point.depart)) {
      parts.push(`出発 ${point.depart}`)
    }
    return parts.join(' / ')
  }
  return strip(point.time)
}

export function addNextPoint(plan: ActionPlanData): ActionPlanData {
  const normalized = normalizeActionPlanForEditor(plan)
  normalized.points.push({ place: '' })
  normalized.legs.push({ memo: '' })
  return normalized
}

export function removePoint(plan: ActionPlanData, index: number): ActionPlanData {
  if (index <= 0 || index >= plan.points.length) {
    return normalizeActionPlanForEditor(plan)
  }
  const normalized = normalizeActionPlanForEditor(plan)
  normalized.points.splice(index, 1)
  normalized.legs.splice(index - 1, 1)
  return normalizeActionPlanForEditor(normalized)
}

export function pointUsesSplitTime(point: ActionPlanPoint, index: number): boolean {
  if (index === 0) {
    return false
  }
  return Boolean(strip(point.arrive) || strip(point.depart) || (!strip(point.time) && index > 0))
}
