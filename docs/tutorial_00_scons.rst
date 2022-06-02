#######################
Tutorial 00: SConstruct
#######################

*************
Prerequisites
*************

1. :ref:`computational_tools` :ref:`build_system`
2. Software Carpentry: GNU Make -  https://swcarpentry.github.io/make-novice/
3. Software Carpentry: Python - https://swcarpentry.github.io/python-novice-inflammation/

.. _sconstruct_environment:

***********
Environment
***********

.. include:: tutorial_environment_activation.txt

***********
Description
***********

`WAVES`_ is a suite of build wrappers and command line utilities for the build system `SCons`_. Build systems help
automate the execution of complex computing workflows by constructing component task execution order. In the
`WAVES-EABM`_ tutorials, there are two components to the `SCons`_ configuration: project definition and simulation
definitions. This tutorial introduces the `SCons`_ project definition file for the `WAVES-EABM`_ template EABM
repository.

The command line utilities provided by `WAVES`_ are those utilities required to implement engineering workflows in
traditional software build systems. For most engineering simulation workflows, software build systems will work
out-of-the-box. However, it is difficult to implement engineering parameter studies in software build systems, which are
designed to produce a single program, not many nearly identical configurations of the same program. The `WAVES`_
parameter generator utility, :ref:`parameter_study_cli`, is designed to work with most build systems, but were
originally developed with the requirements of `CMake`_ in mind.

For production engineering analysis, `WAVES`_ focuses on extending the build system `SCons`_ because `SCons`_
configuration files use `Python`_ as a fully featured scripting language. This choice is primarily driven by the
familiarity of the engineering community with `Python`_ as a programming language, but also because the parameter
generation utility can be integrated more closely with the build system, :ref:`parameter_generator_api`.

***************************
SCons Project Configuration
***************************

3. Create and change to a new project root directory to house the tutorial files. For example

   .. code-block:: bash

      $ pwd
      /home/roppenheimer
      $ mkdir waves-eabm-tutorial
      $ cd /home/roppenheimer/waves-eabm-tutorial

4. Create a new file named ``SConstruct`` in the ``waves-eabm-tutorial`` directory and add the contents listed below. Note
   that the filename is case sensitive.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :emphasize-lines: 8-13
      :end-before: marker-1

.. note::

   Highlighted lines 8-13 are artifacts of the `WAVES-EABM`_ internal project regression tests. EABM owners and tutorial
   users may replace these lines with a simple `WAVES`_ import, such as

   .. code-block::

      import waves

By convention, the `SCons`_ root project file is named ``SConstruct``. Because this is a `Python`_ file, we can import
`Python`_ libraries to help define project settings. The `shebang`_ in the first line is included to help text editors
identify the file as a Python file for syntax highlighting. Using the `PEP-8`_ formatting, the `Python`_ built-in
imports are listed in the first block and third-party imports are listed in the second block, including the `WAVES`_
package. Finally, the EABM version number is hardcoded into the project definition for these tutorials.

5. Add the content below to the ``SConstruct`` file to add the project's command-line build variables to the project
   configuration.

.. include:: line_number_jump_note.txt

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-1
      :end-before: marker-2

The `SCons command-line build variables`_ are specific to the project definition that you are currently creating. EABM
projects may add or remove command line options to aid in build behavior control. The most relevant variable to most
EABMs will be the ``variant_dir_base``, which allows EABM developers to change the build directory location from the
command line without modifying the ``SConstruct`` file source code. For example, the first ``scons`` call will create
the default build directory named ``build`` and the second ``scons`` call will create a build directory named
``non-default_build``.

.. code-block::

   $ ls .
   SConstruct
   $ scons
   $ ls .
   SConstruct
   build/

   $ scons variant_dir_base=non-default_build
   $ ls .
   SConstruct
   build/
   non-default_build/

The ``conditional_ignore`` variable is mostly useful for :ref:`continuous_integration` testing. At the end of this
tutorial, you will see how to explore the project specific command line options and build variables help and usage.

6. Add the content below to the ``SConstruct`` file to initialize the `SCons construction environment`_.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-2
      :end-before: marker-3

Most build systems inherit the user's active `shell environment`_ at build configuration time, referred to as the
"external" environment in the `SCons`_ documentation. This means that (most) of the environment must be identical for
all build tasks in the project. `SCons`_ differs from most build systems by managing the construction environment for
each task separately from the external environment. `SCons`_ projects do not inherit the user's shell environment at
build configuration by default. Instead, projects define one or more construction environments that is used to define
per-task environment configuration.

While this is a powerful feature for large, complex projects, most EABM projects will benefit from maintaining a single
construction environment inherited from the active shell environment at build configuration time. In addition to copying
the active external environment, the above code adds the project command-line build variables to the construction
environment for re-use throughout the project definition files, SConstruct and SConscript, for build control.

7. Add the content below to the ``SConstruct`` file to add the third-party software dependency checks to the project
   definition.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-3
      :end-before: marker-4

