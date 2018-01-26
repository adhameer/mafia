# mafia

A webapp to help with modding games in the McGill Mafia Club.

It is not that great, because I've never made a webapp from scratch before, but hopefully it will do the job. You could probably screw it up by sending unexpected POST requests.

## Setup

**Note**: the Windows instructions here may be wrong, because I haven't tried them myself.

You should probably use a virtualenv for this to avoid clogging up your Python installation with a bunch of extra packages. From this folder, you can set one up as follows (you only need to do this once):

- Mac and Linux:
    ```
    $ python3 -m venv [path]
    $ [path]/bin/pip install --upgrade pip setuptools
    ```

- Windows:
    ```
    C:\> python3 -m venv [path]
    C:\> [path]\Scripts\pip install --upgrade pip setuptools
    ```

I use `env` for my path, which creates a subfolder `env` of this one where all your virtualenv files will go. Assuming you've got a virtualenv at this path, you can now install the project (you only need to do this once now, and then again later only if you change the setup.py file in this directory):

- Mac and Linux:
    ```
    $ env/bin/pip install -e .
    ```

- Windows:
    ```
    C:\> env\Scripts\pip install -e .
    ```

Now you can run the server with:

- Mac and Linux:
    ```
    $ env/bin/pserve development.ini --reload
    ```

- Windows:
    ```
    C:\> env\Scripts\pserve development.ini --reload
    ```

Then go check out the app at localhost:6543.
