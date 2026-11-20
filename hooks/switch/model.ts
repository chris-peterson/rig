/**
 * The switch pane's model: what `rig switch --state` reports, the picks the
 * person makes over it, and what a launch with those picks loads. A port of
 * scripts/rig's plan(), summary(), graph_of() and the picker's state and
 * toggles (LAUNCH-07, -09, -11, PIN-12, PIN-13), kept pure so it tests alone.
 */

export const BASE = 'base'
export const FULL = 'full'
export const PICKED = 'picked'
export const PIN = '📌'

export type Rig = {
  name: string
  built_in: boolean
  default: boolean
  plugins: readonly string[]
}

export type Pin = {
  plugin: string
  path: string
  display: string
  age: string
}

/** What `rig switch --state` prints. */
export type State = {
  launched: boolean
  rigs: readonly Rig[]
  installed: readonly string[]
  pins: readonly Pin[]
  here: readonly string[]
  current: {
    rigs: readonly string[]
    added: readonly string[]
    removed: readonly string[]
    pins: Readonly<Record<string, boolean>>
  }
}

/** The person's choices: the rigs past base, plugins picked and taken out, and each pin's checkout choice. */
export type Picks = {
  rigs: readonly string[]
  added: readonly string[]
  removed: readonly string[]
  choices: Readonly<Record<string, boolean>>
}

export type Offer = {
  pin: Pin
  /** The launch's plugins include the pin's plugin. */
  inRig: boolean
  /** The pin's checkout holds the session's folder. */
  here: boolean
}

export type Plan = {
  selected: readonly string[]
  /** Each plugin the launch loads, with the rig that adds it (or `picked`). */
  sources: ReadonlyMap<string, string>
  missing: readonly string[]
  offered: readonly Offer[]
  added: readonly string[]
  removed: readonly string[]
}

export type RigState = 'on' | 'partial' | 'off'

const unique = <T>(items: Iterable<T>): T[] => [...new Set(items)]

export const nameOf = (pluginId: string): string => pluginId.split('@')[0] ?? pluginId

/** PIN-08: a pin the rigs include loads, unless the launch starts inside it. */
export const isLocked = (offer: Offer): boolean => offer.inRig && !offer.here

/** PIN-07..09: selected when the rigs include it or the launch starts inside it. */
export const isSelected = (offer: Offer): boolean => offer.inRig || offer.here

/** Whether the pin's checkout loads under these choices. */
export function loads(offer: Offer, choices: Readonly<Record<string, boolean>>): boolean {
  return isLocked(offer) || (choices[offer.pin.path] ?? isSelected(offer))
}

export function rigNamed(state: State, name: string): Rig | undefined {
  return state.rigs.find(rig => rig.name === name)
}

/** The rigs past base, in the order the state lists them, without repeats or unknown names. */
export function selection(state: State, names: Iterable<string>): string[] {
  const chosen = new Set(names)

  return state.rigs.map(rig => rig.name).filter(name => name !== BASE && chosen.has(name))
}

/**
 * RIG-02, RIG-03, RIG-10, LAUNCH-11: base's plugins, then each chosen rig's,
 * without repeats, less the ones taken out, then the ones picked on their own.
 */
export function planOf(state: State, picks: Picks): Plan {
  const removed = unique(picks.removed)
  const sources = new Map<string, string>()

  for (const pluginId of rigNamed(state, BASE)?.plugins ?? []) {
    if (!removed.includes(pluginId)) {
      sources.set(pluginId, BASE)
    }
  }

  for (const name of picks.rigs) {
    for (const pluginId of rigNamed(state, name)?.plugins ?? []) {
      if (!removed.includes(pluginId) && !sources.has(pluginId)) {
        sources.set(pluginId, name)
      }
    }
  }

  const added = unique(picks.added).filter(p => !sources.has(p) && !removed.includes(p))

  for (const pluginId of added) {
    sources.set(pluginId, PICKED)
  }

  const inRig = new Set([...sources.keys()].map(nameOf))
  const installed = new Set(state.installed)

  return {
    selected: [...picks.rigs],
    sources,
    missing: [...sources.keys()].filter(p => !installed.has(p)),
    offered: state.pins.map(pin => ({ pin, inRig: inRig.has(pin.plugin), here: state.here.includes(pin.path) })),
    added,
    removed,
  }
}

/** The picks the session runs with now: its rigs and plugins, and its checkouts as a choice where one is open. */
export function initialPicks(state: State): Picks {
  const base: Picks = {
    rigs: selection(state, state.current.rigs),
    added: [...state.current.added],
    removed: [...state.current.removed],
    choices: {},
  }

  const choices: Record<string, boolean> = {}

  for (const offer of planOf(state, base).offered) {
    const loaded = state.current.pins[offer.pin.path]

    if (!isLocked(offer) && loaded !== undefined) {
      choices[offer.pin.path] = loaded
    }
  }

  return { ...base, choices }
}