These checks are not strictly required for an `SCons`_ `WAVES`_ EABM; however, they provide valuable build control
options for EABM developers. Most of the `WAVES-EABM`_  compute environment dependencies are `Python`_ packages managed
with `Conda`_ as described in the :ref:`sconstruct_environment` section of this tutorial. Many modsim repositories will
also depend on proprietary or commercial software that is not included in a package manager such as `Conda`_. Instead,
the project configuration can check the construction environment for software installation(s) and provide an environment
variable to conditionally skip any tasks that depend on missing software.

In `WAVES`_ and `WAVES-EABM`_, this approach is primarily used to allow developers to perform development work on local
computers without cluttering their test builds with tasks that cannot succeed on their local computer.
:ref:`tutorialgeometrywaves` will introduce the use of these variables for build control.

8. Add the content below to the ``SConstruct`` file to add the command-line build variables to the `SCons project build
   help`_ message.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-4
      :end-before: marker-5

The following line adds the help messages for the command-line build variables to the project help message displayed
wheen running ``scons -h``. The help messages are added to the construction environment, so this line must come after
the construction environment instantiation.

.. note::

   The project help message uses the conventional lowercase help option, ``-h``. Most bash commands use this option to
   display the command's help message corresponding the software options. Due to this behavior, the `SCons`_ command
   options are displayed with the unconventional capitalized option, ``-H``, as ``scons -H``. The `WAVES-EABM`_
   tutorials and documentation will not discuss the full range of `SCons`_ command options, so modsim developers are
   encouraged to read the `SCons`_ usage summary and `SCons manpage`_ to learn more about available build control options.

9. Add the content below to the ``SConstruct`` file to add the project meta data to the construction environment.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-5
      :end-before: marker-6

The `WAVES-EABM`_ makes use of the `SCons hierarchical build`_ feature to separate simulation output in the build
directory. This is valuable for modsim repositories that include a suite of simulations. To avoid hardcoded duplication
of project meta data, the project meta data variables are added to the construction environment, which will be passed
around to all `SCons`_ configuration files. The implementation that passes the construction environment around is
introduced in :ref:`tutorialgeometrywaves`.

10. Add the content below to the ``SConstruct`` file to add `WAVES`_ builders to the project definition.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-6
      :end-before: marker-7

Although it is possible to re-create the `WAVES-EABM`_ entirely in native `SCons`_ code, the builder extensions provided
by `WAVES`_ reduce the requisite background knowledge to begin creating EABM repositories. The construction environment
``BUILDERS`` variable must be updated to include these custom `SCons`_ builders and make them available to the
simulation configuration starting in :ref:`tutorialgeometrywaves`.

The :ref:`sconsbuildersapi` describes the available builders and their usage. As `WAVES`_ matures, more software will be
supported with build wrappers. Prior to a `WAVES`_ builder, modsim developers can create their own `SCons custom
builders`_.

11. Add the content below to the ``SConstruct`` file to create a placeholder call to the hierarchical simulation configuration files.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-7
      :end-before: marker-8

The for loop in this code-snippet is the method for implementing an `SCons hierarchical build`. The ``exports`` keyword
argument allows the project configuration file to pass the ``env`` construction environment variable with the `SCons
sharing environments`_ feature. The first simulation configuration will be added to the ``eabm_simulation_directories``
list in :ref:`tutorialgeometrywaves`.

12. Add the content below to the ``SConstruct`` file to add an empty default target list and to list the default targets
    in the project help message.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-8
      :end-before: marker-9

Because the `WAVES-EABM`_ contains a suite of simulations, it is useful to limit what `SCons`_ will build by default. To
protect against running all simulations by default, create an empty default list. This will require that simulation
targets are specified by name in the `SCons`_ build command. In addition to limiting the default target list, it is
useful to print the list of default targets in the project help to remind developers what targets will build when no
target is specified in the call to ``scons``. The second call to ``Help()`` will append the default target list to the
output of ``scons -h``.

13. Add the content below to the ``SConstruct`` file to add the project aliases to the project help message.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_00_SConstruct
      :language: Python
      :lineno-match:
      :start-after: marker-9
      :end-before: marker-10

Simulation build workflows will typically involve many targets and tasks in a non-trivial execution order. The target
file names may also be cumbersome to type when explicitly listing build targets in the `SCons`_ build command. For
convenience, the `WAVES-EABM`_ simulation configurations will add a collector alias for the list of simulation targets
with the `SCons alias`_ feature. By convention, `WAVES-EABM` matches the alias name to the simulation subdirectory
name. :ref:`tutorialgeometrywaves` will introduce the first target alias, which will then populate the project help
message diplayed by the ``scons -h`` command option.

.. note::

   The alias list is constructed manually according to the `WAVES-EABM`_ naming convention. There may be a way to
   recover the alias list from the construction environment. If so, recovering the alias list directly will be a more
   robust solution for building the project's alias list than a project naming convention. This tutorial will be updated
   to reflect best practice if/when an `SCons`_ alias list solution is better understood.