.. _tutorial_data_extraction_waves:

############################
Tutorial 08: Data Extraction
############################

Many post-processing activities require a non-proprietary serialization format to provide common access to a mix of
analysis libraries and tools. The :ref:`parameter_generator_api` of this project uses the `xarray dataset`_ and H5
files, so it will be convenient to extract data results to a similar H5 file using matching coordinates for the
N-dimensional data.

Abaqus provides a scripting interface and a proprietary, binary output database file containing the simulation results.
While this object and interface is good for scripting with the Abaqus kernel and CAE features, the Python interface is
limited to the Python 2.7 environment that is shipped with Abaqus. When post-processing requires more Python libraries
or other third party tools, it is common to extract a portion of the Abaqus results to an intermediate file. To reduce
duplicated effort in extracting Abaqus ODB files to a common format, the :ref:`odb_extract_cli` command line utility and
the associated :meth:`waves.builders.abaqus_extract` builder are provided to parse the output of ``abaqus odbreport``
into several `xarray dataset`_ objects in an H5 file.

Future releases of |PROJECT| may include extract utilities for other numeric solvers.

**********
References
**********

* |PROJECT| :ref:`waves_builders_api` API: :meth:`waves.builders.abaqus_extract`
* :ref:`odb_extract_cli` CLI

***********
Environment
***********

.. include:: tutorial_environment_activation.txt

*******************
Directory Structure
*******************

3. Copy the ``tutorial_07_cartesian_product`` file to a new file named ``tutorial_08_data_extraction``

.. code-block:: bash

   $ pwd
   /path/to/waves-tutorials
   $ cp tutorial_07_cartesian_product tutorial_08_data_extraction

**********
SConscript
**********

A ``diff`` against the ``tutorial_07_cartesian_product`` file from :ref:`tutorial_cartesian_product_waves` is included
below to help identify the changes made in this tutorial.

.. admonition:: waves-tutorials/tutorial_08_data_extraction

   .. literalinclude:: tutorials_tutorial_08_data_extraction
      :language: Python
      :diff: tutorials_tutorial_07_cartesian_product

The only new code in this tutorial adds the :meth:`waves.builders.abaqus_extract` builder task. Note that this task
falls within the parameterization loop and will be executed once per parameter set. :ref:`odb_extract_cli` will output
two files: ``single_element_compression_datasets.h5``, which contains h5py paths to the `Xarray`_ datasets, and
``single_element_compression.h5``, which contains h5py native datasets for anything that :ref:`odb_extract_cli` doesn't
organize into `Xarray`_ datasets and a list of group paths pointing at `Xarray`_ datasets in
``single_element_compression_datasets.h5``. The second file also contains external links to the datasets file, so h5py
can be used to access all group paths if necessary. :ref:`tutorial_post_processing_waves` will introduce an example for
accessing and organizing the results files and concatenating the parameter study information.

**********
SConstruct
**********

A ``diff`` against the ``SConstruct`` file from :ref:`tutorial_cartesian_product_waves` is included below to help identify the
changes made in this tutorial.

.. admonition:: waves-tutorials/SConstruct

   .. literalinclude:: tutorials_tutorial_08_data_extraction_SConstruct
      :language: Python
      :diff: tutorials_tutorial_07_cartesian_product_SConstruct

*************
Build Targets
*************

4. Build the new targets

.. code-block:: bash

   $ pwd
   /path/to/waves-tutorials
   $ scons tutorial_08_data_extraction --jobs=4

************
Output Files
************

5. View the output files. The output files should match those introduced in :ref:`tutorial_cartesian_product_waves`, with
   the addition of the :ref:`odb_extract_cli` output files.

.. code-block:: bash

   $ pwd
   /path/to/waves-tutorials
   $ find build/tutorial_08_data_extraction/ -name "*.h5"
   build/tutorial_08_data_extraction/parameter_set2/single_element_compression.h5
   build/tutorial_08_data_extraction/parameter_set2/single_element_compression_datasets.h5
   build/tutorial_08_data_extraction/parameter_set1/single_element_compression.h5
   build/tutorial_08_data_extraction/parameter_set1/single_element_compression_datasets.h5
   build/tutorial_08_data_extraction/parameter_set3/single_element_compression.h5
   build/tutorial_08_data_extraction/parameter_set3/single_element_compression_datasets.h5
   build/tutorial_08_data_extraction/parameter_set0/single_element_compression.h5
   build/tutorial_08_data_extraction/parameter_set0/single_element_compression_datasets.h5