/** The rigs a launch uses, then the plugins picked on their own (LAUNCH-11): `base + web + x@m - a@m`. */
export function label(selected: readonly string[], added: readonly string[] = [], removed: readonly string[] = []): string {
  return [BASE, ...selected, ...added].join(' + ') + removed.map(p => ` - ${p}`).join('')
}

/** LAUNCH-02, LAUNCH-12: `base + web: 9 plugins`, or `all 40 plugins` with full. */
export function summary(plan: Plan): string {
  const count = plan.sources.size
  const plugins = `${count} plugin${count === 1 ? '' : 's'}`

  if (!plan.selected.includes(FULL)) {
    return `${label(plan.selected, plan.added, plan.removed)}: ${plugins}`
  }

  return plan.removed.length > 0 ? `all but ${plan.removed.join(', ')}: ${plugins}` : `all ${plugins}`
}

/** LAUNCH-11: a rig is partly loaded when plugins of it are taken out, or, not chosen, picked. */
export function rigState(rig: Rig, plan: Plan): RigState {
  if (rig.name === BASE || plan.selected.includes(rig.name)) {
    return rig.plugins.some(p => plan.removed.includes(p)) ? 'partial' : 'on'
  }

  return rig.name !== FULL && rig.plugins.some(p => plan.added.includes(p)) ? 'partial' : 'off'
}

/**
 * LAUNCH-09, LAUNCH-11: a rig loaded whole goes, and one partly loaded or not
 * at all comes in whole. Every launch loads base, and full holds every other
 * rig's plugins, so full goes alone.
 */
export function toggleRig(state: State, picks: Picks, name: string): Picks {
  const rig = rigNamed(state, name)

  if (!rig) {
    return picks
  }

  const plan = planOf(state, picks)
  const plugins = new Set(rig.plugins)
  let chosen = new Set(picks.rigs)
  let added = [...picks.added]
  let removed = [...picks.removed]

  if (rigState(rig, plan) === 'on') {
    if (name === BASE) {
      return picks
    }

    chosen.delete(name)
    added = added.filter(p => !plugins.has(p))
  } else {
    removed = removed.filter(p => !plugins.has(p))

    if (name === FULL) {
      chosen = new Set([FULL])
      added = []
    } else if (name !== BASE) {
      chosen.delete(FULL)
      chosen.add(name)
    }
  }

  return { ...picks, rigs: selection(state, chosen), added, removed }
}

/** LAUNCH-11: take a plugin out of the launch, or put it in, whatever rigs hold it; null for a bare pin. */
export function togglePlugin(state: State, picks: Picks, pluginId: string): Picks | null {
  if (!pluginId.includes('@')) {
    return null
  }

  const plan = planOf(state, picks)
  let added = [...picks.added]
  let removed = [...picks.removed]

  if (plan.sources.has(pluginId)) {
    if (added.includes(pluginId)) {
      added = added.filter(p => p !== pluginId)
    } else {
      removed.push(pluginId)
    }
  } else {
    removed = removed.filter(p => p !== pluginId)

    if (!planOf(state, { ...picks, added, removed }).sources.has(pluginId)) {
      added.push(pluginId)
    }
  }

  return { ...picks, added, removed }
}

export function offerFor(plan: Plan, pluginId: string): Offer | undefined {
  return plan.offered.find(offer => offer.pin.plugin === nameOf(pluginId))
}

/** Flip whether a pin's checkout loads; null when its rigs lock it in. */
export function togglePin(state: State, picks: Picks, pluginId: string): Picks | null {
  const offer = offerFor(planOf(state, picks), pluginId)

  if (!offer || isLocked(offer)) {
    return null
  }

  return { ...picks, choices: { ...picks.choices, [offer.pin.path]: !loads(offer, picks.choices) } }
}

/** What `rig switch --picks` records: the rigs, the plugins picked and taken out, and whether each checkout loads. */
export function recorded(state: State, picks: Picks): {
  rigs: string[]
  added: string[]
  removed: string[]
  pins: Record<string, boolean>
} {
  const plan = planOf(state, picks)

  return {
    rigs: [...plan.selected],
    added: [...plan.added],
    removed: [...plan.removed],
    pins: Object.fromEntries(plan.offered.map(offer => [offer.pin.path, loads(offer, picks.choices)])),
  }
}

