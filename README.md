# SSHerlock
An SSH-based autonomous agent to replace system administrators

## Todo

- allow key credentials to be created in addition to password credentials
- allow sudo credentials to be specified for target hosts
- allow selecting all target hosts at once when adding a job
- rename 'add job' or 'create job' to 'start job'
- allow shift-clicking target hosts when starting a job
- cap the vertical size of the target hosts text box in the start job view
- add an 'updated' field to the jobs list. update this field whenever an action is performed on a job
- containerize the ssherlock runner. deploy on google GCP cloud run. when a job is started, the server calls the GCP API to start a cloud run container. the container stops when the job is finished
- add automatic alerts that send to me with debug info when there's an exception anywhere, including a local javascript exception on a user's browser
- Prevent objects with duplicate names from getting created
- Prevent bastion hosts or target hosts with the same names getting created per user
- fix file usage functions in views.py using more django-ish conventions
- break apart ssherlock_server and ssherlock_runner ansible role
