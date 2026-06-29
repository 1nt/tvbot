#!/bin/bash

COOKIE_FILE="/root/tvbot/.cookie_string"
COOKIES=$(cat "$COOKIE_FILE")

echo "ID       | LOGIN               | ПАКЕТ"
echo "---------+---------------------+--------------"

curl -s -b "$COOKIES" "https://b.1lot.tv/dealer_iptv.php?action=adminUsers" | \
perl -0777 -ne '
@blocks = split(/(?=<input[^>]*masEvent\[\])/);
shift @blocks;
for $block (@blocks) {
    ($id) = $block =~ /value="(\d+)"/;
    ($user) = $block =~ /adminUser[^>]*>([^<]+)/;
    %seen = ();
    while ($block =~ /#006600">([^<]+)<\/font>/g) {
        $v = $1;
        next if $v =~ /^\d+\.\d+$/;
        next if $v eq "unlim";
        next if $v =~ /ваш IP/i;
        next if $seen{$v}++;
        printf "%-8s %-20s %s\n", $id, $user, $v;
    }
}
'