## MIBI pipeline

Prepares data and does 2D segmentation of MIBI images.


### Usage example

`cwltool pipeline.cwl subm.yaml`

Requires `meta.yaml` with names of channels 
that will be used for segmentation of cell and nucleus compartments.

### The expected input directory structure:

**Input dir**: `/.../Serial_Section/no_background`

```
Serial_Section
└── no_background
    ├── Point1
    │    └── TIFs
    │        ├── Au.tif
    │        ├── BetaCatenin.tif
    │        │          ...
    │        └── HH3.tif
    └── PointN
        └── TIFs
            ├── Au.tif
            ├── BetaCatenin.tif
            │          ...
            └── HH3.tif
        
```

### The output structure:
```
pipeline_output/
├── expr
│   ├── region_001
│   │    └── reg001_expr.ome.tiff
│   │    
│   └── region_00N
│        └── reg00N_expr.ome.tiff
│       
└── mask
    ├── region_001
    │    └── reg001_mask.ome.tiff
    │    
    └── region_00N
         └── reg00N_mask.ome.tiff
```
