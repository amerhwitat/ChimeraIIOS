# Chimera II OS — Neural Dimensional Status

## Current Aurora status

Aurora initializes the multidimensional neural engine at **1024D** by default.

The top status line now reports both the live N-bit execution profile and neural representation, for example:

`AURORA | CHIMERA II | ISA N8192 RISC NativeWide | NEURAL 1024D HyperDimensional | LIVE / NO REBOOT`

The neural dimensionality is independent of the CPU register width. A Chimera process can therefore use an N-bit execution profile such as N8192 while the learning representation operates at 1024D, 4096D, 16384D, or higher.

## Supported neural dimensionalities

- 128D baseline
- 256D
- 512D
- 1024D (Aurora default)
- 2048D
- 4096D
- 8192D
- 16384D
- 32768D
- 65536D

The native multidimensional engine is bounded at 65536D in this implementation. This is a computational representation width, not a claim that these are additional physical spatial dimensions.

## Architecture

The deep-learning layer now provides:

1. **HyperVector** — dense floating-point vectors with runtime-selected dimensionality.
2. **Binding** — element-wise multiplicative composition for representing relationships.
3. **Bundling** — normalized aggregation of multiple representations.
4. **Cosine similarity** — similarity measurement in the active high-dimensional space.
5. **AdaptiveTensor encoding** — expands compact input features into the active representation width.
6. **Dimensional projection** — maps between supported representation widths.
7. **Runtime dimensional control** — changes the active neural width without rebooting Aurora or restarting the neural services.

This follows the established project architecture in which higher dimensions are treated as computational degrees of freedom. The Library research also distinguishes vector dimensionality from tensor rank and describes high-dimensional embedding spaces as normal computational representations rather than extra spatial axes. fileciteturn704file3

The Library material further identifies hyperdimensional computing as a neural paradigm using vectors commonly around 10,000 dimensions or more, and proposes tensor propagation, neural perception, temporal evolution, and higher-dimensional expansion as components of the Chimera research architecture. fileciteturn704file2

## Runtime controls

From an Aurora/Chimera shell:

`tools/runtime/chimera-neural-dim.py status`

`tools/runtime/chimera-neural-dim.py up`

`tools/runtime/chimera-neural-dim.py down`

`tools/runtime/chimera-neural-dim.py set 16384 HyperDimensional`

The state is stored in:

`~/.config/chimera/neural-dimension.json`

No reboot is required to change this representation setting.

## Relationship to the 128D framework

The implementation does **not** treat 128D as the upper boundary. It treats 128D as a baseline semantic region and allows the learned representation to expand into higher computational dimensionality.

The intended conceptual pipeline is:

`physical / event features → 14D semantic basis → 128D framework → high-dimensional learned representation → emergent N-dimensional tensor state`

This is a software architecture for experimentation. It should not be interpreted as an experimentally established physical theory of dimensions.

## External ML context

Modern embedding systems routinely operate above 128 dimensions; for example, Google's current Gemini Embedding documentation describes configurable embedding sizes from 128 through 3072 dimensions. TensorFlow likewise defines tensor dimensionality by rank/axes and supports arbitrary-rank tensor shapes. citeturn0search0turn0search4

Chimera extends the same computational idea inside its own native engine to the 65536D software ceiling, while retaining explicit separation between vector dimensionality, tensor rank, CPU register width, and physical-space interpretation.
