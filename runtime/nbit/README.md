# Native N-bit runtime ABI v1

- Limbs are little-endian arrays of 64-bit words; bit width is carried by typed IR/object metadata and the caller masks unused top bits.
- Helpers return 0 on success, -1 for invalid arguments, -2 for divide-by-zero.
- Arithmetic is unsigned limb arithmetic. Signed operations are two's-complement wrappers in compiler lowering and must define overflow policy.
- Multiply uses compiler 128-bit support where available and 32-bit partial products otherwise.
- Division is restoring long division; simple and portable, not constant-time. Do not use for secret-dependent cryptographic arithmetic.
- F32/F64 helpers operate on bit-cast IEEE binary32/binary64 values using host C floating operations. They are not a software IEEE implementation and require a target/runtime with matching IEEE behavior and compiler flags that do not enable unsafe fast-math.
- These helpers are a runtime ABI foundation. Existing target backends must still emit calls and preserve ABI/calling convention before wide arithmetic works in compiled programs.
