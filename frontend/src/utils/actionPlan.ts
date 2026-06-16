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

function asString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

/** 保存時: 場所・経由メモは末尾空白のみ削除（文中・先頭の空白は保持） */
function trimEndField(value: unknown): string {
  return asString(value).trimEnd()
}

/** 時刻系は前後空白を削除 */
function trimTime(value: unknown): string {
  return asString(value).trim()
}

function isBlank(value: unknown): boolean {
  return asString(value).trim() === ''
}

function pointIsEmpty(point: ActionPlanPoint): boolean {
  return (
    isBlank(point.place) &&
    isBlank(point.time) &&
    isBlank(point.arrive) &&
    isBlank(point.depart)
  )
}

function planHasContent(plan: ActionPlanData): boolean {
  if (plan.points.some((p) => !pointIsEmpty(p))) {
    return true
  }
  return plan.legs.some((leg) => !isBlank(leg.memo))
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
        place: trimEndField(p.place),
        time: trimTime(p.time) || undefined,
        arrive: trimTime(p.arrive) || undefined,
        depart: trimTime(p.depart) || undefined,
      }
    })
    const legs = Array.isArray(obj.legs)
      ? obj.legs.map((item) => {
          const leg = item as Record<string, unknown>
          return { memo: trimEndField(leg.memo) }
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
      const hasLaterPoints = editor.points.slice(1).some((p) => !pointIsEmpty(p))
      if (pointIsEmpty(point) && !hasLaterPoints) {
        return
      }
      points.push({
        place: trimEndField(point.place),
        time: trimTime(point.time),
      })
      return
    }
    if (pointIsEmpty(point)) {
      return
    }
    const normalized: ActionPlanPoint = { place: trimEndField(point.place) }
    const time = trimTime(point.time)
    const arrive = trimTime(point.arrive)
    const depart = trimTime(point.depart)
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
    legs.push({ memo: trimEndField(editor.legs[i]?.memo) })
  }

  return { points, legs }
}

/** 編集中用。空の地点も保持。場所・経由メモは入力どおり保持する */
export function normalizeActionPlanForEditor(plan: ActionPlanData): ActionPlanData {
  const points = plan.points.map((point, index) => {
    if (index === 0) {
      return {
        place: asString(point.place),
        time: asString(point.time),
      }
    }
    const normalized: ActionPlanPoint = { place: asString(point.place) }
    const time = asString(point.time)
    const arrive = asString(point.arrive)
    const depart = asString(point.depart)
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
    legs.push({ memo: asString(plan.legs[i]?.memo) })
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
  if (!planHasContent(normalized)) {
    return '行動予定の内容を1件以上入力してください'
  }
  for (let i = 1; i < normalized.points.length; i += 1) {
    const point = normalized.points[i]
    const hasTime = Boolean(
      !isBlank(point.time) || !isBlank(point.arrive) || !isBlank(point.depart),
    )
    if (isBlank(point.place) && !hasTime) {
      return `地点${i + 1} に場所または時刻を入力してください`
    }
    if (!isBlank(point.time) && (!isBlank(point.arrive) || !isBlank(point.depart))) {
      return `地点${i + 1} は単一時刻と到着・出発を同時に指定できません`
    }
  }
  return null
}

export function formatPointTimes(point: ActionPlanPoint, index: number): string {
  if (index === 0) {
    return trimTime(point.time)
  }
  if (!isBlank(point.arrive) || !isBlank(point.depart)) {
    const parts: string[] = []
    if (!isBlank(point.arrive)) {
      parts.push(trimTime(point.arrive))
    }
    if (!isBlank(point.depart)) {
      parts.push(trimTime(point.depart))
    }
    return parts.join(' / ')
  }
  return trimTime(point.time)
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
  return Boolean(
    !isBlank(point.arrive) ||
      !isBlank(point.depart) ||
      (isBlank(point.time) && index > 0),
  )
}
