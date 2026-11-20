import type { CommandRunInput, On, RenderInput, SessionStartInput } from 'claude-code'

import type { State } from '../../hooks/switch/model'

export const SESSION_ID = 'sess-1'

/** A session rig launched at a terminal with web, in a folder the rig plugin's pin holds. */
export const STATE: State = {
  launched: true,
  rigs: [
    { name: 'base', built_in: true, default: false, plugins: ['anchor@getty'] },
    { name: 'ops', built_in: false, default: false, plugins: ['splunk@getty'] },
    { name: 'web', built_in: false, default: true, plugins: ['rig@cp', 'beacon@getty'] },
    { name: 'full', built_in: true, default: false, plugins: ['anchor@getty', 'beacon@getty', 'rig@cp', 'splunk@getty', 'tack@cp'] },
  ],
  installed: ['anchor@getty', 'beacon@getty', 'rig@cp', 'splunk@getty', 'tack@cp'],
  pins: [{ plugin: 'rig', path: '/src/rig', display: '~/src/rig', age: '3 days ago' }],
  here: ['/src/rig'],
  current: { rigs: ['web'], added: [], removed: [], pins: { '/src/rig': true } },
}

export const SESSION: SessionStartInput = { surface: 'terminal', isInteractive: true, cwd: '/src/rig' }

export const commandOf = (args = ''): CommandRunInput => ({
  command: 'rig',
  args,
  origin: { kind: 'composer' },
  presentation: { isFullscreen: false, columns: 160 },
})

export const PANE: RenderInput<'Pane'> = {
  component: 'Pane',
  surface: 'terminal',
  requestId: 'rig-switch',
  viewport: { columns: 160, rows: 40 },
  props: {
    title: 'rig switch',
    isFocused: true,
    bodyColumns: 156,
    placement: 'inline',
    scroll: { offset: 0, bodyRows: 30 },
    view: {},
  },
}

type Reply = { exitCode: number; stdout: string; stderr: string; isStdoutTruncated: boolean; isStderrTruncated: boolean }

export type World = {
  runs: string[][]
  opened: string[]
  closed: string[]
  toasts: string[]
  logs: string[]
  commands: string[]
  exits: number
  /** What rig answers, by its arguments past the script path. */
  answer: (args: readonly string[]) => Reply
}

const ok = (stdout: string): Reply => ({ exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false })

/** The engine and rig beneath the mod, in memory. */
export function worldOf(on: On, state: State = STATE): World {
  const world: World = {
    runs: [],
    opened: [],
    closed: [],
    toasts: [],
    logs: [],
    commands: [],
    exits: 0,
    answer: args => {
      if (args[0] === 'switch' && args[1] === '--state') {
        return ok(JSON.stringify(state))
      }

      if (args[0] === 'switch' && args.includes('--picks')) {
        return ok('rig: relaunching this conversation with base + ops.\n')
      }

      if (args[0] === 'switch') {
        return ok(`rig: relaunching this conversation with base + ${args[1]}.\n`)
      }

      return ok('')
    },
  }

  on('process.run', ($, e) => {
    const script = e.argv.findIndex(arg => arg.endsWith('/scripts/rig'))
    const args = e.argv.slice(script + 1)

    world.runs.push([...args])

    return { value: world.answer(args) }
  })

  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('session.id', () => ({ value: SESSION_ID }))
  on('command.register', ($, e) => {
    world.commands.push(e.name)

    return { value: { command: e.name } }
  })

  on('command.run', { command: 'exit' }, () => {
    world.exits += 1

    return { text: '' }
  })

  on('ui.open', ($, e) => {
    world.opened.push(e.id)

    return { value: { isPlaced: true as const } }
  })

  on('ui.close', ($, e) => {
    world.closed.push(e.id)

    return { value: undefined }
  })

  on('ui.toast', ($, e) => {
    world.toasts.push(e.text)

    return { value: undefined }
  })

  on('ui.log', ($, e) => {
    world.logs.push(e.text)

    return { value: undefined }
  })

  on('ui.invalidate', () => ({ value: undefined }))
  on('ui.scroll', () => ({ value: {} }) as never)

  return world
}

/** The text a drawn tree shows, Button labels included. */
export function textOf(tree: unknown): string {
  if (typeof tree === 'string' || typeof tree === 'number') {
    return String(tree)
  }

  if (Array.isArray(tree)) {
    return tree.map(textOf).join('')
  }

  if (typeof tree !== 'object' || !tree) {
    return ''
  }

  const props: unknown = Reflect.get(tree, 'props')
  const labelOf = (prop: string) => {
    const value: unknown = typeof props === 'object' && props ? Reflect.get(props, prop) : undefined

    return typeof value === 'string' ? value : ''
  }

  const children = Reflect.get(tree, 'children') ?? (typeof props === 'object' && props ? Reflect.get(props, 'children') : [])

  return `${labelOf('label')}${textOf(children ?? [])}`
}
