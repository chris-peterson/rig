# shipyard runs from its git ref, with no checkout and no install. CI is the
# writer for what lands; these recipes are for seeing the projection first.
shipyard := "uvx --from 'git+https://github.com/chris-peterson/shipyard@v2' shipyard"

# what this is, and every recipe there is
[private]
default:
    @echo ""
    @echo "  rig: launch Claude Code with a named set of plugins"
    @echo ""
    @just --list --unsorted --list-heading '' --list-prefix '    '
    @echo ""
    @echo "  Generated files are written by CI on PRs and main; edit the source, not the output."
    @echo ""

# run rig against a throwaway HOME and a stand-in claude, showing what each launch passes
[group('start here')]
demo:
    @uv run --quiet --with pyyaml python dev/demo.py

# preview the docsify docs site locally
[group('start here')]
docs:
    {{shipyard}} build-docs
    docsify serve docs --open

# run the test suite, including the completion parity check
[group('check your work')]
test:
    uv run --quiet --with pyyaml python -m unittest discover -s tests

# project source into the generated artifacts (plugin.json, describe, docs)
[group('generated files')]
generate:
    {{shipyard}} generate

# regenerate the artifacts and list what the projection job would commit
[group('generated files')]
check-generated:
    {{shipyard}} generate
    git --no-pager diff --stat

# run claude plugin validate with plugin.yml's acceptances, as the projection job does
[group('generated files')]
validate:
    {{shipyard}} validate
