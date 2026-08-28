# Frozen sorted variable-residual-bond protocol

Locked on 2026-08-20 before executing a variable-residual-bond recurrence.

## Design inputs

The existing fixed residual ladders R128 and R256 on `ibm32/confirm/sorted`
were used only to select a single schedule. The exact dense oracle values were
not used in the selection objective. The available paired correction budget is

`|Delta_MPS| - compressed_first_term = 0.18733613088137425`.

The fixed R128 correction is `0.21919816464699163` and fails. Fixed R256 gives
`0.14304864269016626` and passes.

## Frozen schedule

Keep the already frozen primary backward schedule unchanged. Use the residual
schedule

- checkpoint positions 1-303: residual bond 256;
- checkpoint positions 304-555: residual bond 128.

The fixed-ladder additive design proxy predicts paired correction
`0.15587187624384635`, paired width `0.22344018259738840`, and margin
`0.03146425463752789`. This proxy is not a certificate because residual states
depend recursively on earlier compression choices. The schedule must therefore
be executed end-to-end and certified from its own recurrence.

## Success criteria

Primary success requires the newly executed variable-bond recurrence to satisfy

`compressed_first_term_pair + operator_correction_pair < |Delta_MPS|`

with no dense-oracle audit violation. Resource success requires cubic residual
bond-work no greater than 0.65 of fixed R256. The prespecified schedule has proxy

`(303*256^3 + 252*128^3)/(555*256^3) = 0.6027027027`.

Failure is retained. No range endpoint may be changed for the primary result.
