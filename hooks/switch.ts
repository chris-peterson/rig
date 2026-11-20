import type { EngineInterface, On, ProcessRunResult } from 'claude-code'

import * as Model from './switch/model'
import { KEYS, paneView, type PaneModel } from './switch/view'

/** The slash command: `/rig` opens the picker, `/rig <rig>...` switches at once. */
export const COMMAND = 'rig'
export const PANE_ID = 'rig-switch'
export const CANCELLED_TEXT = 'rig switch cancelled'

const RIG_TIMEOUT_MS = 60_000

/** What a failed rig run says: its stderr, else its stdout, else its status. */
function failureOf(result: ProcessRunResult): string {
  return result.stderr.trim() || result.stdout.trim() || `rig exited ${result.exitCode}`
}

function parseState(text: string): Model.State | null {
  try {
    const value: unknown = JSON.parse(text)

    return typeof value === 'object' && value !== null && 'rigs' in value ? (value as Model.State) : null
  } catch {
    return null
  }
}

/** SWITCH-05: the pane, as tall as the graph inline, and docked only as wide as its rig names on two staggered rows need. */
function openOf(state: Model.State) {
  const graph = Model.graphOf(state)

  return {
    id: PANE_ID,
    title: 'rig switch',
    focus: true,
    closeOnEscape: true,
    rows: graph.rows.length + 9,
    columns: Math.max(Model.tiersOf(graph, 2).width + 2, 32),
  } as const
}

/** The open pane's model, and the session it switches: one session per process. */
let pane: PaneModel | null = null
let sessionId = ''

/** rig, run from this plugin's checkout as the skill it replaces ran it. */
function rig($: EngineInterface, args: readonly string[]): Promise<ProcessRunResult> {
  return $.process.run(['uv', 'run', '--quiet', '--script', `${$.plugin.root}/scripts/rig`, ...args], {
    timeoutMs: RIG_TIMEOUT_MS,
  })
}

/** Ends the session once the hook that asked has returned: rig, Claude Code's parent, relaunches it. */
function exitSoon($: EngineInterface): void {
  $.clock.after(0, () => {
    void $.command.run({ command: 'exit' }).catch(() => undefined)
  })
}

function redraw($: EngineInterface): void {
  $.ui.invalidate('ui.render')
}

function actionsOf($: EngineInterface) {
  const update = (picks: Model.Picks | null, focus?: string) => {
    if (!pane) {
      return
    }

    if (picks === null) {
      return
    }

    pane = { ...pane, picks, ...(focus ? { focus } : {}) }
    redraw($)
  }

  return {
    toggleRig: (name: string) => {
      if (pane) {
        update(Model.toggleRig(pane.state, pane.picks, name), KEYS.rigOf(name))
      }
    },
    activate: (pluginId: string) => {
      if (!pane) {
        return
      }

      const plan = Model.planOf(pane.state, pane.picks)

      if (Model.offerFor(plan, pluginId)) {
        pane = { ...pane, dialog: pluginId, focus: KEYS.pluginOf(pluginId) }
        redraw($)

        return
      }

      const picks = Model.togglePlugin(pane.state, pane.picks, pluginId)

      if (picks === null) {
        $.ui.toast(`${pluginId} isn't installed; its ${Model.PIN} loads it.`)
      }

      update(picks, KEYS.pluginOf(pluginId))
    },
    togglePlugin: (pluginId: string) => {
      if (pane) {
        const picks = Model.togglePlugin(pane.state, pane.picks, pluginId)

        pane = { ...pane, dialog: null }
        update(picks)
        redraw($)
      }
    },
    togglePin: (pluginId: string) => {
      if (pane) {
        const picks = Model.togglePin(pane.state, pane.picks, pluginId)

        pane = { ...pane, dialog: null }
        update(picks)
        redraw($)
      }
    },
    closeDialog: () => {
      if (pane) {
        pane = { ...pane, dialog: null }
        redraw($)
      }
    },
    unpin: (pluginId: string) => {
      void unpin($, pluginId)
    },
    switchRigs: () => {
      void record($)
    },
    cancel: () => {
      // A plugin's own $.ui.close skips its own ui.close hook, so the line is said here.
      pane = null
      $.ui.log(CANCELLED_TEXT)
      void $.ui.close({ id: PANE_ID }).catch(() => undefined)
    },
  }
}

