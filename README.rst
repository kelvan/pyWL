====
pyWL
====

python lib for WienerLinien API

API key
-------

create key.py and insert your api key

senderid_dev = "\<your key\>"

Station DB
----------

use `python -m db.importer` to import wienerlinien stop/station/line csv

get them from https://open.wien.at/site/datensatz/?id=add66f20-d033-4eee-b9a0-47019828e698

or use `bin/fetch_csv.sh` script

CLI
---

`python3 -m ui.cli`

e.g. `python3 -m ui.cli -l U1`
