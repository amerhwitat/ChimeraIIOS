# Neurovisual adaptive desktop layer

This shared userland component turns a normalized 14-axis state vector into
bounded visual tokens for Aurora Glass and Marine Blue. A recurrent exponential
smoother avoids abrupt changes; the browser adapter maps those tokens to CSS
custom properties. The C++ header exposes the same state/projection for a native
desktop shell or compositor to consume.

## 14-axis contract

1–3 position (x/y/z); 4 time; 5 perspective; 6 energy/light; 7 interaction;
8 visual identity; 9 material response; 10 information density; 11
stochasticity/noise; 12 agency/motion; 13 semantic palette; 14 integration
coherence.

D14 is a computational consistency feature, **not a consciousness measurement**.
D11 is a bounded visual-noise control, **not a quantum probability model**.
The component does not implement an LLM, CNN, autograd tensor engine, LQG spin
network, or physical theory. Those require separately trained, versioned models
and validated scientific implementations. A future inference adapter may send
normalized outputs through the `chimera-neurovisual-input` browser event or
the C++ `State14` API. Inputs are clamped to [0,1].

## Browser integration

Load `neurovisual.js` after the page's desktop styles. It exports
`window.ChimeraNeurovisual` with `update`, `setIdentity`, `getState`,
and `reset`. Send inference output with:

```js
window.dispatchEvent(new CustomEvent("chimera-neurovisual-input", {
  detail: { identity: "aurora", state: { energy: 0.7, material: 0.8, agency: 0.25 } }
}));
```

Respect `prefers-reduced-motion`; the adapter does so by default. No remote
service, account data, or model weights are downloaded.
