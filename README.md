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
* **[README](ABOUT.md)** – Original Sumatra Readme.

## Additional Setup Requirement

The integration of this requirement to CoRR yielded some extra steps in using the original code.
Originally to setup a project with Sumatra, one would do:

    $ smt init MyProject

To Use Sumatra with your CoRR account. Retrieve your access token in your home page account and do:

    $ smt init -s http(s):{instance_api_domain_port}/corr/api/v0.1/private/{access_token} MyProject
    
You will need the api domain and port. This is accessible through your account by downloading the 
config file. We are working to make this init part be able to load the config file.

For example, in my local development CoRR instance i have setup this way:

    smt init -s http://localhost:5100/corr/api/v0.1/private/b6b458cecd92bf0f6308645d783d2a14f55e4d30c248482bbc6b82637de5c410 sumatra-python

## Developers & Users

This sumatra code is currently in development mode and is registered in a localhost instance of CoRR.
It will soon be linked to an official CoRR instance and be added as an application that users registered
could use to push their sumatra records.

After standing an instance of CoRR, to allow users to use this version of sumatra, please contact me
(Faical Yannick P. Congo) or look into sumatra/recordstore/http_store.py and search for:

    self.sumatra_token = "1f3976f98d348483f8d2bc2232f827ed3fa78b8cf0bb1a142bf41a811b371c99".

Replace the token by the newly created application token of sumatra produced by your CoRR instance and
provide this code to your user.

We are working to make many instances of CoRR interoperable with the same sumatra code. So contacting me
would be the most sustainable effort.

## Note

This effort is part of part of CoRR flexible integration capability and includes many other software 
management tools.
