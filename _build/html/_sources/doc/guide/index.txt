Getting Started
===============

While browsing the :doc:`../src/index` can be useful if you're a developer, it won't actually set up a build environment for you...thus, this section.

.. note::

   It should be taken for granted that, wherever I say "Linux," I mean basically any POSIX-compatible operating system.

.. _dependencies:

------------
Dependencies
------------

For starters, you will need `Python 2.7 <http://python.org/download/releases/2.7.5/>`_--no earlier version will work (due to the liberal use of context managers). It is recommended that you use a 32-bit version, as finding the following dependencies in 64-bit builds can be challenging, especially on OS's without package managers (like Windows).

After you are done with that, you'll need the following:

=========================================== ======================= =================================================================
Name                                        Package                 Website
=========================================== ======================= =================================================================
Pygame (Python bindings to SDL)             python-pygame           http://pygame.org/
PyOpenGL (Python bindings to OpenGL)        python-opengl           http://pyopengl.sourceforge.net/
Numpy (Numerical Python)                    python-numpy            http://www.numpy.org/
Sphinx (Optional; for generating docs)      python-sphinx           http://sphinx-doc.org/
=========================================== ======================= =================================================================

.. _repository:

----------------------
Getting the repository
----------------------

There's two ways to do this: use `git <http://git-scm.com/>`_, or get the .zip file from `the Github repository <https://github.com/Grissess/Mindscape/>`_. There are numerous reasons why actually getting the repository via git is preferred (not the least of which is ease of updating). In fact, if you're going to develop, you're going to *need* to know how to do this if you want to modify the repository.

If you're going to use the second method, just extract it to a local folder and move on. Otherwise, continue.

After you have this all in place, you'll want to open up a command line. On Windows, you can do this by searching for ``cmd`` in your start menu, or splash screen (or actually running ``cmd`` in your Run prompt, usually ``<WinKey>+R``). On Linux et. al., you can pull up your favorite terminal emulator, or use an actual (or virtual) terminal.

First, ``cd`` to the correct directory. The syntax, starting location, and file system conventions differ from operating system to operating system, so you'll want to consult your OS's documentation (usually ``help cd`` on the command line) for more information about this.

Once you're there, execute the following commands::

   git init .
   git remote add origin git://github.com/Grissess/Mindscape.git
   git pull origin master

.. note::

   If you're on Windows, ``git`` may or may not be in your PATH. If executing ``git`` gives you a "Command not found" error, you may need to find ``git.exe`` and type the full path to it (instead of ``git`` used above). Otherwise, the syntax is the same.

   Of course, a more permanent solution is to add the path containing the ``git.exe`` binary to your system's PATH variable. This is a complex topic that I won't delve into here.

After you're done setting up the repository thusly, you can repeat the last command (``git pull origin master``) to keep your repository up to date. Additionally, if you make any local commits (``git commit -a -m 'comment message goes here'``), you can use ``git push origin master`` to push the changes to the repository (assuming you have an account that allows this; consult the contributors on #mindscape at irc.rizon.net if you're interested!).

If you have a fork repository, you might want to set that one to being the ``origin`` instead. I'm assuming that, if you've forked it, you know how to do so.

.. _testing:

-------------
Running Tests
-------------

Now that you have the :ref:`dependencies <dependencies>` and :ref:`repository <repository>`, you're ready to run engine tests. All of these tests (so far) are Python files (``.py``) that begin with ``test_``.

If you're still in that command line, you can just call ``python`` on any such file. If you're on Windows, and ``python`` also isn't in your path, you can run test.bat instead, which will arrange to call Python on a file of your choosing (assuming it's installed in the default location). Or, of course, you could just type out the full path to wherever ``python.exe`` is on your system.

If you're on Linux, you should ensure that your ``python`` interpreter is actually 2.7--``python --version`` should output something starting with "Python 2.7". In general, Linux distros that have package managers symlink ``python`` to one of a few executable interpreters with the version in the name, such as ``python2.6``, ``python2.7``, ``python3.3``, et cetera. If ``python --version`` doesn't report 2.7, try ``python2.7`` instead, and, if needed, install this from your favorite package manager (or online). (After doing so, you may need to fetch those :ref:`dependencies <dependencies>` again.

---------------
Troubleshooting
---------------

There's a couple of ways to do this right, but a million ways to do this wrongly. I'll try to provide explanations of common issues here:

**The window closes without doing anything**
   99.9% of the time (on Windows) this is due to an uncaught exception in the Python code. As a result, the interpreter exits, which--if you're running the batch file, especially by double clicking it--unfortunately destroys the console window.

   To remedy this, go to the command line again (``cmd``, as outlined above in :ref:`Getting the repository <repository>`), ``cd`` into the repository directory, and run ``test.bat`` from in there (or just invoke the interpreter directly). Now, the console window should stick around long enough for you to see what the issue is.

**The test doesn't run, and the last line before exiting starts with "ImportError".**
   This means Python can't find a required module. There are a lot of reasons this could happen:

   * You may not have a required dependency. (Review the :ref:`dependencies <dependencies>` list.)
   * You may have the wrong or incompatible version of a dependency. Make sure you are getting the Python 2.7 version, with the same architecture (if you're finding it hard to find 64-bit versions, don't say I didn't warn you).
   * Your current working directory is improperly set. You need to call ``test.bat`` from directly inside the directory; don't call it absolutely from elsewhere, or the interpreter will be unable to find the modules in the root.

**Whenever I run ``test.bat``, it complains that it could not find the interpreter in the default location.**
   ``test.bat`` makes the assumption that you've installed Python to "C:\Python27\". If that isn't the case, you can edit the file and replace the relevant line. Of course, you should really make sure you *actually installed Python 2.7* and not some other version.

**The test doesn't run, and some other error appears for the last line.**
   That's probably a bug. Submit an issue report and/or yell at an awake developer on #mindscape at irc.rizon.net with your favorite IRC client!

---------------------
Where to go from here
---------------------

Soon enough, some IDEs will be present to begin doing engine work (as well as integrating other well-known IDEs like Blender into the workflow). Stay tuned for more information on that :D
