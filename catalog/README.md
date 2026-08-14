# Game catalogue

This directory defines the durable catalogue of what can be recovered from each
game build. The catalogue is broader than a decompilation: it records binary
facts, resources, behavior observed in the original executable, and the evidence
behind later interpretations.

Generated databases live in `workspace/catalog/` and are intentionally ignored.
The schema and builder are versioned so any database can be regenerated from a
preserved app bundle.

## Evidence levels

- `fact`: directly measured or present in the artifact, such as a symbol name,
  selector, file hash, Mach-O section, or resource path.
- `observed`: behavior reproduced while executing the original game.
- `inferred`: an interpretation supported by one or more facts but not yet
  proven through control-flow or runtime tracing.
- `hypothesis`: a useful lead requiring verification.

Every subsystem note should point to an address, symbol, resource, runtime log,
or other reproducible evidence. Names recovered from the executable remain the
canonical vocabulary until analysis proves a better meaning.

## Coverage target

The long-term catalogue should cover:

- every Mach-O slice, section, import, symbol, Objective-C class and selector;
- compilation units and recovered C++ types/functions;
- startup, game loop, renderer, input, audio, persistence, networking and IAP;
- every resource, its hash, dimensions/encoding, consumers, and decoded form;
- scenarios, maps, units, entities, rules, AI, progression and text;
- runtime screens, transitions, timings and input/output traces;
- uncertainty, conflicting evidence, and differences between releases.

`tools/build_catalog.py` seeds both the mechanical index and decoded functional
content. Content entries use stable IDs and four independent coverage flags:

- `extracted`: its source bytes have an exact boundary and hash;
- `linked`: a container, consumer, or related record is known;
- `understood`: the fields or behavior have a defensible interpretation;
- `presented`: the content has a usable textual, visual, or audio presentation.

Confidence is separate from coverage. A record boundary can be confirmed while
the record's meaning remains unknown. `content_relationships` records containment,
localization, byte identity, and asset references; `consumer_callsites` connects
content to surviving functions and addresses in each architecture.

Human RE notes and runtime observations should be added incrementally rather
than hidden in a single narrative document.
