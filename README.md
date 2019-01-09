# REsearch COmpendium memeNTO

A yaml structured research compendium for ease of use, containing three sections:
- datasources
- scriptsources
- workflow, referencing data and scripts

This reconto python package, helps prepare the research compendium
yaml and execute it to make the research compendium.

An example of the structure of the main yaml file:

    ---
    exenv: docker://reconto
    
    data:
    - &data1 https://example.com/dataset.tar.gz
    - &data2 /localfile.txt
    - &data3 localfile.txt # same file as above

    scripts:
    - &program1 python3://hello
    - &program2 brew://goodbye
    
    workflow:
    - *program1 *data1 *data2 -o &result1
    - *program2 *data3 *data1
    ...

Local datafiles have to reside under a local data subfolder, they can
be referenced starting with a '/' or without. Results will be written
out to the results subfolder of the research compendium.

`exenv` is the executing environment. The default is the reconto
docker image version 1. It can also be a tagged list, then the first
listed environment is the default, and all others can be mentioned
after a program in the `scripts` section.