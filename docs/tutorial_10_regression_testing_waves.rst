.. _tutorial_regression_testing_waves:

###############################
Tutorial 10: Regression Testing
###############################

.. include:: wip_warning.txt

Regression testing is the practice of running a verification test suite after making changes to a repository or
codebase. For modsim repositories, there may not be many unit or integration tests if there is no software or scripting
library specific to the project. Instead, regression testing a modsim repository may look more like regular execution of
system tests that verify the simulation workflow still executes as expected.

Ideally, this verification suite of system tests would perform the complete simulation workflow from start to finish.
However, modsim repositories often contain simulations that are computationally expensive or produce large amounts of
data on disk. In these cases, it may be too expensive to run the full simulation suite at any regular interval. It is
still desirable to provide early warning of breaking changes in the simulation workflow, so as much of the workflow that
can be tested should be tested as regularly as possible given compute resource constraints.

This tutorial introduces a project wide alias to allow convenient execution of the simulation workflow through the
simulation datacheck task introduced in :ref:`tutorial_simulation_waves`. From that tutorial onward, each tutorial has
propagated a tutorial specific datacheck alias. This tutorial will add a project wide ``datacheck`` alias and apply it
to a copy of the :ref:`tutorial_post_processing_waves` configuration files. The user may also go back to previous
tutorials to include the full suite of datacheck tasks in the project wide datacheck regression test alias.

**********
References
**********

* :ref:`testing`
* `SCons Alias`_ :cite:`scons-user`
* Continuous Integration software

  * GitHub Actions: https://docs.github.com/en/actions :cite:`github-actions`
  * Gitlab CI: https://docs.gitlab.com/ee/ci/ :cite:`gitlab-ci`
  * Bitbucket Pipelines: https://bitbucket.org/product/features/pipelines :cite:`bitbucket-pipelines`

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
        $ waves fetch --overwrite --destination eabm_package/python 'tutorials/eabm_package/python/__init__.py' 'tutorials/eabm_package/python/rectangle_compression_nominal.py' 'tutorials/eabm_package/python/rectangle_compression_cartesian_product.py' 'tutorials/eabm_package/python/post_processing.py'
        WAVES fetch
        Destination directory: 'eabm_package/python'
        $ waves fetch tutorials/tutorial_09_post_processing_SConstruct && mv tutorial_09_post_processing_SConstruct SConstruct
        WAVES fetch
        Destination directory: '/home/roppenheimer/waves-tutorials'

4. Download and copy the ``tutorial_09_post_processing`` file to a new file named ``tutorial_10_regression_testing``
   with the :ref:`waves_cli` :ref:`waves_fetch_cli` subcommand.

.. code-block:: bash

   $ pwd
   /home/roppenheimer/waves-tutorials
   $ waves fetch --overwrite tutorials/tutorial_09_post_processing && cp tutorial_09_post_processing tutorial_10_regression_testing
   WAVES fetch
   Destination directory: '/home/roppenheimer/waves-tutorials'

********
CSV file
********

5. In the ``waves-tutorials/eabm_package/python`` directory, Create a new file named ``rectangle_compression_cartesian_product.csv`` from the contents below

.. admonition:: waves-tutorials/eabm_package/python/rectangle_compression_cartesian_product.csv

   .. literalinclude:: python_rectangle_compression_cartesian_product.csv
      :lineno-match:

**********
SConscript
**********

A ``diff`` against the ``tutorial_09_post_processing`` file from :ref:`tutorial_post_processing_waves` is included below to help identify the
changes made in this tutorial.

.. admonition:: waves-tutorials/tutorial_10_regression_testing

   .. literalinclude:: tutorials_tutorial_10_regression_testing
      :language: Python
      :diff: tutorials_tutorial_09_post_processing

To see the full power of the new project-wide ``datacheck`` alias, go back through the previous tutorials and add each
simulation specific datacheck task to the new alias.

**********
SConstruct
**********

A ``diff`` against the ``SConstruct`` file from :ref:`tutorial_post_processing_waves` is included below to help identify the
changes made in this tutorial.

.. admonition:: waves-tutorials/SConstruct

   .. literalinclude:: tutorials_tutorial_10_regression_testing_SConstruct
      :language: Python
      :diff: tutorials_tutorial_09_post_processing_SConstruct

*************
Build Targets
*************

6. Build the datacheck targets without executing the full simulation workflow

.. code-block:: bash

   $ pwd
   /home/roppenheimer/waves-tutorials
   $ scons datacheck --jobs=4

The full simulation suite may also be executed with a single command, but will take much longer to run as the full
simulation solve, data extraction, and post-processing will be performed. To compare the time of execution of the full
simulation suite against the limited datacheck workflow, perform the following sequence of commands.

