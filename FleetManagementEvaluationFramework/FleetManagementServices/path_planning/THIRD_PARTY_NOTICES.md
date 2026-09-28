# Third-Party Notices (path_planning_service)

This file documents third-party components used by `path_planning_service`.
Each component remains subject to its original license terms.

---

## 1) bentley_ottmann

- **Component name:** `bentley_ottmann`
- **Upstream project:** https://github.com/lycantropos/bentley_ottmann
- **Upstream basis in this service:** references in
  `mapf_algorithms/collision_detection/bentley_ottmann/core/base.py`,
  `events_queue.py`, `sweep_line.py`, `utils.py`
- **Version/revision:** not pinned in this repository (derived from referenced upstream files)
- **License:** See `third_party_licenses/bentley_ottmann/LICENSE`
- **Used in:**
  `mapf_algorithms/collision_detection/bentley_ottmann/`
- **Modification status:** **Modified**
- **Derived files in this service:**
  `mapf_algorithms/collision_detection/bentley_ottmann/core/base.py`,
  `events_queue.py`, `sweep_line.py`, `utils.py`
- **Change type:** adapted and integrated for fleet-management collision detection workflows

## 2) ground

- **Component name:** `ground`
- **Upstream project:** https://github.com/lycantropos/ground
- **Upstream basis in this service:** references in
  `mapf_algorithms/collision_detection/bentley_ottmann/payload_data/payload_context.py`,
  `payload_data.py`
- **Version/revision:** not pinned in this repository (derived from referenced upstream files)
- **License:** See `third_party_licenses/ground/LICENSE`
- **Used in:**
  `mapf_algorithms/collision_detection/bentley_ottmann/payload_data`
- **Modification status:** **Modified**
- **Derived files in this service:**
  `mapf_algorithms/collision_detection/bentley_ottmann/payload_data/payload_context.py`,
  `payload_data.py`
- **Change type:** adapted and integrated for AMR-specific payload context/data handling

## 3) rustworkx

- **Component name:** `rustworkx`
- **Upstream project:** https://github.com/Qiskit/rustworkx
- **PyPI package:** https://pypi.org/project/rustworkx/
- **Version in current development environment:** `0.17.1`
- **Version constraint in repository:** `rustworkx` (unconstrained) in `requirements.txt`
- **License:** Apache-2.0
- **License text in this service:** `third_party_licenses/rustworkx/LICENSE`
- **Used in:**
  `mapf_algorithms/core/path_planning_obj.py`
- **Modification status:** **Unmodified**

## Notes

1. For exact legal terms, refer to each component's original license text.
2. For source/binary/container redistribution, include required license texts and notices for listed components.