/** PIN-13: the pin dialog's state line. */
export function pinStateOf(plan: Plan, pluginId: string, choices: Readonly<Record<string, boolean>>): string {
  const offer = offerFor(plan, pluginId)

  if (!offer) {
    return ''
  }

  if (isLocked(offer)) {
    return 'in these rigs, so the checkout loads'
  }

  if (loads(offer, choices)) {
    return 'the checkout loads'
  }

  return plan.sources.has(pluginId) ? 'the installed copy loads' : 'not loaded'
}

/** The toast for each pin holding the session's folder. */
export function hereNotes(state: State, picks: Picks): string[] {
  const plan = planOf(state, picks)

  return plan.offered
    .filter(offer => offer.here)
    .map(offer => {
      const what = loads(offer, picks.choices) ? 'its checkout loads' : 'the installed copy loads'

      return `${PIN} ${offer.pin.plugin} holds this folder: ${what}`
    })
}

// ---------------------------------------------------------------- the graph

/** The terminal columns text takes: two for a wide character such as 📌. */
export function cells(text: string): number {
  let width = 0

  for (const char of text) {
    const code = char.codePointAt(0) ?? 0
    const isWide =
      code >= 0x1f300 ||
      (code >= 0x1100 && code <= 0x115f) ||
      (code >= 0x2e80 && code <= 0xa4cf) ||
      (code >= 0xac00 && code <= 0xd7a3) ||
      (code >= 0xf900 && code <= 0xfaff) ||
      (code >= 0xfe30 && code <= 0xfe4f) ||
      (code >= 0xff00 && code <= 0xff60) ||
      (code >= 0xffe0 && code <= 0xffe6)

    width += isWide ? 2 : 1
  }

  return width
}

export function pad(text: string, width: number): string {
  return text + ' '.repeat(Math.max(width - cells(text), 0))
}

/** Python's str.center, so a mark sits where `rig list --graph` puts it. */
export function center(text: string, width: number): string {
  const margin = width - text.length

  if (margin <= 0) {
    return text
  }

  const left = Math.floor(margin / 2) + (margin & width & 1)

  return ' '.repeat(left) + text + ' '.repeat(margin - left)
}

/** PIN-12: the one way rig writes a plugin's name, marked 📌 in front when a checkout is pinned for it. */
export function pluginCell(pluginId: string, pins: readonly Pin[]): string {
  return pins.some(pin => pin.plugin === nameOf(pluginId)) ? `${PIN} ${pluginId}` : pluginId
}

export type Graph = {
  rigs: readonly Rig[]
  rows: readonly string[]
  labels: readonly string[]
  heads: readonly string[]
  width: number
  /** Room for a 📌 in front of the names, when any row is pinned. */
  margin: string
}

/** RIG-14, LAUNCH-07: each rig's plugins together, then the installed plugins no rig names, then pins for none of those. */
export function graphOf(state: State): Graph {
  const rows = unique(state.rigs.flatMap(rig => rig.plugins))

  rows.push(...state.installed.filter(p => !rows.includes(p)))

  const shown = new Set(rows.map(nameOf))

  rows.push(...state.pins.map(pin => pin.plugin).filter(name => !shown.has(name)))

  const pinned = (p: string): boolean => state.pins.some(pin => pin.plugin === nameOf(p))
  const margin = rows.some(pinned) ? ' '.repeat(cells(`${PIN} `)) : ''
  const labels = rows.map(p => (pinned(p) ? pluginCell(p, state.pins) : margin + p))
  const heads = state.rigs.map(rig => (rig.default ? '★' : '') + rig.name)
  const width = Math.max(cells(margin + 'plugin'), ...labels.map(cells))

  return { rigs: state.rigs, rows, labels, heads, width, margin }
}

/** Whether row `pluginId` of the graph loads under the plan: a bare pin row loads when its plugin does. */
export function rowLoads(plan: Plan, pluginId: string): boolean {
  return [...plan.sources.keys()].some(p => p === pluginId || nameOf(p) === pluginId)
}

/** LAUNCH-07, LAUNCH-11: ★ when a rig is a default, ✓ when a rig besides base loads, ◐ while a rig loads in part. */
export function legendOf(graph: Graph, states: readonly RigState[]): { mark: string; meaning: string }[] {
  const keys = [
    { mark: '★', meaning: 'default', shown: graph.rigs.some(rig => rig.default) },
    { mark: '✓', meaning: 'loads', shown: states.slice(1).includes('on') },
    { mark: '◐', meaning: 'part', shown: states.includes('partial') },
  ]

  return keys.filter(key => key.shown).map(({ mark, meaning }) => ({ mark, meaning }))
}
