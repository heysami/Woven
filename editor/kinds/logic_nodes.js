// Shared client/server node definitions. Keep the assignment JSON-compatible.
globalThis.TH_LOGIC_NODE_DEFS = {
  "input-pointer": {
    "glyph": "‹",
    "label": "Pointer",
    "section": "Sources",
    "w": 220,
    "h": 300,
    "desc": "Mouse / single-pointer on the render surface",
    "controls": {
      "space": {
        "type": "select",
        "value": "normalized",
        "options": [
          "normalized",
          "pixels"
        ]
      },
      "button": {
        "type": "select",
        "value": "any",
        "options": [
          "any",
          "left",
          "right",
          "middle"
        ]
      }
    },
    "provides": {
      "x": {
        "label": "x",
        "dtype": "number"
      },
      "y": {
        "label": "y",
        "dtype": "number"
      },
      "isDown": {
        "label": "isDown",
        "dtype": "boolean"
      },
      "clicked": {
        "label": "clicked",
        "dtype": "event"
      },
      "downX": {
        "label": "downX",
        "dtype": "number"
      },
      "downY": {
        "label": "downY",
        "dtype": "number"
      },
      "upX": {
        "label": "upX",
        "dtype": "number"
      },
      "upY": {
        "label": "upY",
        "dtype": "number"
      },
      "hover": {
        "label": "hover",
        "dtype": "boolean"
      },
      "pos": {
        "label": "pos",
        "dtype": "vector2"
      }
    },
    "accepts": {}
  },
  "input-touch": {
    "glyph": "⊛",
    "label": "Touch",
    "section": "Sources",
    "w": 220,
    "h": 320,
    "desc": "Multi-touch on the render surface",
    "controls": {
      "maxPoints": {
        "type": "number",
        "value": 5,
        "min": 1,
        "max": 10,
        "step": 1
      },
      "space": {
        "type": "select",
        "value": "normalized",
        "options": [
          "normalized",
          "pixels"
        ]
      }
    },
    "provides": {
      "count": {
        "label": "count",
        "dtype": "number"
      },
      "pos": {
        "label": "pos",
        "dtype": "vector2"
      },
      "touches": {
        "label": "touches",
        "dtype": "vector2"
      },
      "isDown": {
        "label": "isDown",
        "dtype": "boolean"
      },
      "center": {
        "label": "center",
        "dtype": "vector2"
      },
      "spread": {
        "label": "spread",
        "dtype": "number"
      },
      "pinchDelta": {
        "label": "pinchDelta",
        "dtype": "number"
      },
      "rotation": {
        "label": "rotation",
        "dtype": "number"
      },
      "tap": {
        "label": "tap",
        "dtype": "event"
      }
    },
    "accepts": {}
  },
  "input-keyboard": {
    "glyph": "⎄",
    "label": "Keyboard",
    "section": "Sources",
    "w": 220,
    "h": 280,
    "desc": "Keyboard on the render surface",
    "controls": {
      "key": {
        "type": "text",
        "value": ""
      },
      "repeat": {
        "type": "boolean",
        "value": false
      }
    },
    "provides": {
      "key": {
        "label": "key",
        "dtype": "string"
      },
      "isDown": {
        "label": "isDown",
        "dtype": "boolean"
      },
      "pressed": {
        "label": "pressed",
        "dtype": "event"
      },
      "released": {
        "label": "released",
        "dtype": "event"
      },
      "axisX": {
        "label": "axisX",
        "dtype": "number"
      },
      "axisY": {
        "label": "axisY",
        "dtype": "number"
      }
    },
    "accepts": {}
  },
  "input-scroll": {
    "glyph": "⇕",
    "label": "Scroll",
    "section": "Sources",
    "w": 220,
    "h": 280,
    "desc": "Wheel / scroll on the render surface",
    "controls": {
      "space": {
        "type": "select",
        "value": "normalized",
        "options": [
          "normalized",
          "pixels"
        ]
      },
      "clampMin": {
        "type": "number",
        "value": 0,
        "step": 0.01
      },
      "clampMax": {
        "type": "number",
        "value": 1,
        "step": 0.01
      }
    },
    "provides": {
      "deltaY": {
        "label": "deltaY",
        "dtype": "number"
      },
      "deltaX": {
        "label": "deltaX",
        "dtype": "number"
      },
      "accumY": {
        "label": "accumY",
        "dtype": "number"
      },
      "accumX": {
        "label": "accumX",
        "dtype": "number"
      },
      "velocity": {
        "label": "velocity",
        "dtype": "number"
      }
    },
    "accepts": {}
  },
  "input-gyro": {
    "glyph": "┑",
    "label": "Gyro",
    "section": "Sources",
    "w": 220,
    "h": 260,
    "desc": "Device orientation (mobile-primary)",
    "controls": {
      "smoothing": {
        "type": "number",
        "value": 0.2,
        "min": 0,
        "max": 1,
        "step": 0.01
      }
    },
    "provides": {
      "alpha": {
        "label": "alpha",
        "dtype": "number"
      },
      "beta": {
        "label": "beta",
        "dtype": "number"
      },
      "gamma": {
        "label": "gamma",
        "dtype": "number"
      },
      "tilt": {
        "label": "tilt",
        "dtype": "vector2"
      },
      "ready": {
        "label": "ready",
        "dtype": "boolean"
      }
    },
    "accepts": {}
  },
  "input-audio": {
    "glyph": "▿",
    "label": "Audio",
    "section": "Sources",
    "w": 220,
    "h": 300,
    "desc": "Microphone / audio asset level, pitch, bands",
    "controls": {
      "source": {
        "type": "select",
        "value": "mic",
        "options": [
          "mic",
          "asset"
        ]
      },
      "band": {
        "type": "select",
        "value": "full",
        "options": [
          "bass",
          "mid",
          "treble",
          "full"
        ]
      },
      "fftSize": {
        "type": "number",
        "value": 2048,
        "min": 32,
        "max": 32768,
        "step": 1
      },
      "smoothing": {
        "type": "number",
        "value": 0.8,
        "min": 0,
        "max": 1,
        "step": 0.01
      }
    },
    "provides": {
      "level": {
        "label": "level",
        "dtype": "number"
      },
      "pitch": {
        "label": "pitch",
        "dtype": "number"
      },
      "band": {
        "label": "band",
        "dtype": "number"
      },
      "beat": {
        "label": "beat",
        "dtype": "event"
      },
      "spectrum": {
        "label": "spectrum",
        "dtype": "channel"
      },
      "bands": {
        "label": "bands",
        "dtype": "channel"
      }
    },
    "accepts": {
      "asset": {
        "label": "Audio asset (source=asset)",
        "dtype": "string",
        "tags": [
          "asset",
          "audio"
        ]
      }
    }
  },
  "input-gamepad": {
    "glyph": "⊞",
    "label": "Gamepad",
    "section": "Sources",
    "w": 220,
    "h": 300,
    "desc": "Gamepad sticks + buttons (no permission)",
    "controls": {},
    "provides": {
      "leftStick": {
        "label": "leftStick",
        "dtype": "vector2"
      },
      "rightStick": {
        "label": "rightStick",
        "dtype": "vector2"
      },
      "x": {
        "label": "x",
        "dtype": "number"
      },
      "y": {
        "label": "y",
        "dtype": "number"
      },
      "a": {
        "label": "a",
        "dtype": "boolean"
      },
      "b": {
        "label": "b",
        "dtype": "boolean"
      },
      "connected": {
        "label": "connected",
        "dtype": "boolean"
      }
    },
    "accepts": {}
  },
  "input-accel": {
    "glyph": "⊕",
    "label": "Accel",
    "section": "Sources",
    "w": 220,
    "h": 240,
    "desc": "Device motion / accelerometer (permission-gated)",
    "controls": {},
    "provides": {
      "x": {
        "label": "x",
        "dtype": "number"
      },
      "y": {
        "label": "y",
        "dtype": "number"
      },
      "z": {
        "label": "z",
        "dtype": "number"
      },
      "ready": {
        "label": "ready",
        "dtype": "boolean"
      }
    },
    "accepts": {}
  },
  "input-midi": {
    "glyph": "⊟",
    "label": "MIDI",
    "section": "Sources",
    "w": 220,
    "h": 300,
    "desc": "WebMIDI controller: note / velocity / CC (permission-gated)",
    "controls": {},
    "provides": {
      "note": {
        "label": "note",
        "dtype": "number"
      },
      "velocity": {
        "label": "velocity",
        "dtype": "number"
      },
      "cc": {
        "label": "cc",
        "dtype": "number"
      },
      "ccValue": {
        "label": "ccValue",
        "dtype": "number"
      },
      "gate": {
        "label": "gate",
        "dtype": "boolean"
      },
      "ready": {
        "label": "ready",
        "dtype": "boolean"
      }
    },
    "accepts": {}
  },
  "input-camera": {
    "glyph": "⊙",
    "label": "Camera",
    "section": "Sources",
    "w": 220,
    "h": 240,
    "desc": "Live webcam stream handle",
    "controls": {
      "facing": {
        "type": "select",
        "value": "user",
        "options": [
          "user",
          "environment"
        ]
      },
      "resolution": {
        "type": "select",
        "value": "medium",
        "options": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "provides": {
      "stream": {
        "label": "stream",
        "dtype": "string"
      },
      "ready": {
        "label": "ready",
        "dtype": "boolean"
      },
      "layer": {
        "label": "Layer",
        "dtype": "layer",
        "tags": [
          "layer"
        ]
      }
    },
    "accepts": {}
  },
  "input-video": {
    "glyph": "▷",
    "label": "Video",
    "section": "Sources",
    "w": 220,
    "h": 240,
    "desc": "A video asset / clip as a stream handle",
    "controls": {
      "loop": {
        "type": "boolean",
        "value": true
      },
      "autoplay": {
        "type": "boolean",
        "value": true
      }
    },
    "provides": {
      "stream": {
        "label": "stream",
        "dtype": "string"
      },
      "t": {
        "label": "t",
        "dtype": "number"
      },
      "playing": {
        "label": "playing",
        "dtype": "boolean"
      },
      "layer": {
        "label": "Layer",
        "dtype": "layer",
        "tags": [
          "layer"
        ]
      }
    },
    "accepts": {
      "asset": {
        "label": "Video asset",
        "dtype": "string",
        "tags": [
          "asset",
          "video"
        ]
      }
    }
  },
  "vision-detect": {
    "glyph": "◉",
    "label": "Vision detect",
    "section": "Processors",
    "w": 240,
    "h": 480,
    "desc": "MediaPipe Tasks Vision: face / hand / object detection",
    "controls": {
      "detector": {
        "type": "select",
        "value": "face",
        "options": [
          "face",
          "hand",
          "object"
        ]
      },
      "target": {
        "type": "select",
        "value": "present",
        "options": [
          "present",
          "count",
          "location",
          "gesture"
        ]
      },
      "hand": {
        "type": "select",
        "value": "primary",
        "options": [
          "primary",
          "leftmost",
          "rightmost",
          "second"
        ]
      }
    },
    "provides": {
      "present": {
        "label": "present",
        "dtype": "boolean"
      },
      "count": {
        "label": "count",
        "dtype": "number"
      },
      "pos": {
        "label": "pos",
        "dtype": "vector2"
      },
      "region": {
        "label": "region",
        "dtype": "region"
      },
      "gesture": {
        "label": "gesture",
        "dtype": "string"
      },
      "confidence": {
        "label": "confidence",
        "dtype": "number"
      },
      "wrist": {
        "label": "wrist",
        "dtype": "vector2"
      },
      "thumbTip": {
        "label": "thumbTip",
        "dtype": "vector2"
      },
      "indexTip": {
        "label": "indexTip",
        "dtype": "vector2"
      },
      "middleTip": {
        "label": "middleTip",
        "dtype": "vector2"
      },
      "ringTip": {
        "label": "ringTip",
        "dtype": "vector2"
      },
      "pinkyTip": {
        "label": "pinkyTip",
        "dtype": "vector2"
      },
      "nose": {
        "label": "nose",
        "dtype": "vector2"
      },
      "leftEye": {
        "label": "leftEye",
        "dtype": "vector2"
      },
      "rightEye": {
        "label": "rightEye",
        "dtype": "vector2"
      }
    },
    "accepts": {
      "stream": {
        "label": "stream",
        "dtype": "string"
      }
    }
  },
  "vision-ocr": {
    "glyph": "⊜",
    "label": "Vision OCR",
    "section": "Processors",
    "w": 240,
    "h": 280,
    "desc": "tesseract.js text recognition over a stream",
    "controls": {
      "query": {
        "type": "text",
        "value": ""
      },
      "interval": {
        "type": "number",
        "value": 500,
        "min": 50,
        "max": 10000,
        "step": 50
      }
    },
    "provides": {
      "text": {
        "label": "text",
        "dtype": "string"
      },
      "matched": {
        "label": "matched",
        "dtype": "boolean"
      },
      "region": {
        "label": "region",
        "dtype": "region"
      },
      "count": {
        "label": "count",
        "dtype": "number"
      }
    },
    "accepts": {
      "stream": {
        "label": "stream",
        "dtype": "string"
      }
    }
  },
  "palette": {
    "glyph": "◧",
    "label": "Palette",
    "section": "Processors",
    "w": 240,
    "h": 440,
    "desc": "Extract N dominant colors from a wired image",
    "controls": {
      "count": {
        "type": "number",
        "value": 5,
        "min": 2,
        "max": 8,
        "step": 1
      },
      "quality": {
        "type": "number",
        "value": 4,
        "min": 1,
        "max": 16,
        "step": 1
      }
    },
    "provides": {
      "color0": {
        "label": "color0",
        "dtype": "color"
      },
      "color1": {
        "label": "color1",
        "dtype": "color"
      },
      "color2": {
        "label": "color2",
        "dtype": "color"
      },
      "color3": {
        "label": "color3",
        "dtype": "color"
      },
      "color4": {
        "label": "color4",
        "dtype": "color"
      },
      "color5": {
        "label": "color5",
        "dtype": "color"
      },
      "color6": {
        "label": "color6",
        "dtype": "color"
      },
      "color7": {
        "label": "color7",
        "dtype": "color"
      },
      "dominant": {
        "label": "dominant",
        "dtype": "color"
      },
      "domR": {
        "label": "dom R",
        "dtype": "number"
      },
      "domG": {
        "label": "dom G",
        "dtype": "number"
      },
      "domB": {
        "label": "dom B",
        "dtype": "number"
      },
      "ready": {
        "label": "ready",
        "dtype": "boolean"
      },
      "count": {
        "label": "count",
        "dtype": "number"
      }
    },
    "accepts": {
      "image": {
        "label": "Image asset",
        "dtype": "string",
        "tags": [
          "asset",
          "image"
        ]
      }
    }
  },
  "value-bool": {
    "glyph": "⊤",
    "label": "Boolean",
    "section": "Literals",
    "w": 200,
    "h": 200,
    "desc": "Constant boolean value",
    "controls": {
      "value": {
        "type": "boolean",
        "value": true
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "boolean"
      }
    },
    "accepts": {}
  },
  "value-string": {
    "glyph": "⊏",
    "label": "String",
    "section": "Literals",
    "w": 220,
    "h": 220,
    "desc": "Constant text value",
    "controls": {
      "value": {
        "type": "text",
        "value": ""
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "string"
      }
    },
    "accepts": {}
  },
  "value-vec2": {
    "glyph": "⊕",
    "label": "Vector2",
    "section": "Literals",
    "w": 200,
    "h": 240,
    "desc": "Constant {x,y} vector",
    "controls": {
      "x": {
        "type": "number",
        "value": 0.5,
        "step": 0.01
      },
      "y": {
        "type": "number",
        "value": 0.5,
        "step": 0.01
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "vector2"
      }
    },
    "accepts": {}
  },
  "op-math": {
    "glyph": "∑",
    "label": "Math",
    "section": "Operators",
    "w": 220,
    "h": 240,
    "desc": "Binary math on two numbers",
    "controls": {
      "op": {
        "type": "select",
        "value": "add",
        "options": [
          "add",
          "sub",
          "mul",
          "div",
          "mod",
          "min",
          "max",
          "pow",
          "atan2"
        ]
      }
    },
    "provides": {
      "r": {
        "label": "r",
        "dtype": "number"
      }
    },
    "accepts": {
      "a": {
        "label": "a",
        "dtype": "number"
      },
      "b": {
        "label": "b",
        "dtype": "number"
      }
    }
  },
  "op-unary": {
    "glyph": "ƒ",
    "label": "Unary",
    "section": "Operators",
    "w": 220,
    "h": 220,
    "desc": "Unary math on one number",
    "controls": {
      "op": {
        "type": "select",
        "value": "abs",
        "options": [
          "abs",
          "neg",
          "floor",
          "round",
          "sin",
          "cos",
          "sqrt",
          "sign"
        ]
      }
    },
    "provides": {
      "r": {
        "label": "r",
        "dtype": "number"
      }
    },
    "accepts": {
      "a": {
        "label": "a",
        "dtype": "number"
      }
    }
  },
  "op-compare": {
    "glyph": "≷",
    "label": "Compare",
    "section": "Operators",
    "w": 220,
    "h": 240,
    "desc": "Compare two numbers, emit boolean",
    "controls": {
      "op": {
        "type": "select",
        "value": "gt",
        "options": [
          "eq",
          "ne",
          "lt",
          "gt",
          "le",
          "ge"
        ]
      },
      "epsilon": {
        "type": "number",
        "value": 0.0001,
        "step": 0.0001
      }
    },
    "provides": {
      "r": {
        "label": "r",
        "dtype": "boolean"
      }
    },
    "accepts": {
      "a": {
        "label": "a",
        "dtype": "number"
      },
      "b": {
        "label": "b",
        "dtype": "number"
      }
    }
  },
  "op-logic": {
    "glyph": "&",
    "label": "Logic",
    "section": "Operators",
    "w": 220,
    "h": 240,
    "desc": "Boolean logic on two booleans",
    "controls": {
      "op": {
        "type": "select",
        "value": "and",
        "options": [
          "and",
          "or",
          "xor",
          "nand",
          "nor"
        ]
      }
    },
    "provides": {
      "r": {
        "label": "r",
        "dtype": "boolean"
      }
    },
    "accepts": {
      "a": {
        "label": "a",
        "dtype": "boolean"
      },
      "b": {
        "label": "b",
        "dtype": "boolean"
      }
    }
  },
  "op-map": {
    "glyph": "↦",
    "label": "Map",
    "section": "Operators",
    "w": 240,
    "h": 320,
    "desc": "Remap + clamp + ease a number",
    "controls": {
      "inMin": {
        "type": "number",
        "value": 0,
        "step": 0.01
      },
      "inMax": {
        "type": "number",
        "value": 1,
        "step": 0.01
      },
      "outMin": {
        "type": "number",
        "value": 0,
        "step": 0.01
      },
      "outMax": {
        "type": "number",
        "value": 1,
        "step": 0.01
      },
      "clamp": {
        "type": "boolean",
        "value": true
      },
      "ease": {
        "type": "select",
        "value": "linear",
        "options": [
          "linear",
          "in",
          "out",
          "inout"
        ]
      }
    },
    "provides": {
      "r": {
        "label": "r",
        "dtype": "number"
      }
    },
    "accepts": {
      "x": {
        "label": "x",
        "dtype": "number"
      }
    }
  },
  "op-vector": {
    "glyph": "⊿",
    "label": "Vector",
    "section": "Operators",
    "w": 240,
    "h": 280,
    "desc": "Make / break / measure vec2",
    "controls": {
      "mode": {
        "type": "select",
        "value": "make",
        "options": [
          "make",
          "break",
          "distance",
          "add",
          "scale",
          "lerp"
        ]
      }
    },
    "provides": {
      "v": {
        "label": "v",
        "dtype": "vector2"
      },
      "x": {
        "label": "x",
        "dtype": "number"
      },
      "y": {
        "label": "y",
        "dtype": "number"
      },
      "d": {
        "label": "d",
        "dtype": "number"
      }
    },
    "accepts": {
      "x": {
        "label": "x",
        "dtype": "number"
      },
      "y": {
        "label": "y",
        "dtype": "number"
      },
      "v": {
        "label": "v",
        "dtype": "vector2"
      },
      "a": {
        "label": "a",
        "dtype": "vector2"
      },
      "b": {
        "label": "b",
        "dtype": "vector2"
      },
      "t": {
        "label": "t",
        "dtype": "number"
      }
    }
  },
  "op-tostring": {
    "glyph": "“”",
    "label": "To string",
    "section": "Operators",
    "w": 240,
    "h": 240,
    "desc": "Format a value into a string",
    "controls": {
      "template": {
        "type": "text",
        "value": "{v}"
      }
    },
    "provides": {
      "s": {
        "label": "s",
        "dtype": "string"
      }
    },
    "accepts": {
      "a": {
        "label": "a",
        "dtype": "number"
      }
    }
  },
  "flow-if": {
    "glyph": "⋔",
    "label": "If / select",
    "section": "Control flow",
    "w": 240,
    "h": 260,
    "desc": "Pass then-branch when cond, else else-branch",
    "controls": {},
    "provides": {
      "r": {
        "label": "r",
        "dtype": "number"
      }
    },
    "accepts": {
      "cond": {
        "label": "cond",
        "dtype": "boolean"
      },
      "then": {
        "label": "then",
        "dtype": "number"
      },
      "else": {
        "label": "else",
        "dtype": "number"
      }
    }
  },
  "flow-gate": {
    "glyph": "⊳",
    "label": "Gate",
    "section": "Control flow",
    "w": 240,
    "h": 240,
    "desc": "Pass value only while open; else hold last",
    "controls": {
      "holdLast": {
        "type": "boolean",
        "value": true
      }
    },
    "provides": {
      "r": {
        "label": "r",
        "dtype": "number"
      }
    },
    "accepts": {
      "value": {
        "label": "value",
        "dtype": "number"
      },
      "open": {
        "label": "open",
        "dtype": "boolean"
      }
    }
  },
  "flow-while": {
    "glyph": "↻",
    "label": "Bounded sample",
    "section": "Control flow",
    "w": 240,
    "h": 260,
    "desc": "Samples the memoized body up to maxIterations when condition is true; does not run a subgraph loop",
    "controls": {
      "maxIterations": {
        "type": "number",
        "value": 64,
        "min": 1,
        "max": 10000,
        "step": 1
      }
    },
    "provides": {
      "count": {
        "label": "count",
        "dtype": "number"
      },
      "last": {
        "label": "last",
        "dtype": "number"
      }
    },
    "accepts": {
      "cond": {
        "label": "cond",
        "dtype": "boolean"
      },
      "body": {
        "label": "body",
        "dtype": "number"
      }
    }
  },
  "flow-repeat": {
    "glyph": "⟳",
    "label": "Repeat sample",
    "section": "Control flow",
    "w": 240,
    "h": 240,
    "desc": "Repeats a memoized value; index affects external number sources only",
    "controls": {},
    "provides": {
      "sum": {
        "label": "sum",
        "dtype": "number"
      },
      "values": {
        "label": "values",
        "dtype": "number"
      }
    },
    "accepts": {
      "n": {
        "label": "n",
        "dtype": "number"
      },
      "body": {
        "label": "body",
        "dtype": "number"
      }
    }
  },
  "state-counter": {
    "glyph": "№",
    "label": "Counter",
    "section": "State",
    "w": 220,
    "h": 260,
    "desc": "Count inc events; reset clears",
    "controls": {
      "step": {
        "type": "number",
        "value": 1,
        "step": 1
      },
      "wrap": {
        "type": "number",
        "value": 0,
        "step": 1
      }
    },
    "provides": {
      "count": {
        "label": "count",
        "dtype": "number"
      }
    },
    "accepts": {
      "inc": {
        "label": "inc",
        "dtype": "event"
      },
      "reset": {
        "label": "reset",
        "dtype": "event"
      }
    }
  },
  "state-toggle": {
    "glyph": "⇄",
    "label": "Toggle",
    "section": "State",
    "w": 220,
    "h": 220,
    "desc": "Flip a boolean on each flip event",
    "controls": {
      "initial": {
        "type": "boolean",
        "value": false
      }
    },
    "provides": {
      "on": {
        "label": "on",
        "dtype": "boolean"
      }
    },
    "accepts": {
      "flip": {
        "label": "flip",
        "dtype": "event"
      }
    }
  },
  "state-latch": {
    "glyph": "⎍",
    "label": "Latch",
    "section": "State",
    "w": 220,
    "h": 240,
    "desc": "Sample hold when set rises, then keep it",
    "controls": {},
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      }
    },
    "accepts": {
      "set": {
        "label": "set",
        "dtype": "boolean"
      },
      "hold": {
        "label": "hold",
        "dtype": "number"
      }
    }
  },
  "state-timer": {
    "glyph": "⧗",
    "label": "Timer",
    "section": "State",
    "w": 220,
    "h": 260,
    "desc": "Elapsed time between start / stop events",
    "controls": {
      "autostart": {
        "type": "boolean",
        "value": false
      }
    },
    "provides": {
      "elapsed": {
        "label": "elapsed",
        "dtype": "number"
      },
      "running": {
        "label": "running",
        "dtype": "boolean"
      }
    },
    "accepts": {
      "start": {
        "label": "start",
        "dtype": "event"
      },
      "stop": {
        "label": "stop",
        "dtype": "event"
      }
    }
  },
  "state-smooth": {
    "glyph": "∿",
    "label": "Smooth",
    "section": "State",
    "w": 220,
    "h": 240,
    "desc": "Critically-damped pursuit of a target number",
    "controls": {
      "stiffness": {
        "type": "number",
        "value": 8,
        "min": 0,
        "max": 200,
        "step": 0.1
      },
      "damping": {
        "type": "number",
        "value": 1,
        "min": 0,
        "max": 10,
        "step": 0.01
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      }
    },
    "accepts": {
      "target": {
        "label": "target",
        "dtype": "number"
      }
    }
  },
  "gen-lfo": {
    "glyph": "∿",
    "label": "LFO",
    "section": "Generate",
    "w": 220,
    "h": 300,
    "desc": "Low-frequency oscillator (sine/tri/saw/square)",
    "controls": {
      "wave": {
        "type": "select",
        "value": "sine",
        "options": [
          "sine",
          "tri",
          "saw",
          "square"
        ]
      },
      "freq": {
        "type": "number",
        "value": 1,
        "min": 0,
        "max": 30,
        "step": 0.01
      },
      "phase": {
        "type": "number",
        "value": 0,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "lo": {
        "type": "number",
        "value": 0,
        "step": 0.01
      },
      "hi": {
        "type": "number",
        "value": 1,
        "step": 0.01
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      },
      "phase": {
        "label": "phase",
        "dtype": "number"
      }
    },
    "accepts": {}
  },
  "gen-noise": {
    "glyph": "≈",
    "label": "Noise",
    "section": "Generate",
    "w": 220,
    "h": 280,
    "desc": "Smooth value noise over time",
    "controls": {
      "speed": {
        "type": "number",
        "value": 1,
        "min": 0,
        "max": 20,
        "step": 0.01
      },
      "seed": {
        "type": "number",
        "value": 0,
        "step": 1
      },
      "lo": {
        "type": "number",
        "value": 0,
        "step": 0.01
      },
      "hi": {
        "type": "number",
        "value": 1,
        "step": 0.01
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      }
    },
    "accepts": {}
  },
  "gen-clock": {
    "glyph": "◷",
    "label": "Clock",
    "section": "Generate",
    "w": 220,
    "h": 220,
    "desc": "Wall clock: time, frame count, fps",
    "controls": {},
    "provides": {
      "time": {
        "label": "time",
        "dtype": "number"
      },
      "frame": {
        "label": "frame",
        "dtype": "number"
      },
      "fps": {
        "label": "fps",
        "dtype": "number"
      }
    },
    "accepts": {}
  },
  "op-slope": {
    "glyph": "∂",
    "label": "Slope",
    "section": "Operators",
    "w": 220,
    "h": 200,
    "desc": "Rate of change (derivative) of a number",
    "controls": {},
    "provides": {
      "slope": {
        "label": "slope",
        "dtype": "number"
      }
    },
    "accepts": {
      "x": {
        "label": "x",
        "dtype": "number"
      }
    }
  },
  "chop-filter": {
    "glyph": "≀",
    "label": "Filter",
    "section": "Operators",
    "w": 220,
    "h": 240,
    "desc": "One-pole low/high-pass smoothing filter",
    "controls": {
      "mode": {
        "type": "select",
        "value": "low",
        "options": [
          "low",
          "high"
        ]
      },
      "cutoff": {
        "type": "number",
        "value": 0.2,
        "min": 0,
        "max": 1,
        "step": 0.01
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      }
    },
    "accepts": {
      "x": {
        "label": "x",
        "dtype": "number"
      }
    }
  },
  "state-delay": {
    "glyph": "⇥",
    "label": "Delay",
    "section": "State",
    "w": 220,
    "h": 220,
    "desc": "Delay a number by N frames",
    "controls": {
      "frames": {
        "type": "number",
        "value": 8,
        "min": 1,
        "max": 240,
        "step": 1
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      }
    },
    "accepts": {
      "x": {
        "label": "x",
        "dtype": "number"
      }
    }
  },
  "state-trigger": {
    "glyph": "◺",
    "label": "Envelope",
    "section": "State",
    "w": 220,
    "h": 320,
    "desc": "ADSR envelope driven by a gate event",
    "controls": {
      "attack": {
        "type": "number",
        "value": 0.05,
        "min": 0.001,
        "max": 5,
        "step": 0.01
      },
      "decay": {
        "type": "number",
        "value": 0.1,
        "min": 0.001,
        "max": 5,
        "step": 0.01
      },
      "sustain": {
        "type": "number",
        "value": 0.6,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "release": {
        "type": "number",
        "value": 0.3,
        "min": 0.001,
        "max": 5,
        "step": 0.01
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      }
    },
    "accepts": {
      "gate": {
        "label": "gate",
        "dtype": "event"
      }
    }
  },
  "state-trail": {
    "glyph": "≋",
    "label": "Trail",
    "section": "State",
    "w": 220,
    "h": 220,
    "desc": "Record a number into a rolling channel (a scope)",
    "controls": {
      "length": {
        "type": "number",
        "value": 128,
        "min": 2,
        "max": 4096,
        "step": 1
      }
    },
    "provides": {
      "channel": {
        "label": "channel",
        "dtype": "channel"
      }
    },
    "accepts": {
      "x": {
        "label": "x",
        "dtype": "number"
      }
    }
  },
  "chan-sample": {
    "glyph": "⊏",
    "label": "Sample",
    "section": "Channel",
    "w": 220,
    "h": 240,
    "desc": "Read one sample of a channel by index or phase",
    "controls": {
      "mode": {
        "type": "select",
        "value": "index",
        "options": [
          "index",
          "phase"
        ]
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      }
    },
    "accepts": {
      "channel": {
        "label": "channel",
        "dtype": "channel"
      },
      "index": {
        "label": "index",
        "dtype": "number"
      },
      "phase": {
        "label": "phase",
        "dtype": "number"
      }
    }
  },
  "chan-analyze": {
    "glyph": "Σ",
    "label": "Analyze",
    "section": "Channel",
    "w": 220,
    "h": 220,
    "desc": "Reduce a channel to a number (min/max/avg/rms/sum)",
    "controls": {
      "mode": {
        "type": "select",
        "value": "avg",
        "options": [
          "avg",
          "min",
          "max",
          "rms",
          "sum"
        ]
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      }
    },
    "accepts": {
      "channel": {
        "label": "channel",
        "dtype": "channel"
      }
    }
  },
  "dat-fetch": {
    "glyph": "⇄",
    "label": "Fetch",
    "section": "Data",
    "w": 240,
    "h": 320,
    "desc": "Poll a URL (CORS) and cache the response",
    "controls": {
      "url": {
        "type": "text",
        "value": ""
      },
      "method": {
        "type": "select",
        "value": "GET",
        "options": [
          "GET",
          "POST"
        ]
      },
      "pollMs": {
        "type": "number",
        "value": 0,
        "min": 0,
        "max": 600000,
        "step": 100
      }
    },
    "provides": {
      "text": {
        "label": "text",
        "dtype": "string"
      },
      "value": {
        "label": "value",
        "dtype": "number"
      },
      "ok": {
        "label": "ok",
        "dtype": "boolean"
      },
      "updated": {
        "label": "updated",
        "dtype": "event"
      }
    },
    "accepts": {}
  },
  "op-json-path": {
    "glyph": "{}",
    "label": "JSON path",
    "section": "Data",
    "w": 220,
    "h": 240,
    "desc": "Extract a value from a JSON string by dotted path (a.b[0].c)",
    "controls": {
      "path": {
        "type": "text",
        "value": ""
      }
    },
    "provides": {
      "value": {
        "label": "value",
        "dtype": "number"
      },
      "text": {
        "label": "text",
        "dtype": "string"
      }
    },
    "accepts": {
      "text": {
        "label": "text",
        "dtype": "string"
      }
    }
  },
  "dat-websocket": {
    "glyph": "⇌",
    "label": "WebSocket",
    "section": "Data",
    "w": 240,
    "h": 280,
    "desc": "Live WebSocket: latest message + connected flag",
    "controls": {
      "url": {
        "type": "text",
        "value": ""
      }
    },
    "provides": {
      "message": {
        "label": "message",
        "dtype": "string"
      },
      "value": {
        "label": "value",
        "dtype": "number"
      },
      "connected": {
        "label": "connected",
        "dtype": "boolean"
      },
      "updated": {
        "label": "updated",
        "dtype": "event"
      }
    },
    "accepts": {}
  },
  "control-panel": {
    "glyph": "▥",
    "label": "Control panel",
    "section": "Control",
    "w": 240,
    "h": 380,
    "desc": "Live sliders + toggle to drive params",
    "controls": {
      "a": {
        "type": "number",
        "value": 0,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "b": {
        "type": "number",
        "value": 0,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "c": {
        "type": "number",
        "value": 0,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "d": {
        "type": "number",
        "value": 0,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "toggle": {
        "type": "select",
        "value": "off",
        "options": [
          "off",
          "on"
        ]
      }
    },
    "provides": {
      "a": {
        "label": "a",
        "dtype": "number"
      },
      "b": {
        "label": "b",
        "dtype": "number"
      },
      "c": {
        "label": "c",
        "dtype": "number"
      },
      "d": {
        "label": "d",
        "dtype": "number"
      },
      "on": {
        "label": "on",
        "dtype": "boolean"
      }
    },
    "accepts": {}
  },
  "force": {
    "glyph": "⌖",
    "label": "Force",
    "section": "Physics",
    "w": 240,
    "h": 320,
    "desc": "Generic physics force into the composer's shared world",
    "controls": {
      "type": {
        "type": "select",
        "value": "attract",
        "options": [
          "attract",
          "repel",
          "vortex",
          "drag",
          "wind"
        ]
      },
      "radius": {
        "type": "number",
        "value": 0.3,
        "min": 0.01,
        "max": 2,
        "step": 0.01
      },
      "strength": {
        "type": "number",
        "value": 1,
        "min": -10,
        "max": 10,
        "step": 0.05
      },
      "falloff": {
        "type": "number",
        "value": 1,
        "min": 0,
        "max": 4,
        "step": 0.05
      }
    },
    "provides": {
      "out": {
        "label": "Composer ownership",
        "tags": [
          "force"
        ]
      }
    },
    "accepts": {
      "pos": {
        "label": "pos",
        "dtype": "vector2"
      }
    }
  },
  "shape": {
    "glyph": "⬡",
    "label": "Shape",
    "section": "Render",
    "w": 240,
    "h": 420,
    "desc": "Polygon / polyline from wired vector2 points",
    "controls": {
      "closed": {
        "type": "boolean",
        "value": true
      },
      "fill": {
        "type": "text",
        "value": ""
      },
      "stroke": {
        "type": "text",
        "value": "#6ee7ff"
      },
      "strokeWidth": {
        "type": "number",
        "value": 2,
        "min": 0,
        "max": 64,
        "step": 0.5
      },
      "opacity": {
        "type": "number",
        "value": 1,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "blend": {
        "type": "select",
        "value": "normal",
        "options": [
          "normal",
          "multiply",
          "screen",
          "overlay"
        ]
      },
      "z": {
        "type": "number",
        "value": 0,
        "step": 1
      },
      "smoothing": {
        "type": "number",
        "value": 0,
        "min": 0,
        "max": 1,
        "step": 0.01
      }
    },
    "provides": {
      "out": {
        "label": "Layer",
        "dtype": "layer",
        "tags": [
          "layer"
        ]
      }
    },
    "accepts": {
      "p0": {
        "label": "p0",
        "dtype": "vector2"
      },
      "p1": {
        "label": "p1",
        "dtype": "vector2"
      },
      "p2": {
        "label": "p2",
        "dtype": "vector2"
      },
      "p3": {
        "label": "p3",
        "dtype": "vector2"
      },
      "p4": {
        "label": "p4",
        "dtype": "vector2"
      },
      "p5": {
        "label": "p5",
        "dtype": "vector2"
      },
      "p6": {
        "label": "p6",
        "dtype": "vector2"
      },
      "p7": {
        "label": "p7",
        "dtype": "vector2"
      },
      "fill": {
        "label": "fill (color)",
        "dtype": "color"
      },
      "stroke": {
        "label": "stroke (color)",
        "dtype": "color"
      },
      "content": {
        "label": "Fill content / effect",
        "tags": [
          "asset",
          "layer",
          "effect"
        ]
      }
    }
  },
  "type-motion": {
    "glyph": "⒜",
    "label": "Kinetic Type",
    "section": "Render",
    "w": 240,
    "h": 560,
    "desc": "Per-glyph animated text (kinetic typography)",
    "controls": {
      "text": {
        "type": "text",
        "value": "WOVEN"
      },
      "font": {
        "type": "text",
        "value": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
      },
      "weight": {
        "type": "number",
        "value": 800,
        "min": 100,
        "max": 900,
        "step": 100
      },
      "size": {
        "type": "number",
        "value": 120,
        "min": 4,
        "max": 1000,
        "step": 1
      },
      "color": {
        "type": "text",
        "value": "#ffffff"
      },
      "tracking": {
        "type": "number",
        "value": 0,
        "min": -0.5,
        "max": 2,
        "step": 0.01
      },
      "align": {
        "type": "select",
        "value": "center",
        "options": [
          "center",
          "left",
          "right"
        ]
      },
      "behavior": {
        "type": "select",
        "value": "wave",
        "options": [
          "none",
          "wave",
          "jitter",
          "rotate-cycle",
          "scale-pulse",
          "slot-cycle",
          "fade-stagger",
          "typewriter",
          "fall-gravity",
          "elastic-hop",
          "weightless-float",
          "rainbow-cycle",
          "skew-sway",
          "blur-in",
          "squash-stretch",
          "orbit"
        ]
      },
      "speed": {
        "type": "number",
        "value": 1,
        "min": 0,
        "max": 20,
        "step": 0.05
      },
      "amplitude": {
        "type": "number",
        "value": 1,
        "min": 0,
        "max": 10,
        "step": 0.01
      },
      "stagger": {
        "type": "number",
        "value": 0.08,
        "min": 0,
        "max": 2,
        "step": 0.01
      },
      "path": {
        "type": "select",
        "value": "straight",
        "options": [
          "straight",
          "arc",
          "circle",
          "wave",
          "ring"
        ]
      },
      "pathRadius": {
        "type": "number",
        "value": 0.3,
        "min": 0.02,
        "max": 2,
        "step": 0.01
      },
      "pathAmplitude": {
        "type": "number",
        "value": 30,
        "min": 0,
        "max": 400,
        "step": 1
      },
      "pathRotate": {
        "type": "boolean",
        "value": true
      },
      "loop": {
        "type": "boolean",
        "value": true
      },
      "opacity": {
        "type": "number",
        "value": 1,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "blend": {
        "type": "select",
        "value": "normal",
        "options": [
          "normal",
          "multiply",
          "screen",
          "overlay"
        ]
      },
      "z": {
        "type": "number",
        "value": 0,
        "step": 1
      },
      "feedback": {
        "type": "number",
        "value": 0,
        "min": 0,
        "max": 1,
        "step": 0.01
      }
    },
    "provides": {
      "out": {
        "label": "Layer",
        "dtype": "layer",
        "tags": [
          "layer"
        ]
      }
    },
    "accepts": {}
  },
  "audio-out": {
    "glyph": "◢",
    "label": "Audio out",
    "section": "Output",
    "w": 240,
    "h": 360,
    "desc": "WebAudio synth: oscillator -> gain -> lowpass -> out",
    "controls": {
      "waveform": {
        "type": "select",
        "value": "sine",
        "options": [
          "sine",
          "square",
          "saw",
          "triangle"
        ]
      },
      "frequency": {
        "type": "number",
        "value": 220,
        "min": 20,
        "max": 20000,
        "step": 1
      },
      "gain": {
        "type": "number",
        "value": 0.2,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      "cutoff": {
        "type": "number",
        "value": 8000,
        "min": 20,
        "max": 20000,
        "step": 1
      }
    },
    "provides": {
      "out": {
        "label": "Composer ownership",
        "tags": [
          "audio-out"
        ]
      }
    },
    "accepts": {
      "frequency": {
        "label": "frequency",
        "dtype": "number"
      },
      "gain": {
        "label": "gain",
        "dtype": "number"
      },
      "cutoff": {
        "label": "cutoff",
        "dtype": "number"
      },
      "trigger": {
        "label": "trigger",
        "dtype": "event"
      }
    }
  }
};
