# CKAN Google Analytics Extension

**Status:** Production

**CKAN Version:** >= 2.8

A CKAN extension that both sends tracking data to Google Analytics and
retrieves statistics from Google Analytics and inserts them into CKAN pages.

## Warning
This is a fork (of a fork) of the original project that's been updated to reflect the evolution of Google Analytics and our needs at FjellTopp.

The major changes are:
- Drop support for Python 2.x
- Drop support for Google Analytics since it is no longer supported from July 1st 2024.

## Features


* Puts the Google Analytics asynchronous tracking code into your page headers
  for basic Google Analytics page tracking.

* Adds Google Analytics Event Tracking to resource download links, so that
  resource downloads will be displayed as Events in the Google Analytics
  reporting interface.

* Adds Google Analytics Event Tracking to some API calls so that usage of the
  API can be reported on via Google Analytics.

* Add Google Analytics Event Tracking function that can be used in any exstension
  to create your custom events tracking.

		ckanext.googleanalytics.plugin._post_analytics

## Installation
### Pip installation
It is recommended to perform the installation from an activated virtual environment such one created by `venv` or `conda`:
```
$ pip install -e git+https://github.com/fjelltopp/ckanext-googleanalytics4.git#egg=ckanext-googleanalytics
$ pip install -r ckanext-googleanalytics4/requirements.txt
```

### Pipenv installation
Pipenv comes with its own peculiarities, especially its `Pipfile` and `Pipfile.lock` files, and that's why it requires its own instructions.

Edit your `Pipfile` by adding the following entries:
```
ckanext-googleanalytics = {editable = true, git = "https://github.com/fjelltopp/ckanext-googleanalytics4.git"}
gdata = "~=2.0"
google-api-python-client = ">=1.6.1, <1.7.0"
pyOpenSSL = ">=16.2.0"
rsa = ">=3.1.4, <=4.0"
```
> Notice how we don't add the `#egg=` information to the url, this is to avoid running afoul of PEP 508 about the `egg` fragment being a bare PIP 508 project name. See more at [pypa/pip#11617](https://github.com/pypa/pip/pull/11617).

Then lock your `Pipfile` with:
```
$ pipenv lock
```

Last you can now install from your `Pipfile.lock` with:
```
$ pipenv sync --dev
```
> You should remove the `--dev` flag in production.

## Configuration

### Enabling the extension
The first step is to add `googleanalytics` to your list of extensions either in
your `development.ini`, `production.ini` or `ckan.ini`.

> If you are using a different extension as a storage handler besides the default provided by ckan, make sure to have `googleanalytics` before your storage handler in the list of extensions.

### Configuring the extension
Google Universal Analytics was phased out completely starting July 1st, 2024 with only
Google Analytics 4 (GA4) supported henceforth.

Therefore all configurations options are only applicable to GA4 unlike the original
extension which still supports Universal Analytics.

#### Configuration for sending analytics to Google Analytics
In order to send analytics, in theory, you need only to specify the following:
- Your **measurement ID** which you can find under *Admin > Data collection and modification > data stream*. It should be of the form `G-XXXXXXXXXX`, that is `G-` followed by 10 alphanumeric characters.

Therefore the following needs to be added to your CKAN `.ini` configuration file:
```
googleanalytics.measurement_id = G-XXXXXXXXXX
```

#### Configuration for retreiving analytics from Google Analytics
The extension allows you to retreive the number of times particular
resources have been downloaded and sums up that number to inform
about the number of times to inform you how many times resources in a
dataset have been downloaded.

To enable this functionility, you need the following configuration:
- Your **propery ID**: this can be found under *Admin > Propery > Property details*. This will be a 9 digits number.
   If no property details have been created before hand, this is the time to create one.

At this point, your configuration will look as:
```
googleanalytics.measurement_id = G-XXXXXXXXXX
googleanalytics.property_id = 123456789
```

#### Additional configuration option
While this extension intercepts downloads in order to send additional
data to Google Analytics, you need to let the extension what your download
handler to it can forward it the download request and the user can be served
with the actual file to download.

The configuration for this can be as follow:
```
googleanalytics.download_handler = ckanext.blob_storage.blueprints:download
```

In this case, we have `blob_storage` as our storage handler (uploads and downloads)
and downloads are handled by the function `download` which can found in the file
`ckanext/blob_storage/blueprints.py`. This will vary depending on which storage
handler you use.  
If no storage handler is provided, the default storage handler that comes with CKAN
will be used without explicitly providing it:
```
googleanalytics.download_handler = ckan.views.resource:download
```

## Retreiving analytics from Google Analytics

In order to retrieve statistics from Google Analytics, we need to enable the Google Analytics API and be able to authenticate with it every time we need data.

Some steps below require to have the `gcloud` CLI installed. Details can be found at
https://cloud.google.com/sdk/docs/install.

After installing `gcloud`, run `gcloud init` to get `gcloud` linked to your account.

This accomplished by creating a Google Cloud account at [Google Cloud](https://console.cloud.google.com/welcome) then following these steps:
1. Create a project at https://console.cloud.google.com/projectcreate. If you have no organization, choose the `No organization` option when creating the project.
2. Once you have a project, you need to create a service account under that project:
   ```
   $ gcloud iam service-accounts create google-analytics --description="Service account for Google analytics" --display-name="Google analytics service account"\n
   ```
3. Once you have a service account, you need to create a service account key.
   This will result in a JSON file being downloaded on your computer that contains
   the credentials to access the service account so save it carefully:
   ```
   $ gcloud iam service-accounts keys create google-analytics-service-account-key.json --iam-account=IAM_ACCOUNT
   ```
   where `IAM_ACCOUNT` can be found by running `gcloud iam service-accounts list`.
   It will be an email-looking like string.
4. Enable the Google Analytics API: go to https://console.cloud.google.com/apis/dashboard?project=PROJECT_ID where `PROJECT_ID` can be obtained by running `gcloud projects list`.

With the file `google-analytics-service-account-key.json` in our hands and the Google Analytics API enabled, we can proceed to pull analytics from Google Analytics.

> Right now, the only analytics you can get correspond to file downloads.

1. First, initialize the database by creating tables that `ckanext-googleanalytics` needs:
   ```
   $ ckan -c /path/to/ckan.ini googleanalytics init
   ```
2. Then pull analytics into the local database:
   ```
   $ ckan -c /path/to/ckan.ini googleanalytics load /path/to/google-analytics-service-account-key.json
   ```

## Testing
There are some very high-level functional tests that you can run using::

	(pyenv)~/pyenv/src/ckan$ nosetests --ckan ../ckanext-googleanalytics/tests/

(note -- that's run from the CKAN software root, not the extension root)

## Future

The extension is under active development.
Given this fork is under the care of FjellTopp, the functionalities added will largely
depend on our needs.
