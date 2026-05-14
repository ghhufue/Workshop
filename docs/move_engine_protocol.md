# MoveEngine JSON Lines Protocol

`MoveEngine` is a generic process that receives one board and returns one move.
It may be a rule program, search program, C++ executable, Python script, or neural-network inference process.

`Bot` is reserved for a game opponent role, usually a rule-based machine used in modes such as human-vs-bot or model-vs-bot. A bot can be implemented as a MoveEngine, but not every MoveEngine should be called a bot.

## Process Boundary

```text
Local Move Service
        |
        | stdin/stdout JSON Lines
        v
MoveEngine Process
```

The Local Move Service owns platform state: player color, turn index, request id, timeout policy, move validation, Godot row/col conversion, and Match Server integration.

The MoveEngine only receives a board from its own perspective and returns coordinates.

## Input

The service writes one JSON object per line to the engine stdin:

```json
{
  "board": [
    [0, 0, 0],
    [0, 1, 0],
    [0, -1, 0]
  ]
}
```

Cell values are from the engine perspective:

```text
0  = empty
1  = engine side
-1 = opponent side
```

The service converts platform board values before sending the request.

## Output

The engine writes one JSON object per line to stdout. The minimum response is:

```json
{
  "x": 7,
  "y": 8
}
```

The parser is intentionally loose. It also accepts:

```json
{
  "move": {"x": 7, "y": 8},
  "debug": {"thinking_ms": 25}
}
```

and:

```json
{
  "row": 8,
  "col": 7
}
```

Internally, coordinates are normalized to:

```text
x = column
y = row
```

Godot responses can then use:

```text
row = y
col = x
```

Any `debug` object is preserved for later upload/display. Extra top-level fields are treated as debug metadata when no explicit `debug` object exists.

## stdout/stderr

`stdout` should contain protocol JSON only. Debug logs should be written to `stderr`.
