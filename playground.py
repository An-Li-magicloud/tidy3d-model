from tidy3d.components import Simulation

json = {
  "center": [
    0,
    0,
    0
  ],
  "type": "Simulation",
  "size": [
    4,
    4,
    4
  ],
  "run_time": 4.0027691346211387e-13,
  "medium": {
    "name": "Vacuum",
    "frequency_range": None,
    "type": "Medium",
    "permittivity": 1,
    "conductivity": 0
  },
  "symmetry": [
    0,
    0,
    0
  ],
  "structures": [
    {
      "geometry": {
        "center": [
          0,
          0,
          0
        ],
        "type": "Box",
        "size": [
          1.5,
          1.5,
          1.5
        ]
      },
      "medium": {
        "name": "medium_1",
        "frequency_range": None,
        "type": "Medium",
        "permittivity": 4,
        "conductivity": 0
      },
      "name": "structure_0",
      "type": "Structure"
    }
  ],
  "sources": [
    {
      "center": [
        -1.5,
        0,
        0
      ],
      "type": "UniformCurrentSource",
      "size": [
        0,
        0.4,
        0.4
      ],
      "source_time": {
        "amplitude": 1,
        "phase": 0,
        "type": "GaussianPulse",
        "freq0": 299792458580946.8,
        "fwidth": 29979245858094.68,
        "offset": 5
      },
      "name": "source_0",
      "polarization": "Ey"
    }
  ],
  "boundary_spec": {
    "x": {
      "plus": {
        "name": None,
        "type": "PML",
        "num_layers": 12,
        "parameters": {
          "sigma_order": 3,
          "sigma_min": 0,
          "sigma_max": 1.5,
          "type": "PMLParams",
          "kappa_order": 3,
          "kappa_min": 1,
          "kappa_max": 3,
          "alpha_order": 1,
          "alpha_min": 0,
          "alpha_max": 0
        }
      },
      "minus": {
        "name": None,
        "type": "PML",
        "num_layers": 12,
        "parameters": {
          "sigma_order": 3,
          "sigma_min": 0,
          "sigma_max": 1.5,
          "type": "PMLParams",
          "kappa_order": 3,
          "kappa_min": 1,
          "kappa_max": 3,
          "alpha_order": 1,
          "alpha_min": 0,
          "alpha_max": 0
        }
      },
      "type": "Boundary"
    },
    "y": {
      "plus": {
        "name": None,
        "type": "PML",
        "num_layers": 12,
        "parameters": {
          "sigma_order": 3,
          "sigma_min": 0,
          "sigma_max": 1.5,
          "type": "PMLParams",
          "kappa_order": 3,
          "kappa_min": 1,
          "kappa_max": 3,
          "alpha_order": 1,
          "alpha_min": 0,
          "alpha_max": 0
        }
      },
      "minus": {
        "name": None,
        "type": "PML",
        "num_layers": 12,
        "parameters": {
          "sigma_order": 3,
          "sigma_min": 0,
          "sigma_max": 1.5,
          "type": "PMLParams",
          "kappa_order": 3,
          "kappa_min": 1,
          "kappa_max": 3,
          "alpha_order": 1,
          "alpha_min": 0,
          "alpha_max": 0
        }
      },
      "type": "Boundary"
    },
    "z": {
      "plus": {
        "name": None,
        "type": "PML",
        "num_layers": 12,
        "parameters": {
          "sigma_order": 3,
          "sigma_min": 0,
          "sigma_max": 1.5,
          "type": "PMLParams",
          "kappa_order": 3,
          "kappa_min": 1,
          "kappa_max": 3,
          "alpha_order": 1,
          "alpha_min": 0,
          "alpha_max": 0
        }
      },
      "minus": {
        "name": None,
        "type": "PML",
        "num_layers": 12,
        "parameters": {
          "sigma_order": 3,
          "sigma_min": 0,
          "sigma_max": 1.5,
          "type": "PMLParams",
          "kappa_order": 3,
          "kappa_min": 1,
          "kappa_max": 3,
          "alpha_order": 1,
          "alpha_min": 0,
          "alpha_max": 0
        }
      },
      "type": "Boundary"
    },
    "type": "BoundarySpec"
  },
  "monitors": [
    {
      "center": [
        0,
        0,
        0
      ],
      "type": "FieldMonitor",
      "size": [
        "Infinity",
        "Infinity",
        0
      ],
      "name": "fields_on_plane",
      "freqs": [
        299792458580946.8
      ],
      "fields": [
        "Ex",
        "Ey",
        "Hz"
      ],
      "interval_space": [
        1,
        1,
        1
      ],
      "colocate": False
    }
  ],
  "grid_spec": {
    "grid_x": {
      "type": "AutoGrid",
      "min_steps_per_wvl": 30,
      "max_scale": 1.4,
      "mesher": {
        "type": "GradedMesher"
      }
    },
    "grid_y": {
      "type": "AutoGrid",
      "min_steps_per_wvl": 30,
      "max_scale": 1.4,
      "mesher": {
        "type": "GradedMesher"
      }
    },
    "grid_z": {
      "type": "AutoGrid",
      "min_steps_per_wvl": 30,
      "max_scale": 1.4,
      "mesher": {
        "type": "GradedMesher"
      }
    },
    "wavelength": None,
    "override_structures": [],
    "type": "GridSpec"
  },
  "shutoff": 0.00001,
  "subpixel": True,
  "courant": 0.9,
  "version": "1.5.0"
}
sim = Simulation.parse_obj(json)
print(sim)