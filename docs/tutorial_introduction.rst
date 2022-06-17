.. _tutorial_introduction:

#####################
Tutorial Introduction
#####################

*************
Start Options
*************

Users who want to jump straight to a minimally functional simulation workflow example can start with the
:ref:`quickstart`. For a detailed discussion of a recommended best practices `SCons`_  and `WAVES-EABM`_ project setup,
meta data, and features, start with :ref:`tutorialsconstruct`. It's also possible to skip the detailed project setup
discussion and start with the simulation task definitions and discussion directly in :ref:`tutorial_geometry_waves`.

*************
Prerequisites
*************

.. include:: tutorial_00_prerequisites.txt

********
Schedule
********

======================== ============================================ ==================================================
Time to complete (HH:MM) Tutorial                                     Summary
------------------------ -------------------------------------------- --------------------------------------------------
                   00:10 :ref:`quickstart`                            Minimally functional simulation build system
                                                                      workflow
                   01:00 :ref:`tutorialsconstruct`                    `SCons`_ project definition and meta data
                   01:00 :ref:`tutorial_geometry_waves`               Hierarchical `SCons`_ builds, task creation,
                                                                      Abaqus journal files as small utility software
                   01:00 :ref:`tutorial_partition_mesh_waves`         Dependent tasks and execution order
                   00:20 :ref:`tutorial_solverprep_waves`             Copying files into the build directory
                   00:20 :ref:`tutorial_simulation_waves`             Abaqus solver execution
                   00:20 :ref:`tutorial_parameter_substitution_waves` Parameterized builds and substituting parameter
                                                                      values into copied files
                   00:20 :ref:`tutorial_include_files_waves`          Including files that can be re-used in more than
                                                                      one workflow
                   01:00 :ref:`tutorial_cartesian_product_waves`      Parameter study introduction
======================== ============================================ ==================================================