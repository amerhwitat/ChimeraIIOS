# Chimera II ISA Encoding Data Dictionary

## Record format

The expanded machine-readable artifact uses semicolon-delimited CSV because several operand and note fields may contain commas.

```text
mnemonic;opcode;encoding;operands;privilege;latency;throughput;pipeline_stage;isa_family;notes;source_ref;encoding_template;opcode_bits;imm_size;modrm_like;example_binary
```

## Normalization rules

- UTF-8 encoding.
- One instruction per physical CSV record.
- Semicolon field delimiter.
- No embedded line breaks inside a field.
- Hexadecimal opcode values are accepted with `0x` prefix.
- `opcode_bits` must identify the same opcode as `opcode` unless a documented prefix scheme is introduced.
- `imm_size=0` means no immediate field.
- `modrm_like` is `yes` or `no`.
- `source_ref=internal` identifies project-supplied metadata rather than an external standards claim.

## Example normalized records

```text
ADD;0x0001;R;rd,rs,rt;user;1;1;ALU;R8192;Lane-wise wide add;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x01;0;no;0x01010203
SUB;0x0002;R;rd,rs,rt;user;1;1;ALU;R8192;Lane-wise wide subtract;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x02;0;no;0x02010203
AND;0x0003;R;rd,rs,rt;user;1;1;ALU;R8192;Lane-wise bitwise and;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x03;0;no;0x03010203
OR;0x0004;R;rd,rs,rt;user;1;1;ALU;R8192;Lane-wise bitwise or;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x04;0;no;0x04010203
XOR;0x0005;R;rd,rs,rt;user;1;1;ALU;R8192;Lane-wise bitwise xor;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x05;0;no;0x05010203
NOT;0x0006;R;rd,rs;user;1;1;ALU;R8192;Lane-wise bitwise not;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 reserved];0x06;0;no;0x06010200
SHL;0x0007;R;rd,rs,imm;user;2;1;ALU;R8192;Logical left shift lanes;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 imm8];0x07;8;no;0x07010204
SHR;0x0008;R;rd,rs,imm;user;2;1;ALU;R8192;Logical right shift lanes;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 imm8];0x08;8;no;0x08010204
ROL;0x0009;R;rd,rs,imm;user;3;0.8;ALU;R8192;Rotate left lanes;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 imm8];0x09;8;no;0x09010204
ROR;0x000A;R;rd,rs,imm;user;3;0.8;ALU;R8192;Rotate right lanes;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 imm8];0x0A;8;no;0x0A010204
MUL;0x000B;R;rd,rs,rt;user;4;0.5;MUL;R8192;Schoolbook low bits multiply;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x0B;0;no;0x0B010203
MULHI;0x000C;R;rd,rs,rt;user;6;0.3;MUL;R8192;High bits multiply;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x0C;0;no;0x0C010203
MULMOD;0x000D;R;rd,rs,rt,mod;priv;120;0.05;CRYPTO;R8192;Modular multiply;internal;[47:40 opcode][39:32 rd][31:24 rs][23:16 rt][15:0 mod16];0x0D;16;no;0x0D01020300FF
MODEXP;0x000E;M;rd,rs,imm;priv;200;0.02;CRYPTO;R8192;Modular exponentiation;internal;[63:56 opcode][55:48 rd][47:40 rs][39:0 imm40];0x0E;40;no;0x0E0102030000000A
BARRETT;0x000F;R;rd,rs,mod;priv;80;0.1;CRYPTO;R8192;Barrett reduction helper;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 mod8];0x0F;8;no;0x0F010203
DIV;0x0010;R;rd,rs,rt;user;20;0.05;ALU;R8192;Wide divide low;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x10;0;no;0x10010203
REM;0x0011;R;rd,rs,rt;user;20;0.05;ALU;R8192;Wide remainder;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x11;0;no;0x11010203
CMP;0x0012;R;rd,rs,rt;user;1;1;ALU;R8192;Lane-wise compare;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x12;0;no;0x12010203
CMPEQ;0x0013;R;rd,rs,rt;user;1;1;ALU;R8192;Lane-wise equal;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x13;0;no;0x13010203
CMPLT;0x0014;R;rd,rs,rt;user;1;1;ALU;R8192;Lane-wise less-than;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 rt];0x14;0;no;0x14010203
MOV;0x0015;R;rd,rs;user;1;2;ALU;R8192;Register move;internal;[31:24 opcode][23:16 rd][15:8 rs][7:0 reserved];0x15;0;no;0x15010200
```

## Completeness statement

The project discussion supplied additional rows beyond this excerpt but terminated during the `RSAMOD` record. This dictionary therefore does not fabricate absent records. The existing repository's complete semantic opcode catalog remains the authoritative 284-instruction identity set until the full expanded source is imported.
