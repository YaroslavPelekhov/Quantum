# Third-party provenance

Large benchmark and baseline repositories are referenced as pinned Git
submodules rather than copied into this repository.

| Path | Upstream | Pinned commit | Role |
|---|---|---|---|
| `QOBLIB` | <https://github.com/ZIB-AOPT/QOBLIB> | `52407861bcbab7cee26c4b3a564ea6f8fd80de7d` | benchmark graphs and published BKS records |
| `metriq-gym` | <https://github.com/unitaryfoundation/metriq-gym> | `21a3d7f46d1598e033d589e3741f2e4f548d801a` | benchmark framework explored during scoping |
| `baselines/qoblib-solutions` | <https://github.com/alejomonbar/qoblib-solutions> | `bd3e8a6d36b48b07d53dc605b020d4cb35da2147` | released QOBLIB reduction, QAOA circuit, and decoder |
| `baselines/QAOA-Parameter-Transfer-via-GAT` | <https://github.com/jxsoortha/QAOA-Parameter-Transfer-via-GAT> | `ab8434ffcb2cfcac16d136d8677f327752d9ca8d` | parameter-transfer comparison material |

Each submodule retains its own license and attribution. The snapshot under
`prior_work/evolutionary_computing_portfolio` includes its own source manifest
and SHA-256 metadata; its copied upstream files remain governed by their
original projects' terms. No blanket license statement in this repository
overrides third-party licensing.

