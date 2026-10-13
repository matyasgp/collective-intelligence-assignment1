# Sociodynamics of Emutopia and Kiwiland relations

An agent-based NetLogo model of how cheap distractors can exhaust a limited, slowly refilling resource, and why the result is an abrupt collapse rather than a gradual decline.
Made for Assignment 1 of *Collective Intelligence* (ELTE IK).

The setting is a tongue-in-cheek fictional story. Emutopia keeps sending "airborne humanitarian food deliveries" to Kiwiland, which would rather not receive them. Every wave has a fixed budget: a real drone costs 100, while a decoy costs 15 and does nothing. Kiwiland's bases launch interceptors at whatever drone they pick out on radar, and each base has only a few interceptors, which it reloads slowly.

**Research question:** how do the decoy share of the budget and the defender's ability to recognise decoys decide whether the defence holds?

[![Demo: one base runs out of interceptors and is hit](presentation/demo_poster.png)](presentation/demo.mp4)

*Demo (click to open): red = real drone, yellow = decoy, blue = interceptor.*

## Result

![Mean bases destroyed over decoy share and decoy recognition](latex/fig_sweep.png)

- **The system does not degrade gradually; it tips.**
  - At 20% decoy recognition, losses jump from 0.56 bases without decoys to 3.54 of 4 at 30% decoys.
  - The tipping point is at **22.6% of the budget spent on decoys**, about 1.8 decoys per real drone.
- **Better recognition moves the tipping point up:** it is at 18.8% with 0% recognition and 26.5% with 30% recognition. From 40% recognition on, the defence never collapses.
- **Almost pure decoy swarms are harmless again:** they contain too few real drones. From 78% decoys upward, losses stay below 0.5 bases.

Every setting was run 100 times. The 95% confidence intervals are at most ±0.36 bases. The full write-up is in the [report](latex/documentation.pdf), and the slides are in the [presentation](presentation/presentation.pdf).

## Model

- **Bases** (4 by default) sit in a central homeland. Each holds 10 interceptors and reloads 1 every 4 ticks.
- **Drones** launch in waves from a ring around the homeland and fly straight at their assigned base. Each wave is split evenly over the bases.
- **Interceptors** chase one drone and roll for a hit (85%). An interceptor is used up after one attempt.
- **Decoy recognition:** with this probability a base aims at the nearest *real* drone; otherwise it aims at the nearest drone of either kind.
- **Weather:** random rain showers lower the hit chance.

## Files

| File | Contents |
|---|---|
| `decoy_saturation.nlogox` | The model (NetLogo 7.0.4); the Info tab explains it |
| `decoy_saturation_experiment.xml` | BehaviorSpace experiments: main sweep, time series, decoys-per-drone sweep |
| `run_experiments.py` | Runs an experiment headless |
| `make_figures.py` | Statistics (mean, 95% CI) and the report figures |
| `sweep_results.csv`, `timeseries.csv`, `ratio_sweep.csv` | Raw BehaviorSpace output |
| `summary_table_ci.csv` | Mean and 95% CI for each of the 561 settings |
| `latex/` | Report source, PDF and figures |
| `presentation/` | Slides (`.pptx`, `.pdf`) and the demo video |

## Reproduce

1. Open `decoy_saturation.nlogox` in [NetLogo 7.0.4](https://ccl.northwestern.edu/netlogo/), then press `setup` and `go`.
2. Re-run the experiments headless. If NetLogo is not in its default Windows location, change the NetLogo paths in `run_experiments.py`.
   ```bash
   python run_experiments.py                                   # decoy-saturation-sweep -> sweep_results.csv (56,100 runs)
   python run_experiments.py regime-timeseries timeseries.csv
   ```
3. Rebuild the statistics and figures (needs `matplotlib`):
   ```bash
   python make_figures.py
   ```

## Limitations

- Drones fly straight.
- Both sides follow simple fixed tactics, and neither one adapts.
- Bases do not share interceptors.
- Costs and magazine sizes are stylised. The exact percentages are not real-world numbers; the result is the shape of the transition.

## Acknowledgements

Partly inspired by Perun's YouTube presentations.
