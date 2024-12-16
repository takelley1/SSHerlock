# SSHerlock
An SSH-based autonomous agent to replace system administrators

## Todo

- change the theme of the site to dark
- add an account page with password reset, account management options
- containerize the ssherlock runner. deploy on google GCP cloud run. when a job is started, the server calls the GCP API to start a cloud run container. the container stops when the job is finished
- add automatic alerts that send to me with debug info when there's an exception anywhere, including a local javascript exception on a user's browser
- Prevent objects with duplicate names from getting created
- Prevent bastion hosts or target hosts with the same names getting created per user
- fix file usage functions in views.py using more django-ish conventions
- break apart ssherlock_server and ssherlock_runner ansible role
