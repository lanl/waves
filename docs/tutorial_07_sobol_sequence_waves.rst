.. _tutorial_sobol_sequence_waves:

###########################
Tutorial 07: Sobol Sequence
###########################

.. include:: wip_warning.txt

.. TODO: remove the scipy minimum version note after requiring scipy>=1.7.0 in Conda package runtime requirements
.. https://re-git.lanl.gov/aea/python-projects/waves/-/issues/278

.. warning::

   The `AEA Compute environment`_ ``aea-{release,beta}`` does not yet support ``scipy>=1.7.0`` :issue:`278`. This
   tutorial can only be completed in a user-created environment. `WAVES`_ is available on the `AEA Conda channel`_.

**********
References
**********

* |PROJECT| :ref:`parameter_generator_api` API: :meth:`waves.parameter_generators.SobolSequence`
* `Xarray`_ and the `xarray dataset`_ :cite:`xarray,hoyer2017xarray`

***********
Environment
***********

.. include:: tutorial_environment_activation.txt

*******************
Directory Structure
*******************

3. Create a directory ``tutorial_07_sobol_sequence`` in the ``waves-eabm-tutorial`` directory.

.. code-block:: bash

   $ pwd
   /path/to/waves-eabm-tutorial
   $ mkdir tutorial_07_sobol_sequence

4. Copy the ``tutorial_07_cartesian_product/SConscript`` file into the newly created ``tutorial_07_sobol_sequence``
   directory.

.. code-block:: bash

   $ pwd
   /path/to/waves-eabm-tutorial
   $ cp tutorial_07_cartesian_product/SConscript tutorial_07_sobol_sequence/

********************
Parameter Study File
********************

5. Create a new file ``eabm_package/python/single_element_compression_sobol_sequence.py`` from the content below.

.. admonition:: waves-eabm-tutorial/eabm_package/python/single_element_compression_sobol_sequence.py

   .. literalinclude:: python_single_element_compression_sobol_sequence.py
      :language: Python

**********
SConscript
**********

A ``diff`` against the ``SConscript`` file from :ref:`tutorial_cartesian_product_waves` is included below to help identify the
differences between the two parameter generators.

.. admonition:: waves-eabm-tutorial/tutorial_07_sobol_sequence/SConscript

   .. literalinclude:: tutorial_07_sobol_sequence_SConscript
      :language: Python
      :diff: tutorial_07_cartesian_product_SConscript

**********
SConstruct
**********

A ``diff`` against the ``SConstruct`` file from :ref:`tutorial_cartesian_product_waves` is included below to help identify the
changes made in this tutorial.

.. admonition:: waves-eabm-tutorial/SConstruct

   .. literalinclude:: eabm_tutorial_07_sobol_sequence_SConstruct
      :language: Python
      :diff: eabm_tutorial_07_cartesian_product_SConstruct

*************
Build Targets
*************

6. Build the new targets

.. code-block:: bash

   $ pwd
   /path/to/waves-eabm-tutorial
   $ scons tutorial_07_sobol_sequence --jobs=4

************
Output Files
************