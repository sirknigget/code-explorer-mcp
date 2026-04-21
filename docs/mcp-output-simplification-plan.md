# MCP output simplification plan

## Goal

Reduce token-heavy boilerplate in MCP tool responses so an LLM exploring a codebase sees only the information that helps it choose the next step.

This plan is intentionally about response design first, not implementation details.

## Guiding principle

For an exploration-oriented MCP server, the response should optimize for:

1. fast scanning
2. low token cost
3. easy follow-up decisions
4. deterministic structure

The response should not spend tokens repeating:

- request arguments the caller already knows
- field names that add little semantic value
- empty sections
- metadata that can be inferred from the request or file extension
- nested descriptive wrappers when the real payload is just a list of names

---

## Tool-by-tool recommendations

### 1. `get_project_structure`

### What an LLM actually needs

When exploring a repo, the model mainly needs:

- the relevant file tree slice
- enough signal to know which languages/parsers are present
- enough signal to know which follow-up tools are worth calling

### What feels redundant today

Current response includes:

- `root`
- `subfolder`
- `pattern`
- `structure`
- `languages_present`
- `available_symbol_types_by_language`

The least useful pieces are:

- `root`: always `"."`; pure boilerplate
- `subfolder`: already supplied as input
- `pattern`: already supplied as input
- `languages_present`: redundant if language capability data is already present
- tree output that still includes parent folders already implied by the requested subfolder

### Recommended output direction

Make this tool return only:

- the rendered tree slice
- compact parser capability summary

Preferred shape:

```json
{
  "structure": "module.py\nsubdir/\n  helper.ts",
  "languages": {
    "python": ["imports", "globals", "classes", "functions"],
    "typescript": ["imports", "globals", "classes", "functions", "interfaces", "type_aliases", "enums", "re_exports"]
  }
}
```

### Recommended reductions

- drop `root`
- drop echoed `subfolder`
- drop echoed `pattern`
- merge `languages_present` into `languages`
- when `subfolder` is provided, render the tree relative to that subfolder instead of repeating its ancestors

Example:

If the request is `subfolder="src/pkg"`, prefer:

```json
{
  "structure": "component.ts\nmodule.py\nview.tsx",
  "languages": {
    "python": ["imports", "globals", "classes", "functions"],
    "typescript": ["imports", "globals", "classes", "functions", "interfaces", "type_aliases", "enums", "re_exports"]
  }
}
```

instead of reprinting:

```text
src/
  pkg/
    component.ts
    module.py
    view.tsx
```

### Why this helps the LLM

- less prompt budget wasted restating the query context
- easier to scan the actual candidate files
- capabilities remain available for planning the next parse step
- fewer repeated top-level fields across repeated calls

---

### 2. `parse_file`

### What an LLM actually needs

For exploration, the model usually needs:

- what kinds of symbols exist in the file
- the symbol names
- only occasional minimal type/context hints when names alone are ambiguous

The model usually does **not** need rich per-symbol structs for discovery.

### What feels redundant today

Current response includes:

- `filename`
- `language`
- `available_symbol_types`
- `sections`

The biggest token sink is `sections`, because it repeats wrappers like:

- `{ "name": "..." }`
- `members`
- `methods`
- `inner_classes`
- `accessors`
- `syntax`
- `declaration_kind`
- import/re-export object shapes

This is descriptive, but for discovery it is mostly ceremony.

### Recommended output direction

Make `sections` primarily a mapping from section name to arrays of strings.

Preferred baseline shape:

```json
{
  "sections": {
    "imports": ["os", "typing.Any as TypingAny", ".helpers.helper as local_helper"],
    "globals": ["MY_GLOBAL", "OTHER_GLOBAL"],
    "classes": ["MyClass", "MyClass.InnerClass"],
    "functions": ["top_level_function"]
  }
}
```

For TypeScript:

```json
{
  "sections": {
    "imports": ["Thing, { Helper } from ./types", "* as Utils from ./utils"],
    "globals": ["TOP_LEVEL_CONST", "arrowFunction", "mutableValue"],
    "classes": ["MyClass", "MyClass.InnerClass"],
    "functions": ["namedFunction", "arrowFunction"],
    "interfaces": ["MyInterface"],
    "type_aliases": ["MyType"],
    "enums": ["MyEnum"],
    "re_exports": ["{ SharedThing } from ./shared", "* from ./everything"]
  }
}
```

### Specific recommendations by section

#### Imports

Return display strings, not structured objects.

Reason:
- import discovery is mainly about recognizing dependencies and likely symbol origins
- the exact decomposition into `module`, `name`, `alias`, `default`, `namespace`, `named` is overkill for first-pass exploration

#### Globals

Return just names.

Reason:
- `declaration_kind` is rarely the thing that guides the next exploration step
- if the symbol matters, the model can fetch its source

#### Functions

Return just names.

Reason:
- `syntax: function|arrow` is usually irrelevant for exploration
- if syntax matters, fetching the symbol gives the real answer

#### Classes

Return flattened qualified names instead of nested structs.

Recommended format:

```json
"classes": ["MyClass", "MyClass.InnerClass"]
```

