.. _tutorial_post_processing_waves:

############################
Tutorial 09: Post-Processing
############################

.. warning::

   The post-processing techniques in this tutorial are a work-in-progress. They should generally work into the future,
   but WAVES may add new behavior to make concatenating results files with the parameter study definition easier. Be sure
   to check back in on this tutorial frequently or watch the :ref:`changelog` for updates!

**********
References
**********

* |PROJECT| :ref:`waves_scons_api` API: :meth:`waves.scons_extensions.python_script`
* |PROJECT| :ref:`parameter_generator_api` API: :meth:`waves.parameter_generators.CartesianProduct`
* `Xarray`_ and the `xarray dataset`_ :cite:`xarray,hoyer2017xarray`

***********
Environment
***********

.. include:: tutorial_environment_activation.txt

.. include:: version_check_warning.txt

*******************
Directory Structure
*******************

.. include:: tutorial_directory_setup.txt

.. note::

    If you skipped any of the previous tutorials, run the following commands to create a copy of the necessary tutorial
    files.

    .. code-block:: bash

        $ pwd
        /home/roppenheimer/waves-tutorials
        $ waves fetch --overwrite --destination eabm_package tutorials/eabm_package/__init__.py
        WAVES fetch
        Destination directory: 'eabm_package'
        $ waves fetch --overwrite --destination eabm_package/abaqus 'tutorials/eabm_package/abaqus/*'
        WAVES fetch
        Destination directory: 'eabm_package/abaqus'
        $ waves fetch --overwrite --destination eabm_package/python 'tutorials/eabm_package/python/__init__.py' 'tutorials/eabm_package/python/rectangle_compression_nominal.py' 'tutorials/eabm_package/python/rectangle_compression_cartesian_product.py'
        WAVES fetch
        Destination directory: 'eabm_package/python'
        $ waves fetch tutorials/tutorial_08_data_extraction_SConstruct && mv tutorial_08_data_extraction_SConstruct SConstruct
        WAVES fetch
        Destination directory: '/home/roppenheimer/waves-tutorials'

4. Download and copy the ``tutorial_08_data_extraction`` file to a new file named ``tutorial_09_post_processing``
   with the :ref:`waves_cli` :ref:`waves_fetch_cli` subcommand.

.. code-block:: bash

   $ pwd
   /home/roppenheimer/waves-tutorials
   $ waves fetch --overwrite tutorials/tutorial_08_data_extraction && cp tutorial_08_data_extraction tutorial_09_post_processing
   WAVES fetch
   Destination directory: '/home/roppenheimer/waves-tutorials'

**********
SConscript
**********

A ``diff`` against the ``tutorial_08_data_extraction`` file from :ref:`tutorial_data_extraction_waves` is included below to help identify the
changes made in this tutorial.

.. admonition:: waves-tutorials/tutorial_09_post_processing

   .. literalinclude:: tutorials_tutorial_09_post_processing
      :language: Python
      :diff: tutorials_tutorial_08_data_extraction

Here we use the ``post_processing.py`` CLI instead of the module's API for the task definition because the
post-processing will include plotting with ``matplotlib``, which is not thread-safe. When the CLI is used, multiple
post-processing tasks from *separate* workflows can be executed in parallel because each task will be launched from a
separate thread. Care must still be taken to ensure that the post-processing tasks do not write to the same files,
however.

**********************
Post-processing script
**********************

5. In the ``waves-tutorials/eabm_package/python`` directory, create a file called ``post_processing.py`` using the
   contents below.

.. note::

   Depending on the memory and disk resources available and the size of the simulation workflow results, modsim projects
   may need to review the `Xarray`_ documentation for resource management specific to the projects' use case.

.. admonition:: waves-tutorials/eabm_package/python/post_processing.py

   .. literalinclude:: python_post_processing.py
      :language: Python

The script API and CLI are included in the :ref:`waves_eabm_api`: :ref:`eabm_post_processing_api` and :ref:`waves_eabm_cli`:
:ref:`eabm_post_processing_cli`, respectively.

**********
SConstruct
**********

A ``diff`` against the ``SConstruct`` file from :ref:`tutorial_data_extraction_waves` is included below to help identify the
changes made in this tutorial.

.. admonition:: waves-tutorials/SConstruct

   .. literalinclude:: tutorials_tutorial_09_post_processing_SConstruct
      :language: Python
      :diff: tutorials_tutorial_08_data_extraction_SConstruct

*************
Build Targets
*************

6. Build the new targets

.. code-block:: bash

   $ pwd
   /home/roppenheimer/waves-tutorials
   $ scons tutorial_09_post_processing --jobs=4
   <output truncated>

************
Output Files
************

7. Observe the catenated parameter results and paramter study dataset in the post-processing task's STDOUT file

.. code-block::

   $ tree build/tutorial_09_post_processing/ -L 1
   build/tutorial_09_post_processing/
   |-- parameter_set0
   |-- parameter_set1
   |-- parameter_set2
   |-- parameter_set3
   |-- parameter_study.h5
   |-- stress_strain_comparison.csv
   |-- stress_strain_comparison.pdf
   `-- stress_strain_comparison.stdout

   4 directories, 4 files
   $ cat build/tutorial_09_post_processing/stress_strain_comparison.stdout
   <xarray.Dataset>
   Dimensions:             (step: 1, time: 5, elements: 1, integration point: 4,
                            E values: 4, parameter_sets: 4, S values: 4,
                            data_type: 1)
   Coordinates:
     * step                (step) object 'Step-1'
     * time                (time) float64 0.0175 0.07094 0.2513 0.86 1.0
     * elements            (elements) int64 1
       integrationPoint    (elements, integration point) float64 1.0 nan nan nan
     * E values            (E values) object 'E11' 'E22' 'E33' 'E12'
     * S values            (S values) object 'S11' 'S22' 'S33' 'S12'
     * parameter_sets      (parameter_sets) <U14 'parameter_set0' ... 'parameter...
     * data_type           (data_type) object 'samples'
       parameter_set_hash  (parameter_sets) object ...
   Dimensions without coordinates: integration point
   Data variables:
       E                   (parameter_sets, step, time, elements, integration point, E values) float32 ...
       S                   (parameter_sets, step, time, elements, integration point, S values) float32 ...
       displacement        (data_type, parameter_sets) float64 ...
       global_seed         (data_type, parameter_sets) float64 ...
       height              (data_type, parameter_sets) float64 ...
       width               (data_type, parameter_sets) float64 ...

**********************
Workflow Visualization
**********************

View the workflow directed graph by running the following command and opening the image in your preferred image viewer.
Plot the workflow with only the first set, ``set0``.

.. code-block::

   $ pwd
   /home/roppenheimer/waves-tutorials
   $ waves visualize tutorial_09_post_processing --output-file tutorial_09_post_processing_set0.png --width=42 --height=8 --exclude-list /usr/bin .stdout .jnl .env .prt .com .msg .dat .sta --exclude-regex "set[1-9]"

The output should look similar to the figure below.

.. raw:: latex

    \begin{landscape}
        \vspace*{\fill}

.. figure:: tutorial_09_post_processing_set0.png
   :align: center

.. raw:: latex

        \vspace*{\fill}
    \end{landscape}

As in :ref:`tutorial_data_extraction_waves`, the directed graph has not changed much. This tutorial adds the ``*.pdf`` plot
of stress vs. strain.
