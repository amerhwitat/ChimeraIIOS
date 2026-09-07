# Chimera II OS Demo Sites

The following live demonstrations are part of the Chimera II OS project and should be treated as external demo deployments, not as authoritative source trees.

## CodeWords / shared HTML demo

https://codewords.agemo.ai/share/html/22980add8f8df4e6c834a970234105a26c98916f152ccff79720c778407fb2ba

## OnHercules live demo

https://chimera-ii-os-730893.onhercules.app/

## Source synchronization status

The repository links above are authoritative pointers to the live demonstrations. During this repository update, the available web fetch environment could not retrieve either deployment, so their complete generated HTML/CSS/JavaScript/source contents have **not** been copied into this repository and are not represented as inspected source.

To incorporate all code and information from these demos faithfully, export/download the source of each demo (or provide an archive containing the generated site files) and add it under:

- `demos/codewords/`
- `demos/onhercules/`

The exported material should retain its original attribution and third-party licenses. Generated/minified bundles may be preserved in `demos/`, while reusable source should be copied into the appropriate `desktop/`, `web/`, `simulation/`, or `tools/` subsystem after review.

## Integration policy

1. Preserve the original demo as a reproducible snapshot.
2. Identify dependencies and licenses before merging third-party code.
3. Separate generated frontend assets from maintainable source.
4. Add build/run instructions for each demo.
5. Cross-link the demo documentation from the root README.
