# Changelog

## [0.5.0] - 2025-10-23

- Added `PathologySlideNode.upload_tiled_mask` method to upload tiled masks from files using color map codename
  - Supports optional `scale` and `tile_size` parameters
  - Backend handles color map lookup by codename
- Added `ColorMap.get_all_color_maps()` static method to fetch all color maps
- Improved using saved token - detect when expired
- Added debug_logs flag to API

## [0.4.6, 0.4.7] - 2025-09-25

- Fix problem with parsing tiled masks with algorithms

## [0.4.5] - 2025-09-24

- Add possibility to create comments

## [0.4.4] - 2025-09-23

- Fix query handling for some cases (tags, point clouds)
- Add filtering by tags

## [0.4.3] - 2025-08-22

- Fix tag-related queries
- Add methods for renaming, deleting, linking, moving files, and adding subfolders
- Implemented methods for creating and managing studies within a study list.

New Jupyter Notebooks:
- working_with_files.ipynb: Demonstrates file operations such as renaming, deleting, linking, and moving files.
- working_with_studies.ipynb: Demonstrates study management operations, including adding new studies to a study list.

## [0.4.2] - 2025-08-22

- Added `updated_at` and `tags` fields to files

## [0.4.1] - 2025-08-08

- Added `verbose` parameter to `PathologySlideNode.create_from_files` method.
- Improved error handling in `API.query_graphql` method.

## [0.4.0] - 2025-08-08

### Added

- Added `File.search_files` method to search for files in the filesystem.
- Added `File.get_root` method to get the root file of the filesystem.
- Added `StudyNode` class to represent a study.
- Added `Algorithm.run_algorithm` method to run an algorithm on a slide.