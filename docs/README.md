# rig

Different work calls for different plugins. A **rig** is a named set of plugins
chosen for a kind of work; rig launches Claude Code with the one you name.

While you're developing a plugin, pin its local checkout and it stands in for
the installed copy in every rig that uses the plugin, so your edits take effect
without a marketplace release. When you want
Bash commands confined, turn on the sandbox for a launch, or have a rig ask for
it.

[Using rig](/usage) covers installing it, rigs, pins, and the sandbox. The
[spec](/spec) lists what it does, requirement by requirement.
