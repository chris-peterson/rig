/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { Elements, RenderElement } from 'claude-code'

import * as Model from './model'

/** Dracula, as rig's Textual apps draw it. */
export const COLORS = {
  accent: '#bd93f9',
  add: '#50fa7b',
  remove: '#ff5555',
  note: '#f1fa8c',
  warn: '#ffb86c',
} as const

export const KEYS = {
  rigOf: (name: string) => `rig:${name}`,
  pluginOf: (pluginId: string) => `plugin:${pluginId}`,
  SWITCH: 'switch',
  CANCEL: 'cancel',
  LEFT: 'nav-left',
  DOWN: 'nav-down',
  UP: 'nav-up',
  RIGHT: 'nav-right',
  UNPIN: 'pin-unpin',
  TOGGLE: 'pin-toggle',
  LOAD: 'pin-load',
  CLOSE: 'pin-close',
} as const

export type Actions = {
  toggleRig: (name: string) => void
  activate: (pluginId: string) => void
  /** hjkl: the cursor down the plugin rows, up from the first into the rig names, and across the rigs. */
  move: (direction: Direction) => Promise<void>
  switchRigs: () => void
  cancel: () => void
  unpin: (pluginId: string) => void
  togglePlugin: (pluginId: string) => void
  togglePin: (pluginId: string) => void
  closeDialog: () => void
}

export type Direction = 'left' | 'down' | 'up' | 'right'

export type Kit = {
  ui: Pick<Elements['terminal'], 'Box' | 'Text' | 'Button'>
  actions: Actions
  /** The cells across the pane's body: the rig names go down their columns when across doesn't fit. */
  columns: number
}

export type PaneModel = {
  state: Model.State
  picks: Model.Picks
  /** The pinned plugin whose dialog is open (PIN-13), or null. */
  dialog: string | null
  /** The element the ring starts on when the pane takes the keys. */
  focus: string | null
}

const HINT = `arrows hjkl tab move · enter toggles, opens a ${Model.PIN} · g goes · esc cancels`

/** The pane's body: the graph `rig --select` draws, or one pin's dialog over it. */
export function paneView(kit: Kit, model: PaneModel): RenderElement {
  return model.dialog === null ? graphView(kit, model) : pinView(kit, model, model.dialog)
}

