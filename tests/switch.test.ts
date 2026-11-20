import { describe, expect, mock, test } from 'claude-code/testing'

import { PANE, SESSION, SESSION_ID, STATE, commandOf, textOf, worldOf } from './fixtures/switch-world'

const press = (key: string) => ({ plugin: 'rig', key })

describe('switch', () => {
  test('SWITCH-01: the start registers /rig', async ($, on) => {
    const world = worldOf(on)

    await $.session.start(SESSION)

    expect(world.commands).toEqual(['rig'])
  })

  test('SWITCH-01: /rig <rig> records the switch with the session id and exits Claude Code', async ($, on) => {
    const world = worldOf(on)
    const clock = mock.clock(on)

    await $.session.start(SESSION)
    const { text } = await $.command.run(commandOf('ops'))
    await clock.advance(10)

    expect(world.runs).toEqual([['switch', 'ops', '--session', SESSION_ID]])
    expect(text).toContain('base + ops')
    expect(world.exits).toBe(1)
    expect(world.opened).toEqual([])
  })

  test('SWITCH-04: a refused switch shows why and keeps the session', async ($, on) => {
    const world = worldOf(on)
    const clock = mock.clock(on)

    world.answer = () => ({ exitCode: 1, stdout: '', stderr: 'rig: no rig named nope. Rigs: base, ops, web, full\n', isStdoutTruncated: false, isStderrTruncated: false })

    await $.session.start(SESSION)
    const { text } = await $.command.run(commandOf('nope'))
    await clock.advance(10)

    expect(text).toContain('no rig named nope')
    expect(world.exits).toBe(0)
  })

  test('SWITCH-03: outside a session rig launched, /rig refuses and names the resume command', async ($, on) => {
    const world = worldOf(on, { ...STATE, launched: false })

    await $.session.start(SESSION)
    const { text } = await $.command.run(commandOf())

    expect(text).toContain(`rig use web --resume ${SESSION_ID}`)
    expect(world.opened).toEqual([])
  })

  test('SWITCH-05: /rig opens the picker on the session, and a toast names the pin holding this folder', async ($, on) => {
    const world = worldOf(on)

    await $.session.start(SESSION)
    await $.command.run(commandOf())

    expect(world.runs).toEqual([['switch', '--state']])
    expect(world.opened).toEqual(['rig-switch'])
    expect(world.toasts).toEqual(['📌 rig holds this folder: its checkout loads'])

    const drawn = textOf(await $.ui.render(PANE))

    expect(drawn).toContain('rig switch')
    expect(drawn).toContain('base + web: 3 plugins')
    expect(drawn).toContain('📌 rig@cp')
    expect(drawn).toContain('★web')
    expect(drawn).toContain('Switch 🚀')
  })

  test('LAUNCH-09: choosing full takes the other rigs away, and a rig takes full away', async ($, on) => {
    worldOf(on)

    await $.session.start(SESSION)
    await $.command.run(commandOf())
    await $.ui.render(PANE)

    await $.ui.press(press('rig:full'))
    expect(textOf(await $.ui.render(PANE))).toContain('all 5 plugins')

    await $.ui.press(press('rig:ops'))
    expect(textOf(await $.ui.render(PANE))).toContain('base + ops: 2 plugins')
  })

  test('LAUNCH-11: toggling a plugin takes it out of the launch, or picks it in', async ($, on) => {
    worldOf(on)

    await $.session.start(SESSION)
    await $.command.run(commandOf())
    await $.ui.render(PANE)

    await $.ui.press(press('plugin:beacon@getty'))
    expect(textOf(await $.ui.render(PANE))).toContain('base + web - beacon@getty: 2 plugins')

    await $.ui.press(press('plugin:tack@cp'))
    expect(textOf(await $.ui.render(PANE))).toContain('base + web + tack@cp - beacon@getty: 3 plugins')
  })

  test('PIN-13: a pinned row opens its pin, whose checkout can be skipped', async ($, on) => {
    worldOf(on)

    await $.session.start(SESSION)
    await $.command.run(commandOf())
    await $.ui.render(PANE)

    await $.ui.press(press('plugin:rig@cp'))

    const dialog = textOf(await $.ui.render(PANE))

    expect(dialog).toContain('~/src/rig')
    expect(dialog).toContain('pinned 3 days ago')
    expect(dialog).toContain('the checkout loads')
    expect(dialog).toContain('Skip checkout')

    await $.ui.press(press('pin-load'))
    await $.ui.render(PANE)
    await $.ui.press(press('plugin:rig@cp'))

    expect(textOf(await $.ui.render(PANE))).toContain('the installed copy loads')
  })

  test('SWITCH-05: l records the picks with rig and exits Claude Code', async ($, on) => {
    const world = worldOf(on)
    const clock = mock.clock(on)

    await $.session.start(SESSION)
    await $.command.run(commandOf())
    await $.ui.render(PANE)
    await $.ui.press(press('rig:ops'))
    await $.ui.press(press('rig:web'))
    await $.ui.press(press('switch'))
    await clock.advance(10)

    const recorded = world.runs.find(args => args.includes('--picks'))

    expect(recorded?.slice(0, 4)).toEqual(['switch', '--session', SESSION_ID, '--picks'])
    expect(JSON.parse(recorded?.[4] ?? '{}')).toEqual({
      rigs: ['ops'],
      added: [],
      removed: [],
      pins: { '/src/rig': true },
    })
    expect(world.closed).toEqual(['rig-switch'])
    expect(world.logs).toEqual(['rig: relaunching this conversation with base + ops.'])
    expect(world.exits).toBe(1)
  })

  test('SWITCH-05: cancel closes the pane, says so, and records nothing', async ($, on) => {
    const world = worldOf(on)
    const clock = mock.clock(on)

    await $.session.start(SESSION)
    await $.command.run(commandOf())
    await $.ui.render(PANE)
    await $.ui.press(press('cancel'))
    await clock.advance(10)

    expect(world.closed).toEqual(['rig-switch'])
    expect(world.logs).toEqual(['rig switch cancelled'])
    expect(world.runs.some(args => args.includes('--picks'))).toBe(false)
    expect(world.exits).toBe(0)
  })
})
