<p align="center">
    <img src="https://rawgit.com/usnistgov/corr/master/corr-view/frontend/images/logo.svg"
         height="240"
         alt="CoRR logo"
         class="inline">
</p>

<p align="center"><sup><strong>
Check the platform source code at <a href="https://github.com/usnistgov/corr">usnistgov/corr</a>.
</strong></sup></p>

[![Gitter Chat](https://img.shields.io/gitter/room/gitterHQ/gitter.svg)](https://gitter.im/usnistgov/corr)


This repository is part of a effort in integrating most popular software management tools to CoRR.
The current repository is a fork of the Sumatra Code with the integration capabilities built-in.
* **[README](ABOUT)** – Original Sumatra Readme.

## Installing this version

To use this integrated version of Sumatra to CoRR, place yourself in the base of this repository and run:

    $ python setup.py install

## Getting started with Sumatra

This small tutorial on how to get started with this integrated version of sumatra of CoRR requires the
[CoRR examples](https://github.com/usnistgov/corr-examples). Please download it and install the requirements
for the project you want to run it for. Let's assume you are using: project-corr-python.

	$ cd project-corr-python

With sumatra you first have to put the project under version control. We choose to use git here:

    $ git init
    $ git add --all
    $ git commit -m "Initial commit."

At this point the project-corr-python is under git version control. Now we can carry on with the sumatra
initialization with CoRR setup. Login to your corr account and in the home page, got to your account details.
Then download your config file. Open it with a text editor. It should contain:

```
{
    "default": {
        "api": {
            "host": "https://localhost",
            "key": "7b37a3ff1184cb4f5ae04b3b175cfb6a63d2c6843ed051ccebfa87d8b35df4f4",
            "path": "/corr/api/v0.1",
            "port": 5100
        },
        "app": ""
    }
}
```

The host will point out to the api host of the corr instance you are logged in to. You will have also your
account private access key. This key allows sumatra to have access to your corr space to push content.
At this point you will need an application token. There are two options: You can create an application instance
in your dashboard under applications menu. Or query for applications and find one created by another one.
When you have an application profile, in front of the key icon copy the app key and place it in your config
file. This key will allow your sumatra instance to be identified in the plaform as the appropriate tool that will
be pushing content to your space. In this example i have created an app and retrieved the key. The config file is 
now as the following:

```
{
    "default": {
        "api": {
            "host": "https://localhost",
            "key": "7b37a3ff1184cb4f5ae04b3b175cfb6a63d2c6843ed051ccebfa87d8b35df4f4",
            "path": "/corr/api/v0.1",
            "port": 5100
        },
        "app": "2a0d338cca411b4d497f25c4d7fd7ebd2bb14dc39eb9d81bfbc564a2b5f57046"
    }
}
```

Now you can initialize your project with sumatra by providing this config file as the following:

	$ smt init -s path_to_your_config_file sumatra-python

For this example we placed the config in /home/fyc. Note that for this modified version of sumatra there is a 
naming standard in case you want to change the config file name. It will have to contain: config.json in the name.
We renamed this one to sumatra-config.json since we have other config files for other tools:

	$ smt init -s /home/fyc/sumatra-config.json sumatra-python-2017

From this point you can record as many project as you want. By following this scheme with sumatra:

	$ smt run --executable=python --main=main.py default.param

This is done as such since the project-corr-python program is run as the following:

	$ python main.py default.param

After the run of this command by sumatra. Refresh your dashboard and find for the first time a new project
with a single record and for the following times more records. Each records in this case should have 0 input,
1 output and 3 dependencies. You can download any of them to visualize what sumatra captured during the run.
