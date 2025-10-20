# Macallan RF Performance Visualization Tool

A comprehensive Python-based tool for RF performance analysis and compliance checking.

## Features

- **DUT Configuration Management**: Full CRUD operations for DUT types with multiple test stages
- **S-Parameter Analysis**: Wideband and operational gain/VSWR plots with compliance checking
- **Power/Linearity Testing**: Compression and linearity analysis with temperature monitoring
- **Noise Figure Analysis**: NF vs frequency plots with worst-case detection
- **Interactive Plotting**: Editable plots with export capabilities
- **Compliance Tables**: Pass/fail status with export options
- **File Format Support**: Touchstone (.s1p, .s2p, .s3p, .s4p) and CSV files
- **Test Stages**: Board Bring-up, SIT, and Test Campaign requirements

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 (for .exe build)

### Development Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python src/main.py
   ```

### Building Executable
1. Run the build script:
   ```bash
   python build_exe.py
   ```
2. The executable will be created in the `dist` directory

## Usage

### Getting Started
1. **Configure DUTs**: Use the "Configure DUTs" button to set up your DUT types
2. **Select DUT**: Choose a DUT type from the dropdown
3. **Select Test Stage**: Choose Board Bring-up, SIT, or Test Campaign
4. **Load Files**: Load your measurement files (Touchstone or CSV)
5. **View Results**: Generate plots and check compliance tables

### File Formats

#### Touchstone Files (.s1p, .s2p, .s3p, .s4p)
- Supports mag/deg, dB/deg, and real/imag formats
- Filename format: `YYYYMMDD_LXXXXXX_PRI/RED_SNXXXX_HG/LG.sXp`

#### CSV Files (Power/Linearity)
- Required columns: Serial Number, Temp, Frequency, Chain, Timestamp, Power Level (dBm), Mode, Power Meter (dBm), Thermister Calc (C), Marker 1-6 (dBm)
- 3 frequencies per file
- Single-tone and two-tone data

#### CSV Files (Noise Figure)
- Structure TBD (pending user input)

### Test Stages
- **Board Bring-up**: Initial testing requirements
- **SIT (Select-In-Test)**: Tighter requirements for tuning
- **Test Campaign**: Final requirements matching JAMA IDs

## Configuration

### DUT Configuration
Each DUT type includes:
- Frequency ranges (operational and wideband)
- Port configuration (inputs/outputs)
- Test enables (which tests to perform)
- Requirements for each test stage
- HG/LG variant support

### Requirements
- **S-Parameters**: Gain min/max, flatness, VSWR, out-of-band rejection
- **Power/Linearity**: P1dB, Pin-Pout-IM3 requirements
- **Noise Figure**: Maximum NF

## File Structure

```
macallan_rf_perf_tool/
├── src/                    # Source code
│   ├── models/            # Data models
│   ├── controllers/       # Business logic
│   ├── views/            # GUI components
│   └── utils/            # Utilities
├── config/               # Configuration files
├── data/                 # Database files
├── logs/                 # Log files
└── dist/                 # Built executables
```

## Open Actions

The following items require user input:
1. **CSV Filename Convention**: Naming format for power/linearity and NF CSV files
2. **Noise Figure CSV Structure**: Column headers and data organization

## Version History

- **v0.1.0**: Initial release with core functionality

## Support

For questions or issues, please contact the development team.

## License

Proprietary software for Macallan internal use.