#!/usr/bin/python
import sys
import os
import shutil


def ensure_modules_path(path):
    if not os.path.exists(path):
        print('Creating directory %s' % path)
        os.makedirs(path)
    return path


def main():
    try:
        import ansible
    except ImportError:
        print('Could not "import ansible"')
        sys.exit(1)

    ansible_path = os.path.dirname(os.path.abspath(os.path.realpath(ansible.__file__)))
    print('Ansible path is {}'.format(ansible_path))

    modules_path = ensure_modules_path(os.path.join(ansible_path, 'modules', 'extras', 'database', 'foundationdb'))

    # Initialize needed paths
    here = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
    ansible_modules_sourcedir = os.path.join(here, 'modules')

    # Collect files to copy
    ansible_module_files = [f for f in os.listdir(ansible_modules_sourcedir) if f.endswith('.py')]

    # Copy module files
    for f in ansible_module_files:
        source = os.path.join(ansible_modules_sourcedir, f)
        destination = os.path.join(modules_path, f)
        if os.path.exists(destination):
            print('Overwriting %s' % destination)
        else:
            print('Copying %s' % destination)
        shutil.copy(source, destination)


if __name__ == '__main__':
    main()