Reason:
- nested trees are expensive
- for navigation, the model mostly needs to know what can be fetched by name
- flattened qualified names directly support follow-up `fetch_symbol` calls

#### Members / methods / accessors

Do not include these in baseline parse output.

If they are needed later, expose them through either:

- a future optional verbosity mode, or
- `fetch_symbol` on the containing class

Reason:
- they create a lot of tokens
- they mix discovery with deep inspection
- they are often not needed until after the model has identified the relevant class

### What to do with `available_symbol_types`

Two good options:

#### Option A: keep it only when `content` is omitted

This preserves discoverability for callers asking for a file overview.

#### Option B: drop it entirely and let `sections.keys()` be the contract

This is even leaner, but slightly less explicit.

### Recommendation

Prefer Option A:

- if caller requests a subset, return only the requested populated sections
- if caller requests full parse, return `available_symbol_types` plus compact string arrays

### Why this helps the LLM

- the response becomes mostly names, which are the highest-value exploration tokens
- it encourages a clean workflow: discover in `parse_file`, inspect in `fetch_symbol`
- qualified class names reduce guesswork for nested symbol fetching

---

### 3. `fetch_symbol`

### What an LLM actually needs

This tool is already closest to what a model wants:

- the code for exactly one symbol

### What feels redundant today

Current response includes:

- `filename`
- `language`
- `symbol`
- `symbol_type`
- `code`

Potential redundancies:

- `filename`: caller already supplied it
- `symbol`: caller already supplied it
- `language`: can often be inferred from filename
- `symbol_type`: occasionally useful, but secondary to the code itself

### Recommended output direction

Make the success response mostly code-centric.

Preferred minimal shape:

```json
{
  "code": "..."
}
```

Practical compact shape if a little metadata is still desired:

```json
{
  "symbol_type": "interfaces",
  "code": "export interface MyInterface {\n  id: string;\n}"
}
```

### Recommendation

Use a two-tier principle:

- always return `code`
- keep at most one extra metadata field if it materially helps downstream reasoning

Of the current fields, `symbol_type` is the only one with some recurring value.

So the best compact success shape is likely:

```json
{
  "symbol_type": "interfaces",
  "code": "..."
}
```

### Error responses

Error responses should remain explicit and structured.

They are not the place to optimize aggressively, because the model needs them to recover.

That said, errors should avoid unnecessary duplicated fields too. If the request already names the file and symbol, error payloads do not need to restate both unless the transport requires it.

### Why this helps the LLM

- `fetch_symbol` becomes a low-noise code retrieval primitive
- nearly all tokens go to the code the model actually wants to read
- response shape becomes stable and predictable

---

## Cross-tool design recommendations

### 1. Stop echoing request arguments by default

Across all three tools, avoid returning fields that simply repeat caller inputs:

- `subfolder`
- `pattern`
- `filename`
- `symbol`

These are already in the conversation/tool call.

Exception:
- keep normalized values only if normalization itself is meaningful and not obvious

### 2. Prefer omission over empty arrays and null-heavy payloads

If a section is absent or unrequested, omit it.

Examples:
- do not emit empty `interfaces`, `enums`, `re_exports` arrays in every parse response
- do not emit fields whose value is always `null` in success cases

This saves tokens and makes the real content stand out.

### 3. Separate discovery from inspection

The three tools naturally map to a good exploration loop:

1. `get_project_structure` → find candidate files
2. `parse_file` → discover symbols by name
3. `fetch_symbol` → read exact code

The output format should reinforce that separation:

- structure tool: file-focused
- parse tool: name-focused
- fetch tool: code-focused

Avoid mixing deep structural inspection into `parse_file`.

### 4. Favor human-readable compact strings over micro-objects

For LLM consumption, this:

```json
[{ "name": "MyType" }]
```

is almost always worse than this:

```json
["MyType"]
```

Likewise, import/re-export summaries are often more useful as compact strings than decomposed fields.

### 5. Keep determinism

While simplifying, keep:

- deterministic ordering
- stable section names
- stable string formatting conventions

Compact output is only useful if the model can rely on it being consistent.

---

## Suggested target philosophy per tool

### `get_project_structure`
- show me the relevant files
- tell me which parser capabilities exist
- nothing else

### `parse_file`
- show me the symbol names worth navigating to
- avoid structural ceremony
- keep nested names fetchable via qualified strings

### `fetch_symbol`
- give me the code
- only tiny metadata if it clearly helps

---

## Recommended prioritization

If this is done incrementally, prioritize in this order:

1. simplify `parse_file` sections into arrays of strings
2. remove echoed request fields from all responses
3. make `get_project_structure` render relative to the requested subfolder
4. collapse `get_project_structure` language metadata into a single compact field
5. reduce `fetch_symbol` success metadata to `code` plus maybe `symbol_type`

This order gives the biggest token savings first, especially for repeated exploratory parsing.

---

## Main outcome to aim for

A good final design would make the tools feel like this:

- `get_project_structure`: compact file map
- `parse_file`: compact symbol index
- `fetch_symbol`: exact code extractor

That is the shape an LLM can use repeatedly without paying a boilerplate tax on every step.