.. code-block:: bash

   $ pwd
   /home/roppenheimer/waves-tutorials

   # Find all workflows that use the datacheck alias for one-to-one real time comparison
   $ datacheck_aliases=$(for file in $(grep -riIE "env\['datacheck_alias'\]" --include=SConscript -l); do echo $(dirname $file); done)

   # Verify that the list matches those files you changed for this tutorial
   $ echo ${datacheck_aliases}
   ...

   # Clean all and build datacheck alias
   $ scons . --clean --jobs=4 > clean.stdout 2>&1
   $ { time scons datacheck --jobs=4 > scons.stdout 2>&1 ; } 2> time_datacheck_workflow.txt

   # Clean all and build matching full workflows
   $ scons . --clean --jobs=4 > clean.stdout 2>&1
   $ { time scons ${datacheck_aliases} --jobs=4 > scons.stdout 2>&1 ; } 2> time_full_workflow.txt

   # Compare times
   $ grep "real" time_{datacheck,full}_workflow.txt

7. Run the full workflow and verify that the CSV regression test passes

.. code-block:: bash

   $ pwd
   /home/roppenheimer/waves-tutorials
   $ scons tutorial_10_regression_testing --jobs=4
   <output truncated>
   $ echo $?
   0

************
Output Files
************

.. code-block:: bash

   $ pwd
   /home/roppenheimer/waves-tutorials
   $ tree build/tutorial_10_regression_testing/parameter_set0/
   build/tutorial_10_regression_testing/parameter_set0/
   |-- abaqus.rpy
   |-- abaqus.rpy.1
   |-- abaqus.rpy.2
   |-- assembly.inp
   |-- boundary.inp
   |-- field_output.inp
   |-- history_output.inp
   |-- materials.inp
   |-- parts.inp
   |-- rectangle_compression.inp
   |-- rectangle_compression.inp.in
   |-- rectangle_compression_DATACHECK.023
   |-- rectangle_compression_DATACHECK.abaqus_v6.env
   |-- rectangle_compression_DATACHECK.com
   |-- rectangle_compression_DATACHECK.dat
   |-- rectangle_compression_DATACHECK.mdl
   |-- rectangle_compression_DATACHECK.msg
   |-- rectangle_compression_DATACHECK.odb
   |-- rectangle_compression_DATACHECK.prt
   |-- rectangle_compression_DATACHECK.sim
   |-- rectangle_compression_DATACHECK.stdout
   |-- rectangle_compression_DATACHECK.stt
   |-- rectangle_geometry.abaqus_v6.env
   |-- rectangle_geometry.cae
   |-- rectangle_geometry.jnl
   |-- rectangle_geometry.stdout
   |-- rectangle_mesh.abaqus_v6.env
   |-- rectangle_mesh.cae
   |-- rectangle_mesh.inp
   |-- rectangle_mesh.jnl
   |-- rectangle_mesh.stdout
   |-- rectangle_partition.abaqus_v6.env
   |-- rectangle_partition.cae
   |-- rectangle_partition.jnl
   `-- rectangle_partition.stdout

   0 directories, 35 files
   $ tree build/tutorial_10_regression_testing/ -L 1
   build/tutorial_10_regression_testing/
   |-- parameter_set0
   |-- parameter_set1
   |-- parameter_set2
   |-- parameter_set3
   |-- parameter_study.h5
   |-- stress_strain_comparison.csv
   |-- stress_strain_comparison.pdf
   `-- stress_strain_comparison.stdout

   4 directories, 4 files

**********************
Workflow Visualization
**********************

View the workflow directed graph by running the following command and opening the image in your preferred image viewer.
Plot the workflow with only the first set, ``set0``.

.. code-block::

   $ pwd
   /home/roppenheimer/waves-tutorials
   $ waves visualize datacheck --output-file tutorial_10_datacheck_set0.png --width=42 --height=8 --exclude-list /usr/bin .stdout .jnl .env .prt .com .msg .dat .sta --exclude-regex "set[1-9]"

The output should look similar to the figure below.

.. raw:: latex

    \begin{landscape}
        \vspace*{\fill}

.. figure:: tutorial_10_datacheck_set0.png
   :align: center

.. raw:: latex

        \vspace*{\fill}
    \end{landscape}

This tutorial's ``datacheck`` directed graph should look different from the graph in
:ref:`tutorial_post_processing_waves`. Here we have plotted the ``datacheck`` alias output, which does not execute the
full simulation workflow. This partial directed graph may run faster than the full simulation workflow for frequent
regression tests.

**********
Automation
**********

There are many tools that can help automate the execution of the modsim project regression tests. With the collector
alias, those tools need only execute a single `SCons`_ command to perform the selected, lower cost tasks for simulation
workflow verification, ``scons datacheck``. If `git`_ :cite:`git` is used as the version control system, developer
operations software such as `GitHub`_ :cite:`github`, `Gitlab`_ :cite:`gitlab`, and Atlassian's `Bitbucket`_
:cite:`bitbucket` provide continuous integration software that can automate verification tests on triggers, such as
merge requests, or on a regular schedule.

.. TODO: template .gitlab-ci.yml file
.. TODO: add references to alternative to gitlab
