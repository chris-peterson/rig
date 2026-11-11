# shipyard runs from its git ref, with no checkout and no install. CI is the
# writer for what lands; these recipes are for seeing the projection first.
shipyard := "uvx --from 'git+https://github.com/chris-peterson/shipyard@v2' shipyard"

# what this is, and every recipe there is
[private]
default:
    @echo ""
    @echo "  rig: launch Claude Code with a named set of plugins"
    @echo ""
    @echo "  New here?   just demo         see what each launch hands Claude Code"
    @echo "  Try it?     just run list     run rig from this checkout"
    @echo "  Live on it? just trial-on     put this checkout's rig on your PATH"
    @echo ""
    @just --list --unsorted --list-heading '' --list-prefix '    '
    @echo ""
    @echo "  Generated files are written by CI on PRs and main; edit the source, not the output."
    @echo ""

# run rig against a throwaway HOME and a stand-in claude, showing what each launch passes
[group('start here')]
demo:
    @uv run --quiet --with pyyaml python dev/demo.py

# run rig from this checkout against your real setup: just run list
[group('start here')]
[positional-arguments]
run *args:
    @uv run --quiet --script scripts/rig "$@"

# point the `rig` on your PATH at this working copy, until `just trial-off`
[group('start here')]
trial-on:
    @uv run --quiet --script scripts/rig install-cli
    @echo
    @echo "Trialling $(uv run --quiet --script scripts/rig --version) from $(pwd)."
    @echo "Edits are live, with no reinstall; \`just trial-off\` to revert."

# put the installed plugin build back on your PATH
[group('start here')]
trial-off:
    @bash scripts/trial-off.sh

# preview the docsify docs site locally
[group('start here')]
docs:
    {{shipyard}} build-docs
    docsify serve docs --open

# run the test suite, including the completion parity check
[group('check your work')]
test:
    uv run --quiet --with pyyaml --with textual python -m unittest discover -s tests

# run claude plugin validate with plugin.yml's acceptances, as the projection job does
[group('check your work')]
check:
    {{shipyard}} validate

# project source into the generated artifacts (plugin.json, describe, docs)
[group('generated files')]
generate:
    {{shipyard}} generate

# regenerate the artifacts and list what the projection job would commit
[group('generated files')]
check-generated:
    {{shipyard}} generate
    git --no-pager diff --stat