/** PIN-05, PIN-13: stop loading the checkout, in this switch and the launches after it. */
async function unpin($: EngineInterface, pluginId: string): Promise<void> {
  if (!pane) {
    return
  }

  const offer = Model.offerFor(Model.planOf(pane.state, pane.picks), pluginId)

  if (!offer) {
    return
  }

  const result = await rig($, ['unpin', offer.pin.path])

  if (result.exitCode !== 0) {
    $.ui.toast(failureOf(result))

    return
  }

  const refreshed = await rig($, ['switch', '--state'])
  const state = refreshed.exitCode === 0 ? parseState(refreshed.stdout) : null

  if (pane) {
    const { [offer.pin.path]: _dropped, ...choices } = pane.picks.choices
    const pins = pane.state.pins.filter(pin => pin.path !== offer.pin.path)
    const here = pane.state.here.filter(path => path !== offer.pin.path)

    pane = {
      ...pane,
      state: state ?? { ...pane.state, pins, here },
      picks: { ...pane.picks, choices },
      dialog: null,
    }
    redraw($)
  }

  $.ui.toast(`unpinned ${offer.pin.plugin} (${offer.pin.display})`)
}

/** SWITCH-01: record the picks for rig, then end the session so rig relaunches it with them. */
async function record($: EngineInterface): Promise<void> {
  if (!pane) {
    return
  }

  const picks = JSON.stringify(Model.recorded(pane.state, pane.picks))
  const result = await rig($, ['switch', '--session', sessionId, '--picks', picks])

  if (result.exitCode !== 0) {
    $.ui.toast(failureOf(result))

    return
  }

  const text = result.stdout.trim()

  pane = null
  await $.ui.close({ id: PANE_ID }).catch(() => undefined)
  $.ui.log(text)

  // Unchanged picks record nothing, so an exit would end the session with no relaunch.
  if (!isUnchanged(text)) {
    exitSoon($)
  }
}

/** What `rig switch` says when the picks are what the session already loads: it records nothing. */
function isUnchanged(text: string): boolean {
  return text.includes('already uses')
}

/**
 * SWITCH-01..05 in the session: `/rig` opens rig's picker in a pane over the
 * session's rigs, plugins and pins; `l` records the choice with `rig switch
 * --picks` and ends the session, and rig relaunches the conversation with it.
 */
export function register(on: On): void {
  pane = null
  sessionId = ''

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: COMMAND,
      description: 'Switch this session to other rigs, keeping the conversation',
      argumentHint: '[rig...]',
    })

    return next(e)
  })

  on('command.run', { command: COMMAND }, async ($, e) => {
    sessionId = await $.session.id()

    const names = e.args.split(/[\s,]+/).filter(name => name !== '')

    if (names.length > 0) {
      const result = await rig($, ['switch', ...names, '--session', sessionId])

      if (result.exitCode !== 0) {
        return { text: failureOf(result) }
      }

      const text = result.stdout.trim()

      if (!isUnchanged(text)) {
        exitSoon($)
      }

      return { text }
    }

    const result = await rig($, ['switch', '--state'])

    if (result.exitCode !== 0) {
      return { text: failureOf(result) }
    }

    const state = parseState(result.stdout)

    if (!state) {
      return { text: `rig switch --state printed something rig's pane can't read:\n${result.stdout.trim()}` }
    }

    if (!state.launched) {
      const rigs = state.current.rigs.join(' ') || Model.BASE

      return {
        text:
          "this session wasn't launched by rig at a terminal, so rig can't relaunch it. " +
          `Exit Claude Code, then run: rig use ${rigs} --resume ${sessionId}`,
      }
    }

    const picks = Model.initialPicks(state)

    pane = { state, picks, dialog: null, focus: null }

    await $.ui.open(openOf(state))

    for (const note of Model.hereNotes(state, picks)) {
      $.ui.toast(note, { timeoutMs: 8000 })
    }

    return {}
  })

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE_ID || !pane || e.surface !== 'terminal') {
      return next(e)
    }

    const { Box, Text, Button } = $.ui.resolve(e)

    return paneView({ ui: { Box, Text, Button }, actions: actionsOf($), columns: e.props.bodyColumns }, pane)
  })

  /** Escape over the pin dialog backs out to the graph; over the graph it cancels the switch. */
  on('ui.close', { id: PANE_ID }, async ($, e, next) => {
    if (pane?.dialog && e.origin.kind === 'person') {
      pane = { ...pane, dialog: null }
      redraw($)
      void $.ui.open(openOf(pane.state)).catch(() => undefined)

      return { deny: 'back to the graph' }
    }

    const result = await next(e)

    if (pane && e.origin.kind !== 'unload') {
      $.ui.log(CANCELLED_TEXT)
    }

    pane = null

    return result
  })

  /** The ring's walk keeps the row it lands on in view, as rig's picker scrolls to its cursor. */
  on('ui.focus', { requestId: PANE_ID }, async ($, e, next) => {
    const result = await next(e)

    if (pane && e.element) {
      pane = { ...pane, focus: e.element }
      void $.ui.scroll({ in: PANE_ID, to: { key: e.element } }).catch(() => undefined)
    }

    return result
  })
}
