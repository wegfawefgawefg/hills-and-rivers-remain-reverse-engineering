# Localized strings

The app contains 282 `.strings` tables and 6,894 key/value entries across
English, French, German, Japanese, and Spanish. Most tables are Apple binary
property lists. The five `Settings.bundle/*/Root.strings` files use UTF-8
OpenStep strings syntax instead. Both encodings are decoded strictly.

Stable entry identity is locale, table name, and original key. Entries sharing
table and key are related across locales without assuming that every locale has
identical coverage. Counts are:

| Locale | Entries |
| --- | ---: |
| English | 1,379 |
| French | 1,378 |
| German | 1,378 |
| Japanese | 1,381 |
| Spanish | 1,378 |

Important authored tables include `Tutorial`, `Introduction`, `StoryTxt00`
through `StoryTxt09`, `FreeTxt28` through `FreeTxt35`, `MapInfo`, `Game`, item
messages, character names, controls, rules, and results. These are functional
content: they preserve dialogue sequencing vocabulary, rule descriptions, and
the identifiers that binary scenario events are expected to reference.
