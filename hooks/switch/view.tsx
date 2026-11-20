/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { Elements, RenderElement } from 'claude-code'

import * as Model from './model'

/** Dracula, as rig's Textual apps draw it. */
export const COLORS = {
  accent: '#bd93f9',
  add: '#50fa7b',
  note: '#f1fa8c',
  warn: '#ffb86c',
} as const

export const KEYS = {
  rigOf: (name: string) => `rig:${name}`,
  pluginOf: (pluginId: string) => `plugin:${pluginId}`,
  SWITCH: 'switch',
  CANCEL: 'cancel',
  UNPIN: 'pin-unpin',
  TOGGLE: 'pin-toggle',
  LOAD: 'pin-load',
  CLOSE: 'pin-close',
} as const

export type Actions = {
  toggleRig: (name: string) => void
  activate: (pluginId: string) => void
  switchRigs: () => void
  cancel: () => void
  unpin: (pluginId: string) => void
  togglePlugin: (pluginId: string) => void
  togglePin: (pluginId: string) => void
  closeDialog: () => void
}

export type Kit = {
  ui: Pick<Elements['terminal'], 'Box' | 'Text' | 'Button'>
  actions: Actions
}

export type PaneModel = {
  state: Model.State
  picks: Model.Picks
  /** The pinned plugin whose dialog is open (PIN-13), or null. */
  dialog: string | null
  /** The element the ring starts on when the pane takes the keys. */
  focus: string | null
}

const HINT = `↑/↓ or tab move · enter toggles a rig or plugin, opens a ${Model.PIN} · l switches · esc cancels`

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

  const heads = graph.rigs.map((rig, column) => (
    <Box flexDirection="row" key={`head:${rig.name}`}>
      <Text>{'  '}</Text>
      <Button
        key={KEYS.rigOf(rig.name)}
        plain
        dimColor={states[column] === 'off'}
        {...(startKey === KEYS.rigOf(rig.name) ? ({ autoFocus: true } as const) : {})}
        onPress={() => kit.actions.toggleRig(rig.name)}
      >
        {graph.heads[column] ?? rig.name}
      </Button>
    </Box>
  ))

  const marks = graph.rigs.map((rig, column) => {
    const head = graph.heads[column] ?? rig.name
    const width = Model.cells(head)
    const left = Math.floor((width - 1) / 2) + ((width - 1) & width & 1)

    return (
      <Box flexDirection="row" key={`mark:${rig.name}`}>
        <Text>{'  ' + ' '.repeat(left)}</Text>
        {markOf(states[column] ?? 'off')}
        <Text>{' '.repeat(Math.max(width - left - 1, 0))}</Text>
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
      const head = graph.heads[column] ?? rig.name
      const isIn = rig.plugins.includes(pluginId)
      const isOn = isIn && isLoaded && states[column] !== 'off'

      return (
        <Text key={`${pluginId}:${rig.name}`} {...(isOn ? { color: COLORS.add } : { dimColor: true })}>
          {'  ' + Model.center(isIn ? '●' : '·', head.length)}
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
          {Model.pad(graph.labels[index] ?? pluginId, graph.width)}
        </Button>
        {dots}
        {plan.missing.includes(pluginId) ? <Text color={COLORS.warn}>{'  installs at launch'}</Text> : null}
      </Box>
    )
  })

  return (
    <Box flexDirection="column">
      <Text bold>rig switch</Text>
      <Text>{Model.summary(plan)}</Text>
      <Box height={1} />
      <Box flexDirection="row">
        <Text bold>{Model.pad(graph.margin + 'plugin', graph.width)}</Text>
        {heads}
      </Box>
      <Box flexDirection="row">
        <Text>{' '.repeat(graph.width)}</Text>
        {marks}
        {legendText}
      </Box>
      {rows}
      <Box height={1} />
      <Box flexDirection="row" gap={2}>
        <Button key={KEYS.SWITCH} plain hotkey="l" onPress={kit.actions.switchRigs}>
          Switch 🚀
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