function graphView(kit: Kit, model: PaneModel): RenderElement {
  const { Box, Text, Button } = kit.ui
  const { state, picks } = model
  const plan = Model.planOf(state, picks)
  const graph = Model.graphOf(state)
  const states = graph.rigs.map(rig => Model.rigState(rig, plan))
  const legend = Model.legendOf(graph, states)
  const startKey = model.focus ?? KEYS.rigOf(graph.rigs[1]?.name ?? Model.BASE)
  const tiered = Model.stagger(graph, kit.columns)
  const changes = Model.changesOf(state, picks)

  /** A name in green when the switch brings it in, red when it takes it out, else as it was. */
  const named = (text: string, change: Model.Change) =>
    change === null ? text : <Text color={change === 'added' ? COLORS.add : COLORS.remove}>{text}</Text>

  const markOf = (state: Model.RigState) =>
    state === 'on' ? (
      <Text bold color={COLORS.accent}>
        ✓
      </Text>
    ) : state === 'partial' ? (
      <Text bold color={COLORS.note}>
        ◐
      </Text>
    ) : (
      <Text> </Text>
    )

  const headOf = (rig: Model.Rig, column: number) => (
    <Button
      key={KEYS.rigOf(rig.name)}
      plain
      dimColor={states[column] === 'off'}
      {...(startKey === KEYS.rigOf(rig.name) ? ({ autoFocus: true } as const) : {})}
      onPress={() => kit.actions.toggleRig(rig.name)}
    >
      {named(graph.heads[column] ?? rig.name, changes.rigs[column] ?? null)}
    </Button>
  )

  const plugin = <Text bold>{Model.pad(graph.margin + 'plugin', graph.width)}</Text>

  /** One row of rig names across, or rows of them staggered, each name starting over its mark. */
  const headRows = tiered
    ? Array.from({ length: tiered.tiers }, (_, tier) => {
        let cursor = 0
        const parts: RenderElement[] = []

        graph.rigs.forEach((rig, column) => {
          if (column % tiered.tiers !== tier) {
            return
          }

          const at = column * tiered.pitch + 1

          parts.push(<Text key={`gap:${rig.name}`}>{' '.repeat(at - cursor)}</Text>, headOf(rig, column))
          cursor = at + Model.cells(graph.heads[column] ?? rig.name)
        })

        return (
          <Box flexDirection="row" key={`tier:${tier}`}>
            {tier === tiered.tiers - 1 ? plugin : <Text>{' '.repeat(graph.width)}</Text>}
            {parts}
          </Box>
        )
      })
    : [
        <Box flexDirection="row" key="tier:0">
          {plugin}
          {graph.rigs.map((rig, column) => (
            <Box flexDirection="row" key={`head:${rig.name}`}>
              <Text>{'  '}</Text>
              {headOf(rig, column)}
            </Box>
          ))}
        </Box>,
      ]

  /** Where a column's mark sits: centred under its name across, or a cell in when staggered. */
  const spotOf = (column: number): { left: number; right: number } => {
    if (tiered) {
      return { left: 1, right: tiered.pitch - 2 }
    }

    const width = Model.cells(graph.heads[column] ?? '')
    const left = Math.floor((width - 1) / 2) + ((width - 1) & width & 1)

    return { left: 2 + left, right: Math.max(width - left - 1, 0) }
  }

  const marks = graph.rigs.map((rig, column) => {
    const { left, right } = spotOf(column)

    return (
      <Box flexDirection="row" key={`mark:${rig.name}`}>
        <Text>{' '.repeat(left)}</Text>
        {markOf(states[column] ?? 'off')}
        <Text>{' '.repeat(right)}</Text>
      </Box>
    )
  })

  const legendText = legend.map(({ mark, meaning }, index) => (
    <Box flexDirection="row" key={`legend:${mark}`}>
      <Text>{index === 0 ? '    ' : '  '}</Text>
      <Text bold color={mark === '★' ? undefined : mark === '✓' ? COLORS.accent : COLORS.note}>
        {mark}
      </Text>
      <Text dimColor>{` = ${meaning}`}</Text>
    </Box>
  ))

  const rows = graph.rows.map((pluginId, index) => {
    const isLoaded = Model.rowLoads(plan, pluginId)
    const key = KEYS.pluginOf(pluginId)

    const dots = graph.rigs.map((rig, column) => {
      const { left, right } = spotOf(column)
      const isIn = rig.plugins.includes(pluginId)
      const isOn = isIn && isLoaded && states[column] !== 'off'

      return (
        <Text key={`${pluginId}:${rig.name}`} {...(isOn ? { color: COLORS.add } : { dimColor: true })}>
          {' '.repeat(left) + (isIn ? '●' : '·') + ' '.repeat(right)}
        </Text>
      )
    })

    return (
      <Box flexDirection="row" key={`row:${pluginId}`}>
        <Button
          key={key}
          plain
          dimColor={!isLoaded}
          {...(startKey === key ? ({ autoFocus: true } as const) : {})}
          onPress={() => kit.actions.activate(pluginId)}
        >
          {named(Model.pad(graph.labels[index] ?? pluginId, graph.width), changes.rows[index] ?? null)}
        </Button>
        {dots}
        {plan.missing.includes(pluginId) ? (
          <Text color={COLORS.warn} wrap="truncate-end">
            {'  installs at launch'}
          </Text>
        ) : null}
      </Box>
    )
  })

  return (
    <Box flexDirection="column">
      <Text bold>rig switch</Text>
      <Text>{Model.summary(plan)}</Text>
      {changeLine(kit, graph, changes.rows)}
      <Box height={1} />
      {headRows}
      <Box flexDirection="row">
        <Text>{' '.repeat(graph.width)}</Text>
        {marks}
        {tiered ? null : legendText}
      </Box>
      {rows}
      {tiered && legendText.length > 0 ? <Box flexDirection="row">{legendText}</Box> : null}
      <Box height={1} />
      <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
        <Button key={KEYS.LEFT} plain hotkey="h" onPress={() => kit.actions.move('left')}>
          ←
        </Button>
        <Button key={KEYS.DOWN} plain hotkey="j" onPress={() => kit.actions.move('down')}>
          ↓
        </Button>
        <Button key={KEYS.UP} plain hotkey="k" onPress={() => kit.actions.move('up')}>
          ↑
        </Button>
        <Button key={KEYS.RIGHT} plain hotkey="l" onPress={() => kit.actions.move('right')}>
          →
        </Button>
        <Button key={KEYS.SWITCH} plain hotkey="g" onPress={kit.actions.switchRigs}>
          Go 🚀
        </Button>
        <Button key={KEYS.CANCEL} plain hotkey="q" onPress={kit.actions.cancel}>
          Cancel
        </Button>
      </Box>
      <Text dimColor wrap="truncate-end">
        {HINT}
      </Text>
    </Box>
  )
}

