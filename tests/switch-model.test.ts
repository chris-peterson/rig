import { describe, expect, test } from 'claude-code/testing'

import * as Model from '../hooks/switch/model'
import { STATE } from './fixtures/switch-world'

const start = Model.initialPicks(STATE)

describe('switch-model', () => {
  test('the picks start on the session: its rigs, and the checkout it loads', () => {
    expect(start).toEqual({ rigs: ['web'], added: [], removed: [], choices: { '/src/rig': true } })
  })

  test('RIG-02: base, then each rig, without repeats; full is every installed plugin', () => {
    expect([...Model.planOf(STATE, start).sources]).toEqual([
      ['anchor@getty', 'base'],
      ['rig@cp', 'web'],
      ['beacon@getty', 'web'],
    ])
    expect(Model.summary(Model.planOf(STATE, { ...start, rigs: ['full'] }))).toBe('all 5 plugins')
    expect(Model.summary(Model.planOf(STATE, { ...start, rigs: ['full'], removed: ['tack@cp'] }))).toBe(
      'all but tack@cp: 4 plugins',
    )
  })

  test('LAUNCH-09: full goes alone', () => {
    const full = Model.toggleRig(STATE, start, 'full')

    expect(full.rigs).toEqual(['full'])
    expect(Model.toggleRig(STATE, full, 'ops').rigs).toEqual(['ops'])
  })

  test('base never goes', () => {
    expect(Model.toggleRig(STATE, start, 'base')).toBe(start)
  })

  test('LAUNCH-11: a rig with a plugin taken out is partly loaded, and toggling it brings it back whole', () => {
    const out = Model.togglePlugin(STATE, start, 'beacon@getty')

    expect(out?.removed).toEqual(['beacon@getty'])

    const web = STATE.rigs.find(rig => rig.name === 'web')

    expect(web && Model.rigState(web, Model.planOf(STATE, out ?? start))).toBe('partial')
    expect(Model.toggleRig(STATE, out ?? start, 'web').removed).toEqual([])
  })

  test('LAUNCH-11: a plugin no chosen rig holds is picked, marking its rig partly loaded', () => {
    const picked = Model.togglePlugin(STATE, start, 'splunk@getty') ?? start
    const ops = STATE.rigs.find(rig => rig.name === 'ops')

    expect(Model.label(picked.rigs, picked.added, picked.removed)).toBe('base + web + splunk@getty')
    expect(ops && Model.rigState(ops, Model.planOf(STATE, picked))).toBe('partial')
  })

  test('PIN-08: a pin its rigs include and that does not hold the folder is locked in', () => {
    const elsewhere = { ...STATE, here: [] }
    const offer = Model.offerFor(Model.planOf(elsewhere, start), 'rig@cp')

    expect(offer && Model.isLocked(offer)).toBe(true)
    expect(Model.togglePin(elsewhere, start, 'rig@cp')).toBeNull()
  })

  test('PIN-07, PIN-13: a pin holding the folder loads until skipped', () => {
    const skipped = Model.togglePin(STATE, start, 'rig@cp') ?? start
    const plan = Model.planOf(STATE, skipped)

    expect(Model.pinStateOf(plan, 'rig@cp', skipped.choices)).toBe('the installed copy loads')
    expect(Model.recorded(STATE, skipped).pins).toEqual({ '/src/rig': false })
    expect(Model.hereNotes(STATE, skipped)).toEqual(['📌 rig holds this folder: the installed copy loads'])
  })

  test('RIG-14, PIN-12: the graph lists rigs’ plugins, then the rest installed, a 📌 after pinned ones', () => {
    const graph = Model.graphOf(STATE)

    expect(graph.rows).toEqual(['anchor@getty', 'splunk@getty', 'rig@cp', 'beacon@getty', 'tack@cp'])
    expect(graph.labels[2]).toBe('rig@cp 📌')
    expect(graph.heads).toEqual(['base', 'ops', '★web', 'full'])
    expect(graph.width).toBe(Model.cells('splunk@getty'))
  })

  test('marks centre as Python’s str.center does', () => {
    expect(Model.center('●', 4)).toBe(' ●  ')
    expect(Model.center('●', 5)).toBe('  ●  ')
    expect(Model.center('●', 2)).toBe('● ')
    expect(Model.cells('rig 📌')).toBe(6)
  })
})
