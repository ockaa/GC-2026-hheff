## Files
*`closestTriangulation.py`
  * It caluculates the tringilation that the closest to all other tringilations using `distance` and the overall ditance

* `distance.py`

  * It calculates the distance by iteratively flipping edges based on a `Huristic()`.

  * **Note:** The heuristic is currently just a **random 50/50 chance**.

* `drawing.py`

  * This is the **visualizer**.

  * has func `Draw_distance()` that takes 2 triangulations and the steps for the flips.

  * It shows `T1` and `T2` side-by-side, then draws the step-by-step flip sequence that transforms `T1`.
* `testing.py`

  * This is the tester for 2 triangulations that import from the benchmark_instances.

  * Run this file to see the output.
