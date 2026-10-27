# Third-party sources and modifications

The root MIT license covers this repository's original code and documentation. Upstream repositories, dependencies, meshes and models keep their own licenses. No upstream project is claimed as original work here.

## Rob2Nav

Source: https://github.com/YuTaoV5/Rob2Nav at `3187a41400364f18e0d9788ea52b06c4bc02126a`, MIT, copyright 2026 YuTaoV5 (root LICENSE retained).

Copied source files: scripts/prepare.py, pose_adapter.py, livox_relay.py and calibration_form.py originated in deployment/go2edu/. prepare.py has local changes: navigation-mode selection, mode-2 waypoint validation and measured body_height in generated launch. Other copied adapters retain their original logic. The archived Chinese navigation guide, walk_moe manifest, MoE provenance and upstream third-party notices are under references/rob2nav/. They are references; no original SportClient executor is included in the active control chain.

## Previous preparation work

scripts/imu_checks.py, calibration_check.py, accel_six_pose.py and their tests/configs were created during this user's 2026-10-27 preparation. The old installation failed before ROS runtime validation; evidence retained under evidence/. This repository refactors paths and documentation for a new machine.

## Fetched dependencies

SCAN-Planner, Elevator-LIO, Livox SDK2/driver2, Rob2Nav and Unitree SDK2 Python are fetched at locks/sources.json commits into ignored sources/. Their licenses stay in those checkouts. Optional RoboGauge MoE weights are fetched via the pinned Rob2Nav checkout and verified by SHA256; the model and original source notices remain upstream. LI-Init, elevation_mapping_cupy and TravExplorer are references, not vendored dependencies or completed integrations.

Official manuals are linked, not redistributed in full. This project has no affiliation or endorsement claim from Unitree, Livox or the upstream research authors.
