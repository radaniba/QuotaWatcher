#QuotaWatcher

This is a utility to watch the quota on GSC for the `shahlab` group. It can be adapted for any general use

You can adjust the threshold that triggers the notification alert, currently is it set to 2.5 T

The script is set to run as a cron job. You can run it as a standalone tool on demand if you need to as well

Before running the program you need to setup your own environment variables such as :

```
export NOTIFIER_SENDER="quotawatcher.shahlab@gmail.com"
export NOTIFIER_PASSWD="passwordhere"
export NOTIFIER_SMTP="smtp.gmail.com"
export NOTIFIER_SMTP_PORT=587
export NOTIFIER_SUBTYPE="plain"
export GNU_PARALLEL="/path/to/your/gnu/parallel"
```


running the program ; example

```
python test.py /genesis/extscratch/shahlab/ dev_list -n "Hey Test" -t 2500000000000
```
