# Remaster notes

These notes describe redesign opportunities observed while playing and
cataloguing the original. They are not claims about original behavior that has
not yet been verified.

## Immediate presentation issues

- Dialogue is slow and input-heavy. A press is needed to finish the current
  text-reveal step, followed by another press to advance. A remaster should
  offer instant text, faster reveal speeds, press-to-complete, press-to-advance,
  auto-advance, and a backlog. The common case should not require two presses
  per short line.
- The original sprite work is weak, particularly in silhouette, pose variety,
  and animation. Preserve the original assets in the catalogue, but consider
  replacement sprites and animation as a central remaster feature rather than
  merely scaling or filtering the originals.
- Pixel-perfect nearest-neighbor presentation should remain available for the
  preserved original. It does not solve limitations in the source artwork.

## Story material recovered

The 2.0.0 bundle contains the complete localized English text tables for the
main campaign: `Introduction`, `StoryTxt00` through `StoryTxt09`, and
`Epilogue` (470 entries total). It also contains seven optional/free-scenario
tables, `FreeTxt28` through `FreeTxt33` and `FreeTxt35` (156 entries). There is
no `FreeTxt34` resource in this build.

This is complete shipped **text**, not yet a complete executable screenplay.
The scenario event/command format still needs to be decoded to establish exact
speaker identity, portrait and animation cues, runtime ordering, conditions,
branches, pauses, and unused lines.

## Quick narrative assessment

The main campaign follows Alan, a commander of Julius who obeys a belligerent
king despite growing doubts. Julius destroys Herbert, fights the expansionist
Sandia, and invades peaceful Frost. Alan's former friend Dean survives
Herbert's fall; Frost's Queen Viola is Alan's old acquaintance and eventual
love interest. The three nations exhaust one another while repeatedly debating
what makes a cause worth fighting for.

General Claude of Sandia wants to end conflict for the sake of his daughter,
but turns that desire into conquest and ultimately takes his own life. Dean
then adopts a similarly absolutist idea: peace requires eliminating every
source of strife. Their parallel is one of the more useful pieces of thematic
material.

The political conflict is eventually displaced by Zelgius, ruler of the
Netherworld. He manipulated the king, fed on the negative energy produced by
war, and mind-controls the surviving armies. Viola apparently sacrifices
herself for Alan, Dean dies freeing the soldiers, and Alan unites the former
enemies to defeat Zelgius. Viola survives, but the world has already been
devastated. Alan and Viola resolve to rebuild amid the ruins. A short epilogue
implies that an unidentified higher being prevents Zelgius from passing into
the Beyond.

The broad anti-war premise and ruined-world ending have potential. Most of the
execution is repetitive exposition, generic battle dialogue, and variations on
“what are you fighting for?” The supernatural reveal weakens the more
interesting political responsibility by making an external demon the final
cause. A remaster could keep the nations, relationships, Claude/Dean parallel,
and desolate ending while drastically condensing or rewriting scene dialogue.

The optional scenarios provide some useful backstory—Claude's earlier revolt,
Viola deciding to fight, Dean in exile, and Zelgius recruiting his servants—but
also contain disposable comedy. `FreeTxt35`, for example, builds an extended
exchange around Damon asking Saki whether it is her “time of the month.” Such
material should be preserved in the historical transcript, not treated as
writing that a remaster needs to reproduce unchanged.

