# AWK and sed programming in Chimera II

Chimera II treats AWK and sed as programming languages as well as command-line tools.

## AWK

`awk 'BEGIN { print "Chimera II" }'`

`awk '{ print $1 }' file.txt`

`awk -F: '$3 >= 1000 { print $1 }' /etc/passwd`

AWK programs use pattern/action pairs, records, fields, variables, arrays and functions. GNU's current AWK manual documents these core constructs and the execution model. citeturn0search4turn0search6

## sed

`sed 's/old/new/g' file.txt`

`sed -n '1,20p' file.txt`

`sed '/pattern/d' file.txt`

A sed program consists of address/command pairs; GNU sed documents commands, addresses, regular expressions and programming commands. citeturn0search3turn0search5

Chimera's command catalog records POSIX behavior separately from GNU extensions so scripts can be checked for portability.
