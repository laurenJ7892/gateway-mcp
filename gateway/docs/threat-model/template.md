# Title

## Threat

Name the threat on this server. Name the file, the field, or the message.

## Measure

Name the one measure this server adopts. Link [001. Orchestration](../adr/001-orchestration.md) when that record is why the client sees the tool description, the arguments, or the result. Leave the link out when this file is the only record of the measure. Add a new ADR when a second option would change this server.

## Evaluation

Say whether this server applies the measure. Start with `Applied.` or `Not applied yet.` When the measure is not applied, say why. Name the file or the test a reader can check.

## Server change

Name the one change in this repo. Name the file and the test.

Copy this file to `kebab-title.md` in this directory. Replace `Title` with the threat name. Replace every sentence under a heading.

Add a section to [summary.md](summary.md). Use the threat name as the heading. Link the new file. Under `Threat`, write the threat in one sentence. Under `Measure`, copy the measure in one or two sentences. Under `Evaluation`, copy the evaluation in one sentence. Leave `Commit` and `Date` empty until the commit that adopts the measure. `Commit` is that commit's subject line. `Date` is that commit's date, `YYYY-MM-DD`. Put an ADR link in the threat file. Leave the link out of the summary.
