import pathlib

# Set some semi-private project meta variables for package internal use to avoid hardcode duplication
_project_root_abspath = pathlib.Path(__file__).parent.resolve()
_project_name_short = _project_root_abspath.name.upper()
_project_name = f"{_project_name_short} Analysis for Verified Engineering Simulations"
_project_bin_dir = _project_root_abspath / "bin"
_abaqus_environment_file = "abaqus_v6.env"
_abaqus_environment_extension = f".{_abaqus_environment_file}"
_abaqus_solver_common_suffixes = [".odb", ".dat", ".msg", ".com", ".prt"]
_scons_substfile_suffix = ".in"
_stdout_extension = ".stdout"
_hash_coordinate_key = "parameter_set_hash"
_set_coordinate_key = "parameter_sets"
_quantiles_attribute_key = "_quantiles"
_installed_docs_index = _project_root_abspath / "docs/index.html"
