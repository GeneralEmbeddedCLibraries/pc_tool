# Changelog
All notable changes to this project/module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project/module adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
## V0.3.0 - 17.02.2023

### Notice
 This version has new CLI interface format, compatible with CLI V1.3.0 on

### Added
 - Showing paramter details (access, type, persistance)
 - Feedback information on button press (Read All, Store All)
 - Added support for store all parameter button (issue #7)

### Changed
 - Parameter layout control & info change (issue #8)

---
## V0.2.0 - 17.02.2023

### Added
 - Raw traffic enable/disable option
 - Timestamp append to msg enable/disable option
 - Errors & Warnings color coded
 - Added automatic re-connection
 - Added measured data ploting option (offline)

### Fixed
 - End string termination parsing
 - Removed unused function
 - Table coloring problems 

---
## V0.1.0 - 15.08.2022

### Added
 - Connection via serial VCP
 - Command line interface (CLI)
 - Parameter table reading/writing
 - Creating/Deleting CLI shortcuts
 - CLI configurations:
   + Message timestamp 
   + Message source indicator
   + Pause (Freeze) CLI text

### Todo: 
 - Real-time ploting

---