/** SWITCH-05: the plugins the switch brings in, in green, and takes out, in red; nothing while it changes none. */
function changeLine(kit: Kit, graph: Model.Graph, rows: readonly Model.Change[]): RenderElement | null {
  const { Box, Text } = kit.ui
  const namesOf = (change: Model.Change) =>
    graph.rows.flatMap((pluginId, index) => (rows[index] === change ? [(graph.labels[index] ?? pluginId).trim()] : []))
  const added = namesOf('added')
  const removed = namesOf('removed')

  if (added.length === 0 && removed.length === 0) {
    return null
  }

  return (
    <Box flexDirection="column">
      {added.length > 0 ? (
        <Text color={COLORS.add} wrap="truncate-end">
          {`+ ${added.join(', ')}`}
        </Text>
      ) : null}
      {removed.length > 0 ? (
        <Text color={COLORS.remove} wrap="truncate-end">
          {`- ${removed.join(', ')}`}
        </Text>
      ) : null}
    </Box>
  )
}

/** PIN-13: one pin's checkout, age, and whether it loads; Unpin first, then the plugin, then the checkout. */
function pinView(kit: Kit, model: PaneModel, pluginId: string): RenderElement {
  const { Box, Text, Button } = kit.ui
  const plan = Model.planOf(model.state, model.picks)
  const offer = Model.offerFor(plan, pluginId)

  if (!offer) {
    return <Text dimColor>{`${pluginId} has no ${Model.PIN}`}</Text>
  }

  const isLoaded = plan.sources.has(pluginId)
  const isCheckout = Model.loads(offer, model.picks.choices)

  return (
    <Box flexDirection="column">
      <Text bold>{`${Model.PIN} ${offer.pin.plugin}`}</Text>
      <Box height={1} />
      <Text color={COLORS.note}>{offer.pin.display}</Text>
      <Text dimColor>{`pinned ${offer.pin.age}`}</Text>
      <Text>{Model.pinStateOf(plan, pluginId, model.picks.choices)}</Text>
      <Box height={1} />
      <Box flexDirection="row" gap={2}>
        <Button key={KEYS.UNPIN} autoFocus onPress={() => kit.actions.unpin(pluginId)}>
          Unpin
        </Button>
        {pluginId.includes('@') ? (
          <Button key={KEYS.TOGGLE} onPress={() => kit.actions.togglePlugin(pluginId)}>
            {isLoaded ? 'Leave out' : 'Load'}
          </Button>
        ) : null}
        {Model.isLocked(offer) ? null : (
          <Button key={KEYS.LOAD} onPress={() => kit.actions.togglePin(pluginId)}>
            {isCheckout ? 'Skip checkout' : 'Load checkout'}
          </Button>
        )}
        <Button key={KEYS.CLOSE} onPress={kit.actions.closeDialog}>
          ✕ Close
        </Button>
      </Box>
      <Box height={1} />
      <Text dimColor>esc closes</Text>
    </Box>
  )
}
